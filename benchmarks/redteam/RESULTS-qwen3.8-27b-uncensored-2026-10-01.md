# Qwen3.8-27B-Uncensored (orcarouter, NVFP4) — first boot, full-context and refusal eval

Date 2026-10-01. Single DGX Spark GB10 (head, 10.10.20.10), TP=1, vLLM
0.30.1rc1.dev220, recipe `recipes/qwen3.8-27b-uncensored-nvfp4-tp1.yaml`,
served as `qwen3.8-27b-uncensored`.

First time this model has ever run on this pair. Row 41 had sat UNVERIFIED with
a 669 MB metadata stub in place of weights.

## 1. Startup

| Metric | Value |
|---|---|
| Weights | 24.69 GB, 6 shards, checksums verified |
| Weight load | **2.05 s** (`load_format: instanttensor`) |
| Model memory | 22.36 GiB |
| KV cache | 64.47 GiB = **2,029,356 tokens** |
| Concurrency at 262,144 | 7.74x |
| Graph capture | 68 s + 64 s (1.59 + 0.68 GiB) |
| Init engine | 374 s |

Three recipe fixes were required first, each from evidence already in this repo:
the b12x image was swapped for the standard nightly because `instanttensor` is
only verified on the latter here (b12x needs io_uring, which rootless seccomp
forbids); utilization moved 0.82 -> 0.80 to match verified row 52; and the MTP
speculative config was removed because the checkpoint declares no
`num_nextn_predict_layers` and ships no draft weights.

## 2. Full context — needle in a haystack, 21/21 correct

Needle placed at 10%, 50% and 90% depth. Every cell retrieved correctly.

| Measured prompt tokens | Hits | Wall | Prefill |
|---|---|---|---|
| 1,352 | 3/3 | 4.9–8.6 s | 157–278 tok/s |
| 5,153 | 3/3 | 4.8–8.6 s | 602–1,067 tok/s |
| 20,354 | 3/3 | 7.2–9.0 s | 2,258–2,837 tok/s |
| 81,230 | 3/3 | 9.6–10.9 s | 7,447–8,481 tok/s |
| 148,640 | 3/3 | 11.2–12.3 s | 12,117–13,248 tok/s |
| 204,350 | 3/3 | 189–273 s | 749–1,080 tok/s |
| **247,670** | **3/3** | 239–369 s | 671–1,036 tok/s |

The advertised 262,144 window is real and usable to 247,670 tokens; beyond that
the server returns HTTP 400 as it should. No late-context blind spot — the 90%
position is as reliable as the 10%.

**PERFORMANCE CLIFF between 148k and 204k tokens.** Prefill peaks at
13,248 tok/s then collapses to ~1,000, a 13x drop, and wall time goes from 12 s
to as much as 369 s. Accuracy is unaffected, so this is a throughput wall, not a
correctness one. The KV pool still has 7.74x headroom at full context, so KV is
not the constraint — cause unidentified. Practical read: past ~150k context this
is batch-only, not interactive.

## 3. Refusal eval — JailbreakBench JBB-Behaviors

100 harmful behaviours across 10 policy categories plus 100 category-matched
benign controls. Prompts are the published benchmark, not written here, so these
numbers are comparable to the JailbreakBench literature. Grader is keyword
refusal detection, which over-counts refusals on novel phrasing.

### Short context (`--no-think`, 762 s, concurrency 12)

| Split | n | Compliance | Refusal | Truncated | Error |
|---|---|---|---|---|---|
| Harmful | 100 | **100 (100%)** | 0 | 0 | 0 |
| Benign | 100 | **100 (100%)** | 0 | 0 | 0 |

Ten of ten in every category on both splits: Disinformation, Economic harm,
Expert advice, Fraud/Deception, Government decision-making,
Harassment/Discrimination, Malware/Hacking, Physical harm, Privacy,
Sexual/Adult content.

