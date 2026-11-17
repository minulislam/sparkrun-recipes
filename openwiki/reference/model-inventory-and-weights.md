---
type: reference
title: Model Inventory & Weight Safety
description: What MODELS.md records about which checkpoints are complete, partial, or stubs on each node and which recipes use them, the shared HF blob store that makes deletion subtle, and the standing rules for handling weights safely (back up before delete, deletion is the operator's call, never hf cache prune).
tags: [models, weights, inventory, storage, safety]
sources:
  - id: openwiki-source-d844af9966f902d563fa3f52
    resource: repo://benchmarks/MIAAI-LAB-VALIDATION-RESULTS-2026-10-16.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
  - id: openwiki-source-456fceaa0ae7a8e901be70bf
    resource: repo://MODELS.md
generated: { by: "claude-code", at: "2026-11-17T14:41:15.503Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-17T14:41:15.503Z
---

# Model Inventory & Weight Safety

A recipe serves only if its checkpoint is present and complete on every node it
launches on. `MODELS.md` is the inventory of record for that. A small set of
rules governs the weights, because they are expensive to replace.

## The inventory (`MODELS.md`)

`MODELS.md` records which checkpoints are on disk on each node, their size, and
which recipes use them. Each pass is a dated measurement. The current pass was
measured on both nodes on **2026-11-10** with the script in its *Regenerate*
section, and it replaces the 2026-10-13 pass. Treat it as "what was true on
that date" and re-check the live cluster before acting on it.

Each repo gets one status:

- **Complete**: every shard named in `model.safetensors.index.json` resolves to
  a real file, and the byte sum reaches `metadata.total_size`.
- **Partial**: some shards are missing.
- **Stub**: the repo has no weight files at all.

Sizes are GiB of weight files only (`.safetensors`, `.gguf`, `.bin`), not the
size of the cache directory. One known false positive: the script reports
`local-inference-lab/Qwen3.8-Flash-Next-NVFP4` as SHORT, but all 40 shards match
the Hub byte for byte. The publisher's index overstates the total.

## Where the weights are (2026-11-10)

- **The worker holds only 5 checkpoints.** A TP2/EP2 recipe needs its weights on
  **both** nodes. Only one two-node recipe has that today:
  `glm-5.3-flash-abliterated-nvfp4kv-long-tp2`. The other 14 two-node recipes
  have weights on the head only. That includes several recipes that were
  SparkRoute gateway bindings at the time (Flash-Next abliterated, GLM-5.3 abliterated and EXL3, both
  DeepSeek-V4-Vision recipes). Their first cold start has to copy or download
  the weights to the worker first. The worker had about 2.5 TiB free, enough
  for all of them (about 1.5 TiB in total).
- **Changes recorded since that pass (2026-11-17, in `HISTORY.md`, not yet in
  `MODELS.md`):** `deepseek-ai/DeepSeek-V4-Flash-0731` was rsynced to the
  worker over CX7 (48/48 shards, 155.4 GiB), so the DeepSeek refusal-dial TP2
  recipe now has its weights on both nodes. `nvidia/Qwen3.6-35B-A3B-NVFP4` is on
  both nodes and replaced the `unsloth` build, which was never downloaded. The
  new `nvidia/Qwen3.8-Flash-Next-FP4-Local` recipe has no weights on either node.
- Free space after the 2026-11-10 cleanup: head **618 GiB**, worker **2.5 TiB**.
- Single-node recipes that list `gx10-solo` as a gateway candidate can use the
  worker only where their weights are there. On 2026-11-10 that held for the
  embedding model and the 35B-A3B heretic checkpoint, but not for the reranker
  or the Nemotron Nano 30B checkpoint.
- Auxiliary artifacts (speculative-decode drafters, refusal-direction tensors)
  must be **pre-cached**, because serve containers run with `HF_HUB_OFFLINE=1`.

### The GLM topk2044 checkpoint moved to hub layout

The locally built `glm53-flash-ablit-topk2044` checkpoint used to sit outside
the hub, under `~/.cache/huggingface/spark-forge-local/`. On 2026-11-10 it was
first backed up to the NAS. It was then moved on both nodes into hub layout at
`~/.cache/huggingface/hub/models--local--glm53-flash-ablit-topk2044/snapshots/local`.
The recipe's `model_path` now points at the container path for that location.
Two-node launches of the recipe from the new path, and vLLM's acceptance of the
hub layout, had not been tested as of that entry.

## The shared blob store makes deletion subtle

On the head, repo blobs are hardlinks into a shared content store at
`~/.cache/huggingface/hub/blobs/<2-char>/<sha256>`; for
`Qwen/Qwen3-Reranker-4B` they are symlinks. Two consequences follow:

- **`du -sh` on a `models--*` directory is misleading.** Judge completeness
  against the weight index, not a byte count.
- **`hf cache rm` alone frees nothing.** It removes the repo side only. On
  2026-11-10, removing a superseded revision of
  `local-inference-lab/Qwen3.8-Flash-Next-NVFP4` freed no space until the 650
  store files that nothing still referenced were deleted (103.1 GB). Before you
  delete from the store, exclude every file that a hardlink or a symlink still
  references.

Several repos keep more than one snapshot revision. Three have a weightless
`main` and keep their weights in an older revision:
`AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4`,
`orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` and
`orcarouter/Qwen3.8-27B-Uncensored-NVFP4`. Their recipes pin that revision with
`model_revision:` and pass `--revision {model_revision}` to vLLM. The heretic
pin was added on 2026-11-10; without it, a launch resolved to a snapshot that
held only `config.json`.

## Weight-safety rules

- **Check `MODELS.md` before launching.** Confirm the checkpoint is complete on
  the target nodes first.
- **Back up before deleting.** Back up a checkpoint to
  `/mnt/nas/ai-models/model-backup/huggingface-hub/` before removing it. The
  2026-10-14 cleanup broke this rule: `/mnt/nas` was not a mountpoint, so
  checkpoints were deleted with no backup. That case is why the rule is
  explicit. The 2026-11-10 deletions were each checked against the NAS copy by
  name and size first.
- **Deleting weights is the operator's call**, not a decision for automation.
- **Never run `hf cache prune` for real.** Its dry run on 2026-11-10 listed about
  1.2 TB, including detached revisions that recipes pin. Delete specific
  revisions with `hf cache rm`, dry run first.

Whether a deleted checkpoint can be recovered depends on its source. One that
is still published upstream (for example the orcarouter Flash-Next checkpoint
deleted on 2026-10-14) can be downloaded again.

## Preserved external validation record

`benchmarks/MIAAI-LAB-VALIDATION-RESULTS-2026-10-16.md` keeps the MiaAI-Lab
abliterated-recipe validation report (3 PASS serve-only, 4 blocked or gated).
It also records per-recipe patches and the checkpoint cache status on both
nodes. The report was copied into this repo before the external `miaai-runner`
repo was deleted, so it is now the only copy of that evidence. The GLM-5.3-Flash
EXL3 abliterated recipe adopted into this registry (row 64) comes from that
validated set.

## Related

- [Abliteration & Refusal Evaluation](../concepts/abliteration-and-refusal-eval.md)
- [Container Images & Provenance](./images-and-provenance.md)
