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
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-032573fa0676b71689223dc4
    resource: repo://docs/superpowers/specs/2026-11-10-inkling-small-refusal-dial-design.md
  - id: openwiki-source-7845db45164b8996bda8b203
    resource: repo://images/deepseek-rank1/README.md
  - id: openwiki-source-47b542f6d1c02a514532bbb4
    resource: repo://recipes/deepseek-v4-flash-0731-refusal-dial-tp2.yaml
  - id: openwiki-source-afd4b883e2d77bfe356a5248
    resource: repo://recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml
  - id: openwiki-source-6f45ee15500398be92731378
    resource: repo://recipes/mods/inkling-refusal-dial/patch_vllm.py
  - id: openwiki-source-28bdb53b0ca2f20523767328
    resource: repo://recipes/mods/inkling-refusal-dial/run.sh
  - id: openwiki-source-d617492bf9fc1cb81eb1dadd
    resource: repo://recipes/qwen38-27b-nvfp4-refusal-dial.yaml
  - id: openwiki-source-5b4bfb81d2ac388e627c6d62
    resource: repo://tests/test_recipe_schema.py
generated: { by: "claude-code", at: "2026-11-12T21:00:08.984Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-14T21:00:11.653Z
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

**Runtime refusal projection (a "dial").** A few recipes instead serve
**stock** weights and remove the refusal direction at inference time. The
strength (lambda) is set over HTTP, so the degree of abliteration becomes a
serving parameter rather than a fixed property of the weights:

- `qwen38-27b-nvfp4-refusal-dial` uses a published image
  (`docker.io/pocharlies/vllm-qwen38-rank1:20260815`) and published directions.
  Its header records that `VLLM_REFUSAL_LAMBDA_INIT` is ignored on that image:
  the server always starts at 0, and a `post_exec` call sets the real value.
- `deepseek-v4-flash-0731-refusal-dial-tp2` uses a locally built image,
  `spark-forge/vllm-dsv4-rank1`, that bakes a ~758 KB `refusal_dirs.safetensors`.
  The projection is inert unless `VLLM_REFUSAL_DIRS` is set, and the engine boots
  at lambda 0. The image exists only on the two nodes because upstream publishes
  none; its provenance and rebuild steps are recorded alongside it. The recipe's
  `post_exec` then sets lambda to 2.0 once the endpoint is up, matching the
  header's "use lambda 2.0, not upstream's 1.5" note (the JailbreakBench run
  recorded 93/100 harmful complied at 2.0 versus 82/100 at 1.5).
- `inkling-small-nvfp4-refusal-dial-tp2` (added 2026-11-10, **UNVERIFIED**) serves
  stock `thinkingmachines/Inkling-Small-NVFP4` at TP=2 on the stock
  `ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926` image. It needs no
  custom image. Instead it uses a **mod overlay**, `recipes/mods/inkling-refusal-dial/`.
  Before serve, that mod's `run.sh` runs in every rank's container. It copies
  `refusal_dirs_inkling.safetensors` to `/opt/refusal/`, installs
  `refusal_projection.py` and an admin API router into the vLLM package, and runs
  `patch_vllm.py`. The patch edits vLLM's Inkling decoder layer so that the
  attention output passes through the rank-1 projection. Finally, `run.sh`
  byte-compiles the installed and patched modules and runs a self-check
  (`verify_inkling_rank1.py`, installed to `/opt/refusal/`). Lambda is set with
  `POST /admin/refusal_lambda`, and the recipe's `post_exec` sets it to 1.
  The design doc gives lambda 0 as bit-exact to stock. It also describes how the
  per-layer directions were extracted, using contrastive harmful/benign prompt
  pairs and `benchmarks/redteam/extract_contrastive_directions.py`.
  Two cautions apply before a first launch. First, the recipe sets
  `gpu_memory_utilization: 0.85`, above the house range of 0.70–0.82; 0.85 has
  caused NVRM OOM at boot here. Second, Inkling-Small's weights are on the head
  only (see the model inventory page).
  `tests/test_recipe_schema.py` pins the recipe's shape: TP=2 on exactly two
  nodes, the `VLLM_REFUSAL_DIRS` and `VLLM_REFUSAL_LAMBDA_INIT` env vars, the
  `mods/inkling-refusal-dial` mod, and an `admin/refusal_lambda` call in
  `post_exec`.

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
