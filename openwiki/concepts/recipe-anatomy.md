---
type: concept
title: Recipe Anatomy
description: The structure of a sparkrun v2 recipe YAML in this registry — identity (model/container/runtime), placement (min/max_nodes), readiness, the defaults block, the command template with its {placeholder} substitution, the env block, the executor_config entrypoint rule, and the memory-fit knobs.
tags: [recipe, yaml, schema, vllm, configuration]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-9c55c8fb4c58db89d64b13df
    resource: repo://recipes/qwen3.8-flash-next-abliterated-nvfp4-tp2.yaml
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
---

# Recipe Anatomy

A recipe is a single YAML file in `recipes/` that fully specifies one served
model: its checkpoint, container, runtime flags, and fit. This page describes
the fields using `recipes/qwen3.8-flash-next-abliterated-nvfp4-tp2.yaml` as the
worked example; the specific values there are that recipe's, not defaults for
every recipe.

## Identity and placement

```yaml
recipe_version: "2"
model: dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4
runtime: vllm
container: ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926
min_nodes: 2
max_nodes: 2
```

- `recipe_version: "2"` — the sparkrun v2 schema these recipes use.
- `model` — the HuggingFace checkpoint id.
- `runtime` — the engine (typically `vllm`).
- `container` — an **immutable-tagged** image; see the image policy for the
  selection order and why a dated tag beats a digest pin on this cluster.
- `min_nodes` / `max_nodes` — how many nodes the workload needs. A `2`/`2`
  recipe is a two-node tensor-parallel workload on `dgx-pair`; a one-node recipe
  sets `1`/`1` and is launched with `--tp 1`.

## Readiness and metadata

A `readiness:` block raises the timeouts (`port_timeout_s`, `health_timeout_s`,
`inference_timeout_s`) because large MoE checkpoints can take many minutes to
load and capture CUDA graphs before the endpoint serves. A `metadata:` block
carries a human description, maintainer/attribution, and declared dtype/VRAM.

## The `defaults` block and the `command` template

The `defaults:` block holds every tunable as a key:

```yaml
defaults:
  tensor_parallel: 2
  gpu_memory_utilization: 0.7
  max_model_len: 262144
  kv_cache_dtype: fp8
  num_speculative_tokens: 4
  served_model_name: qwen3.8-flash-next-abliterated
```

The `command:` block is the literal engine invocation, with `{placeholder}`
tokens that sparkrun substitutes from `defaults` (and from CLI/`-o` overrides)
at launch — for example `--tensor-parallel-size {tensor_parallel}`,
`--max-model-len {max_model_len}`, `--served-model-name {served_model_name}`.
This split lets an operator override any default from the command line without
editing the file. The served name set here is the model id the endpoint
advertises and that benchmark/needle harnesses must target.

## The `env` block

`env:` sets container environment variables that tune the engine or work around
platform quirks (loader selection, kernel/backend choices, transport toggles).
These are engine/image concerns and are distinct from the cluster-level
communication pins, which live in the cluster definition, **not** in the recipe.

## The executor_config entrypoint rule

Some images bake `ENTRYPOINT ["vllm","serve"]`. A recipe whose `command`
re-invokes `vllm serve` must clear that entrypoint with
`executor_config: {entrypoint: ""}`, or the two stack and the container fails to
start. This is a per-image property, so it is set on the recipes whose image
needs it.

## Fit: the memory knobs

GB10 is **unified memory** — weights and KV cache come out of the same ~121 GiB
the host OS uses — so three fields together decide whether a recipe boots and
how much context it can hold per request:

- `gpu_memory_utilization` — the fraction of memory the engine may claim. The
  working range on this pair is **0.70–0.82**; 0.85 has caused NVRM OOM at boot.
- `max_model_len` — the per-request context ceiling. May be an explicit number
  or `auto` (let the engine size it to the checkpoint's native maximum).
- the KV cache controls — `kv_cache_dtype` (e.g. `fp8`) and, on some recipes, an
  explicit `kv_cache_bytes` pin that reserves a fixed KV pool instead of letting
  it absorb all free memory. A smaller `max_model_len` or a KV pin is how a
  recipe trades per-request context for the batch headroom an agent loop needs.

After launch, the engine's effective `max_model_len` should be read back from
`/v1/models`, and the serve log lives at `/tmp/sparkrun_serve.log` **inside the
container** (not in `docker logs`).

## Related

- [Container Images & Provenance](../reference/images-and-provenance.md)
- [Authoring & Changing Recipes](../workflows/authoring-recipes.md)
