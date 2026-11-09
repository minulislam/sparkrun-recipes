---
type: concept
title: Recipe Anatomy
description: The structure of a sparkrun v2 recipe YAML in this registry — identity (model/container/runtime), placement (min/max_nodes), readiness, the defaults block, the command template with its {placeholder} substitution, the env block, the executor_config entrypoint rule, and the memory-fit knobs.
tags: [recipe, yaml, schema, vllm, configuration]
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
  - id: openwiki-source-c60867cd14827f47e426d16c
    resource: repo://notes/minimax-m3-sparkrun-port/minimax-m3-w4a16-gptq-b12x-nvfp4-eagle3.yaml
  - id: openwiki-source-036e64f955b6e8c14e4c8d88
    resource: repo://notes/minimax-m3-sparkrun-port/README.md
  - id: openwiki-source-67c295973f38e30669ebf01c
    resource: repo://recipes/glm-5.3-flash-exl3-abliterated-tp2.yaml
  - id: openwiki-source-5c02b2143bb9723499b2edf3
    resource: repo://recipes/mods/glm53-exl3-gb10-topk/run.sh
  - id: openwiki-source-b1867d7f36dadf1642430baf
    resource: repo://recipes/qwen3-embedding-4b-tp1.yaml
  - id: openwiki-source-5c6fb7c964f2f95da074a267
    resource: repo://recipes/qwen3-reranker-4b-tp1.yaml
  - id: openwiki-source-9c55c8fb4c58db89d64b13df
    resource: repo://recipes/qwen3.8-flash-next-abliterated-nvfp4-tp2.yaml
generated: { by: "claude-code", at: "2026-11-08T21:00:19.321Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
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

## Mods: pre-serve patches under `recipes/mods/`

A recipe can list directories under a top-level `mods:` key:

```yaml
mods:
  - mods/glm53-exl3-gb10-topk
```

Each mod directory holds a `run.sh` that sparkrun executes **inside every
rank's container before serve**. Mods exist to patch a prebuilt image for this
platform without rebuilding it — the worked example disables vLLM's
decode-path `persistent_topk` in the `:exl3` GLM image, which otherwise kills
the engine on long-history decode on GB10 (SM121) with a shared-memory
oversubscription error. A good mod is idempotent (detects an already-applied
patch), fails loudly if the target pattern is missing, and carries upstream
attribution/licensing files when the edit is ported from another project
(see `mods/glm53-nvfp4kv-overlays/CREDITS.upstream.md`).

## `scheduler` and `distribution_config` (per-recipe placement overrides)

Two less-common top-level keys appear in the MiniMax-M3 port
(`notes/minimax-m3-sparkrun-port/`):

- `scheduler: greedy` — opts the recipe out of the `occupancy-sparse` scheduler
  (the 0.3.x default for new clusters), whose VRAM estimate is a hard admission
  check. For models whose estimate is inflated (MiniMax-M3's reads 115.2 GB per
  rank against a 121 GB accelerator) occupancy-sparse refuses to place any rank;
  `greedy` places them and lets vLLM's own memory profiler be the authority.
  The override is per-recipe and does not weaken placement elsewhere.
- `distribution_config:` — explicitly lists the artifacts sparkrun must stage to
  each node. Listing `models.entries` **replaces** the default single-entry
  list, so the main checkpoint must be re-listed alongside any extra artifact
  (the MiniMax recipe adds its 1.6 GB EAGLE3 drafter, which auto-detection
  misses because the spec config is inline in the command). Omitting
  `containers` keeps the default image-distribution entry.

## Pooling-runner recipes and the `sparkroute` capabilities block

Not every recipe serves chat. `recipes/qwen3-embedding-4b-tp1.yaml` and
`recipes/qwen3-reranker-4b-tp1.yaml` (rows 65–66, added 2026-11-08) serve
vLLM's **pooling runner** instead — the command passes `--runner pooling`, and
the endpoint answers `/v1/embeddings` (embedding) or `/v1/rerank` (reranker)
rather than chat completions. They are deliberately small fits
(`gpu_memory_utilization: 0.3`, 7.5 GiB of weights) so they can share a node.

Two schema consequences:

- An **embedding** recipe must declare its capability to the gateway, or
  SparkRoute refuses to route it:

  ```yaml
  sparkroute:
    capabilities: [single_vector_embedding]
  ```

  The reranker recipe carries no such block because SparkRoute 0.3.4 has no
  rerank route at all — callers hit the container endpoint directly (see the
  proxy & gateway routing page).
- sparkrun's readiness probe expects a chat token, so it reports pooling
  runners as **never-ready**; ignore the probe for these recipes and verify via
  the pooling endpoint instead.

Recipes adapted from an upstream registry open with `# >>> ADAPTED from …`
header comments recording the source recipe, fetch date, what was changed and
why, and the verification status — both pooling recipes were adapted from the
`@official` Qwen3-VL 8B pair (no 4B exists in the VL series, so the text-only
4B checkpoints were substituted).

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
