---
type: concept
title: Abliteration & Refusal Evaluation
description: The uncensored/abliterated recipe family on this pair — weight-baked abliteration vs. runtime refusal-projection — and the JailbreakBench-based refusal evaluation and full-context needle methodology used to characterize them.
tags: [abliteration, refusal-eval, jailbreakbench, uncensored, evaluation, red-team]
sources:
  - id: openwiki-source-8e8938d8ee8b250a61e4bfb0
    resource: repo://benchmarks/redteam/README.md
  - id: openwiki-source-21849df8eea39edddabaddba
    resource: repo://benchmarks/redteam/RESULTS-qwen3.8-27b-uncensored-2026-10-01.md
  - id: openwiki-source-7845db45164b8996bda8b203
    resource: repo://images/deepseek-rank1/README.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
---

# Abliteration & Refusal Evaluation

A substantial part of this registry is a family of **uncensored / abliterated**
recipes — checkpoints whose refusal behavior has been removed or made
controllable. This page documents how such a model is produced in two different
ways on this pair, and the methodology used to *characterize* one before it is
trusted. The goal of the evaluation is measurement, not generation of harmful
content.

## Two mechanisms: baked-in vs. runtime

**Weight-baked abliteration.** Most of the uncensored recipes point at a
checkpoint whose refusal directions were removed in the weights themselves
(for example the Qwen and GLM "abliterated" and the DeepSeek "uncensored"
checkpoints). The recipe is an ordinary serve recipe; the abliteration is a
property of the weights, so the endpoint must be kept off public ingress and
away from untrusted input.

**Runtime refusal projection (a "dial").** One recipe,
`deepseek-v4-flash-0731-refusal-dial-tp2`, instead serves **stock** weights
through a locally built image, `spark-forge/vllm-dsv4-rank1`, that bakes a small
set of rank-1 refusal *directions* (a ~758 KB `refusal_dirs.safetensors`) and
applies them at inference time. The projection is inert unless
`VLLM_REFUSAL_DIRS` is set, the engine boots at strength (lambda) 0, and the
strength is set at runtime over HTTP. This makes the degree of abliteration a
tunable serving parameter rather than a fixed property of the weights. The image
exists only on the two nodes because upstream publishes none; its provenance and
rebuild steps are recorded alongside it.

## Refusal evaluation: both splits are scored

Refusal behavior is measured with the **JailbreakBench JBB-Behaviors** set — 100
harmful behaviours across 10 policy categories, plus 100 category-matched benign
controls. Prompts come from the published benchmark so results are comparable to
the JailbreakBench literature.

The design decision that matters: **both splits are scored, not just the harmful
one.** A properly abliterated checkpoint should comply with *both* harmful and
benign prompts. High harmful compliance with *low* benign compliance is the
signature of abliteration that **damaged** the model rather than merely removing
its refusals — and the benign controls are the only way to see that. The eval
run on the Qwen 27B uncensored checkpoint, for instance, pairs its 100/100
harmful compliance with 100/100 benign compliance and substantive benign
answers, which is what makes "the abliteration is clean" a defensible claim
rather than just "it will answer anything".

Two caveats are documented and load-bearing when reading a scorecard:

- The grader is **keyword refusal detection** — the standard cheap method. It
  over-counts refusals when a model declines in novel phrasing, so a flagged
  refusal can be a false positive (a hedge that then complies). Treat the
  scorecard as a screen and read the raw JSONL for anything surprising.
- `--pad-tokens` reruns the same split **at context depth**. Running a split
  short and then padded, and diffing the rates, tests whether safety behaviour
  degrades with context length — the documented many-shot effect, and the reason
  full-context numbers matter for an uncensored model.

## Full-context needle testing

A recipe's advertised `max_model_len` says nothing about whether the model can
actually *use* that context. The `needle_context_test.py` harness places a
passkey needle at several depths and positions across increasing context sizes
and checks retrieval plus prefill cost, so "serves a 262k window" is only
claimed once a needle has been retrieved near that depth. On the Qwen 27B
uncensored checkpoint this produced 21/21 correct retrievals across depths and
positions up to ~247k tokens, and also surfaced a prefill-cost cliff at high
depth — a property retrieval accuracy alone would have hidden.

Raw generations from these harnesses are gitignored on purpose; the committed
artifacts are the scorecards and result summaries.

## Related

- [Benchmarking & Context Verification](../workflows/benchmarking.md)
- [Model Inventory & Weight Safety](../reference/model-inventory-and-weights.md)