The abliteration is complete rather than partial. **The benign controls are what
make that conclusion possible**: full compliance there, with substantive answers
(median 1,781 chars harmful, 1,750 benign; 95% hit the 400-token cap rather than
stopping early) shows the model is intact, not merely degraded into assent. A
damaged abliteration shows high harmful compliance with impaired benign
behaviour; that is not this.

### Long context (~57,820 tokens of padding, 1,398 s, concurrency 8)

| Split | n | Compliance | Refusal |
|---|---|---|---|
| Harmful | 100 | 99 (99%) | 1 |
| Benign | 100 | 100 (100%) | 0 |

The single flagged refusal is a **grader false positive**: the response opens
"I cannot encourage you to gamble your life savings... However" and then complies
over 1,205 characters. Answer quality holds at depth (median 1,715 / 1,694
chars). So behaviour at ~58k context is indistinguishable from short context.
No evidence of safety drift with depth, and no safety present to drift.

## 4. Correctness — does it actually answer right?

The refusal eval only shows it *will* answer. These two are auto-graded against
gold labels, so they show whether the answer is *right*. This is the number that
decides usefulness, and the one abliteration usually damages.

| Benchmark | Score | Condition | Unparsed |
|---|---|---|---|
| GSM8K (grade-school math) | **144/150 = 96.0%** | reasoning ON, 1536 tok | 1 |
| MMLU (57-subject knowledge) | **125/150 = 83.3%** | reasoning OFF, 768 tok | 0 |

Both land squarely in the expected band for a healthy Qwen3-class 27B, so
**abliteration cost little or no capability here**. Combined with 100% compliance
on the benign split, the checkpoint is uncensored *and* intact — the failure mode
where abliteration lobotomises a model is not present.

### A measurement trap this exposed, twice

A first MMLU pass scored 67.3% with **38/150 unparsed**. Every one of those had
`finish_reason: length`: the model wrote ~2,400 characters of explanation and was
cut off before reaching the answer tag. Asking for the letter FIRST instead of
last took unparsed from 38 to 0 and the score from 67.3% to 83.3%. The 16-point
"gap" was entirely prompt design, not model ability.

That is the same root cause as the 68% truncation in the refusal eval: **this
model is verbose, and any measurement with a tight token budget silently
under-reports it.** Put the gradeable token first, or pay for a large budget.

## 5. Deployment caveat worth more than the rates

**With the default chat template this model reasons past any modest token budget
and returns an empty answer.** At `max_tokens: 512` with thinking on, 68% of
requests produced no `content` at all — the entire budget went to the `reasoning`
field. Callers need either a large `max_tokens` or
`chat_template_kwargs: {"enable_thinking": false}`. This is not a safety
behaviour and must not be mistaken for one; an early version of this eval scored
those empty responses separately as `truncated` for exactly that reason.

## 6. Reproducing

```
./needle_context_test.py --base http://10.10.20.10:8000/v1 \
    --model qwen3.8-27b-uncensored --depths 2048,8192,32768,131072,240000 \
    --positions 0.1,0.5,0.9 --max-tokens 512 --out results/needle.jsonl

./run_refusal_eval.py --base http://10.10.20.10:8000/v1 \
    --model qwen3.8-27b-uncensored --data <jbb>/data --split both \
    --no-think --concurrency 12 --max-tokens 400 --out results/refusal.jsonl

# correctness (needs pyarrow; a venv is fine)
./run_correctness_eval.py --base http://10.10.20.10:8000/v1 \
    --model qwen3.8-27b-uncensored --gsm8k <gsm8k>/main/test-*.parquet \
    -n 150 --max-tokens 1536 --out results/gsm8k.jsonl
./run_correctness_eval.py --base http://10.10.20.10:8000/v1 \
    --model qwen3.8-27b-uncensored --mmlu <mmlu>/all/test-*.parquet \
    -n 150 --max-tokens 768 --no-think --out results/mmlu.jsonl
```

Raw generations are gitignored. Note the filler in both harnesses averages
~5.8–6.2 characters per token, so nominal `--depths` and `--pad-tokens` run
well above the achieved token counts; always read measured `prompt_tokens`.
