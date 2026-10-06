# Uncensored model ranking — dgx-pair, measured 2026-10-01/02

Nine abliterated or uncensored checkpoints with weights on disk, each run through
the same suite: JailbreakBench JBB-Behaviors (100 harmful + 100 category-matched
benign), GSM8K at n=150, MMLU at n=150. Every number here was measured on this
hardware; nothing is inherited from a model card.

Harnesses and raw records: `benchmarks/redteam/`. Raw generations are gitignored.

## The ranking

`avg` is the mean of GSM8K and MMLU. Tiers are gated on fitness for purpose
first, because a model that refuses is not an uncensored model however well it
scores.

| # | Model | GB | Harmful | Benign | GSM8K | MMLU | avg |
|---|---|---|---|---|---|---|---|
| **1** | **Gemma-4-26B AEON** | 16 | 100% | 100% | **96.7** | 86.0 | **91.3** |
| **2** | **Qwen3.8-27B refusal-dial** | 23 | 100% | 100%* | 96.0 | 86.0 | **91.0** |
| **3** | **Gemma-4-12B AEON K4** | **9** | 100% | 100% | 96.0 | 84.0 | **90.0** |
| 4 | Qwen3.8-27B-Uncensored | 25 | 100% | 100% | 96.0 | 83.3 | 89.7 |
| 5 | Qwen3.6-27B AEON Ultimate | 28 | 100% | 100% | 75.3 | **87.3** | 81.3 |
| 6 | Gemma-4-31B DECKARD-HERETIC | 20 | 100% | 99% | 64.7 | 74.0 | 69.3 |
| — | *Nemotron-3-Nano-Omni AEON* | 22 | **93%** | 100% | 92.7 | 73.3 | 83.0 |
| — | *Qwen3.6-35B-A3B heretic* | 23 | **74%** | 99% | 79.3 | **88.0** | 83.7 |
| — | *DeepSeek-V4-Flash-Vision Unc.* | 168 | 100% (58/58) | **crashed** | — | — | — |

\* benign split covered 59 of 100 before a stage timeout; all 59 complied.
Italic rows are disqualified from the ranking — the first two refuse, the third
is unstable.

## Picks

- **Default: Gemma-4-26B AEON.** Highest combined score, fully uncensored, fully
  intact on benign controls, and the fastest model measured — it finished 150
  GSM8K problems in 64 seconds, being a ~4B-active MoE.
- **Tight on memory: Gemma-4-12B AEON K4 at 9 GB.** It reaches 90.0 against the
  leader's 91.3 at 56% of the footprint, matches it on math, and was the only
  model in the set with zero unparsed answers. Best capability per gigabyte by a
  wide margin.
- **Highest knowledge: Qwen3.6-35B heretic at 88.0 MMLU** — but it refuses a
  quarter of harmful requests, so only pick it if uncensored behaviour is not the
  requirement.
- **Multimodal: Nemotron-3-Nano-Omni AEON** is the only one taking image, audio
  and video. It refuses 7%, so it is a specialist rather than a default.

## Four findings that change how to read the fleet

**1. "Uncensored" has meant three different things.** Compliance on harmful
behaviours ranges from 74% to 100% across models the index described
identically. Nobody had measured refusal before this sweep. Naming does not
predict it either: AEON builds span 93–100% and the "heretic" build is the
*least* abliterated at 74%.

**2. Abliteration quality dominates model size.** Within the Gemma-4 family the
12B scores 90.0 and the 31B DECKARD scores 69.3 — the smaller model is 20 points
better. DECKARD also truncated 27 correctness answers, the worst in the set.
Something in that abliteration did real damage. Do not assume a bigger
abliterated model is a better one.

**3. Runtime abliteration beats baked abliteration.** The refusal-dial is not a
modified checkpoint; it applies a rank-1 refusal projection at inference to stock
unsloth weights. Against the baked orcarouter model of the same family it ties on
math and is 2.7 points better on MMLU, both at full compliance. Nothing is
permanently removed from the weights, which is the likely mechanism. Prefer this
approach when a stock checkpoint exists.

**4. Base family predicts the capability shape.** Both Qwen3.6 models are
knowledge-strong and math-weak (87–88 MMLU, 75–79 GSM8K). Gemma-4-26B, Gemma-4-12B
and both Qwen3.8 models sit at ~96 on math. Choose the family for the workload
before choosing the abliteration.

## Measurement notes worth keeping

- **Always score a benign control split.** Gemma-4-31B first reported 0% on both
  splits, which is impossible for a working model and was therefore self-evidently
  a harness bug. With only a harmful split it would have been recorded as
  "refuses everything" and believed.
- **These models are verbose; size the token budget for the worst case.** A
  400-token budget truncated 200/200 Gemma-4-31B responses into the reasoning
  field with empty content. Probing with a trivial prompt does not help, since
  reasoning length is prompt-dependent — "say ping" answered directly at 400
  tokens from the same model that then truncated every real prompt. The suite now
  uses 1400 unconditionally.
- **Ask for the gradeable token first.** MMLU read 67.3% with 38/150 unparsed
  when the answer was requested last, and 83.3% with 0 unparsed when requested
  first. That 16-point swing was prompt design, not ability.
- **`sparkrun --no-rm` does not preserve crashed containers on this version.**
  It discarded the logs three separate times during this sweep, including
  DeepSeek's crash. Any startup or runtime failure is invisible by default, which
  is the single biggest obstacle to debugging this fleet.

## DeepSeek, separately

`deepseek-v4-flash-vision-uncensored-tp2` is marked VERIFIED since 2026-09-26,
but that verification was a short benchmark sweep. Under 200 sustained requests
it served 58 harmful behaviours with zero refusals, then the engine began
returning HTTP 500 and 94 of 100 benign requests failed, taking GSM8K, MMLU and
the needle pass down with it. It had the pair to itself — the worker's reranker
was stopped and 115 GB was free — so this is not the co-tenant collapse its
recipe warns about. **Verified and production-ready are different claims, and
this is the gap.** Needs a retry to establish whether the crash reproduces.
