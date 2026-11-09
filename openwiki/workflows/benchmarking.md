---
type: workflow
title: Benchmarking & Context Verification
description: How recipes get measured — the canonical quick throughput ladder, the needle-in-haystack full-context harness, the mem/results artifacts (the ground truth since nvidia-smi reports N/A on GB10), and the INDEX/benchmarks recording convention.
tags: [benchmarking, throughput, context, needle, workflow, measurement]
sources:
  - id: openwiki-source-af5b2fc4a0830cd3de40e530
    resource: repo://benchmarks/README.md
  - id: openwiki-source-f2fa2c5d988e34496c32de5f
    resource: repo://benchmarks/redteam/needle_context_test.py
  - id: openwiki-source-c14951f9251e738c0eb1ed0a
    resource: repo://benchmarks/results_inkling-small-tp2-20261103.yaml
  - id: openwiki-source-56477e1b1ab6b670861f1147
    resource: repo://benchmarks/results_qwen38-flash-next-tp2-20261103.yaml
  - id: openwiki-source-39c3295efc089133e87a9c80
    resource: repo://CONTEXT.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-036e64f955b6e8c14e4c8d88
    resource: repo://notes/minimax-m3-sparkrun-port/README.md
generated: { by: "claude-code", at: "2026-11-08T21:00:19.321Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
---

# Benchmarking & Context Verification

Benchmarking is the bar **above** verified: a verified recipe answered a
request; a benchmarked one also has measured numbers recorded in `benchmarks/`.
Two independent harnesses produce those numbers — a throughput ladder and a
full-context retrieval test — because they answer different questions.

## Never benchmark the first request

The first request after boot pays one-time costs — JIT kernel compilation,
graph capture, cache warms — that are not steady-state performance. On the
MiniMax-M3 b12x stack the first-request warmup penalty is **~60 s**, and the
penalty recurs per *workload shape*: even a recipe whose `post_commands` burns
a warmup request after the health gate still needs one more burned per shape
(prompt length / concurrency pattern) before numbers are recorded.

## The quick throughput ladder

The canonical throughput profile is the **quick ladder**: concurrency 1 and 8
crossed with context depths 0, 8k, and 32k (`pp2048`/`tg128`). Running the same
ladder for every recipe is what makes recipes comparable to each other and to
the fleet sweep. It captures both the single-stream decode rate (c=1) and the
8-way aggregate, and because it runs at depth it exposes where a recipe's
prefill or concurrency collapses — the fleet sweep found, for instance, recipes
that are fine at c=1 but fall apart at 8-way × 32k.

Per-recipe harness output lands as two artifacts:

- **`results_<label>.json`** — streamed TTFT and decode tok/s (three runs),
  long-context prefill rate, the 8-way concurrent aggregate, and
  quality-probe transcripts. This is the number-of-record; wiki prose should
  point here rather than restate figures.
- **`mem_<label>.txt`** — captured vLLM log lines: "Model loading took", "GPU KV
  cache size", and "Maximum concurrency". On GB10 `nvidia-smi` reports `[N/A]`
  for memory, so **these log lines are the ground truth** for KV pool size and
  per-request concurrency, not a GPU-memory query.

## The needle-in-a-haystack context test

A recipe's `max_model_len` is a claim, not a capability. `needle_context_test.py`
places a passkey needle at several depths and positions across increasing
context sizes and checks both retrieval correctness and prefill cost, so "serves
an N-token window" is only asserted once a needle has been retrieved near depth
N. It talks plain OpenAI-compatible HTTP, so it runs against any served
workload, and it is what turns an advertised context length into a measured one
(and surfaces prefill-cost cliffs that retrieval accuracy alone would hide).

## Numbers are only as good as the fabric: the 2026-11-03 re-benchmarks

Benchmark figures are measurements of the recipe **on the cluster as
configured that day**, and a fabric defect silently caps them. After the CX7
MTU fix (see cluster & networking), `qwen3.8-flash-next-nvfp4-tp2` — same
recipe, same image as the 09-27 baseline — re-measured at tg128 c=1 **73.7
tok/s vs 46.3 (+59%)** and c=8 at tg=256 **118.5 aggregate vs 92.3 (+28%)**,
with pp2048 roughly unchanged. Raw:
`benchmarks/results_qwen38-flash-next-tp2-20261103.{json,csv,yaml}`. Earlier
two-node decode numbers therefore understate the recipes measured before the
fix.

Two caveats from that session:

- **tg128 is unreliable at c=8.** With ~4.8 s of TTFR stagger across 8
  requests, a 128-token window overlaps too little concurrency — the run read
  38.5 aggregate while per-request decode matched baseline. **Use tg=256 (or
  longer) for c=8 comparisons.**
- **llama-benchy can record no steady-state tg for SGLang servers.** The
  `inkling-small-nvfp4-tp2-sglang` re-run produced pp2048 1678 (c1) / 1381
  (c8) but only peak decode figures — a parsing quirk of the harness against
  that server, not a server failure. Raw:
  `benchmarks/results_inkling-small-tp2-20261103.*`.

## Recording convention

When a recipe is benchmarked, the results are recorded in three places that stay
consistent:

1. the raw artifacts under `benchmarks/` (`results_*.json` / `.csv` and
   `mem_*.txt`);
2. the recipe's **`INDEX.md`** row, updated to **BENCHMARKED `<date>`** with a
   short measured summary (row numbers are never renumbered);
3. a dated **`HISTORY.md`** entry.

Reports in `benchmarks/` are dated and **ordered** — a later report corrects or
supersedes earlier ones where they disagree, so the most recent date is read
first. Every number is measured live on `dgx-pair`; nothing is estimated from a
spec sheet.

## Related

- [Recipe Status Vocabulary](../concepts/status-vocabulary.md)
- [Memory, Placement & Known Pitfalls](../operations/memory-placement-and-pitfalls.md)
- [Abliteration & Refusal Evaluation](../concepts/abliteration-and-refusal-eval.md)
