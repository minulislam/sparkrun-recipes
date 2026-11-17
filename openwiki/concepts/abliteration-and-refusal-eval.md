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
  - id: openwiki-source-032573fa0676b71689223dc4
    resource: repo://docs/superpowers/specs/2026-11-10-inkling-small-refusal-dial-design.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-7845db45164b8996bda8b203
    resource: repo://images/deepseek-rank1/README.md
  - id: openwiki-source-8ecf4234b6f64fce2b52016c
    resource: repo://recipes/deepseek/deepseek-v4-flash-0731-refusal-dial-tp2.yaml
  - id: openwiki-source-ab401ad6d69429e93d3b021b
    resource: repo://recipes/qwen/qwen38-27b-nvfp4-refusal-dial.yaml
generated: { by: "claude-code", at: "2026-11-17T14:41:15.503Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-17T14:41:15.503Z
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
Both dial recipes live under their family folders:
`recipes/qwen/qwen38-27b-nvfp4-refusal-dial.yaml` and
`recipes/deepseek/deepseek-v4-flash-0731-refusal-dial-tp2.yaml`. The DeepSeek
dial was re-served from its new path on 2026-11-17 (ready in 323 s with a
393,216-token context) after its weights were also synced to the worker.

### The Inkling dial was dropped

A third dial, `inkling-small-nvfp4-refusal-dial-tp2`, was added on 2026-11-10.
It patched stock Inkling-Small at runtime through a mod overlay
(`recipes/mods/inkling-refusal-dial/`) instead of a custom image. **It never
served.** Its first live boot on dgx-pair hit a `PermissionError` because the
copied directions file stayed at mode 0600. The second boot crashed in the b12x
image's multimodal warmup (`mark_b12x_eager_shapes` with `encoder_rows=None`),
which was then worked around by serving text-only. The third boot was stopped
when the pair was needed elsewhere. On 2026-11-17 the recipe, the mod and their
three pytest files were deleted on request. Inkling stays on its SGLang recipe
(`recipes/inkling/inkling-small-nvfp4-tp2-sglang.yaml`). The design and plan
under `docs/superpowers/` are kept as records, and the directions file remains
in git history.

## Setting lambda from a hook: use plain braces

Both remaining dials set lambda in `post_exec` with a JSON body posted to
`/admin/refusal_lambda`. **Write that JSON with single braces.** sparkrun's hook
renderer (`orchestration/hooks.py`) does not unescape `{{` inside hooks, so a
doubled-brace payload is posted literally as `{{"lambda": 2.0}}`. That is
invalid JSON, and the dial silently stays at 0. This happened on the
2026-11-17 DeepSeek re-serve. Both dial recipes were fixed the same day, and
the rendered command was checked to set lambda 2.0 on both ranks. Always read
the dial back with `GET /admin/refusal_lambda` after boot (both recipes do this
in `post_exec`) rather than trusting the hook ran.

The `/admin/refusal_lambda` endpoint has **no auth**, and a lambda above 0 also
weakens resistance to prompt injection. Keep dial endpoints off public ingress.
Changing lambda invalidates the prefix cache, so the first request after a
switch re-prefills.

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
- [Recipe Anatomy](../concepts/recipe-anatomy.md)
- [Images & Provenance](../reference/images-and-provenance.md)
