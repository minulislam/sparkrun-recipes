---
type: workflow
title: Benchmarking & Context Verification
description: How recipes get measured — the canonical quick throughput ladder, the needle-in-haystack full-context harness, the mem/results artifacts (the ground truth since nvidia-smi reports N/A on GB10), and the INDEX/benchmarks recording convention.
tags: [benchmarking, throughput, context, needle, workflow, measurement]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-af5b2fc4a0830cd3de40e530
    resource: repo://benchmarks/README.md
  - id: openwiki-source-f2fa2c5d988e34496c32de5f
    resource: repo://benchmarks/redteam/needle_context_test.py
  - id: openwiki-source-39c3295efc089133e87a9c80
    resource: repo://CONTEXT.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
---

# Benchmarking & Context Verification

Benchmarking is the bar **above** verified: a verified recipe answered a
request; a benchmarked one also has measured numbers recorded in `benchmarks/`.
Two independent harnesses produce those numbers — a throughput ladder and a
full-context retrieval test — because they answer different questions.

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
