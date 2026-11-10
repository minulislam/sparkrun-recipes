---
type: reference
title: Model Inventory & Weight Safety
description: What MODELS.md records about which checkpoints are complete, partial, or stubs on each node and which recipes use them, and the standing rules for handling weights safely (back up before delete, deletion is the operator's call, never hf cache prune without --dry-run).
tags: [models, weights, inventory, storage, safety]
sources:
  - id: openwiki-source-d844af9966f902d563fa3f52
    resource: repo://benchmarks/MIAAI-LAB-VALIDATION-RESULTS-2026-10-16.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-456fceaa0ae7a8e901be70bf
    resource: repo://MODELS.md
generated: { by: "claude-code", at: "2026-11-09T21:00:11.445Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-09T21:00:11.445Z
---

# Model Inventory & Weight Safety

A recipe only serves if its checkpoint is actually present and complete on the
nodes it launches on. `MODELS.md` is the inventory of record for that, and a
small set of rules governs the weights because they are expensive to replace.

## The inventory (`MODELS.md`)

`MODELS.md` records, per node, which checkpoints are on disk, how large they
are, and which recipe(s) use them. It is a **point-in-time measurement** — each
pass is dated (the current tables were measured on both nodes 2026-10-13, with
an evening addendum of same-day changes that were *not* re-measured) — so it is
read as "what was true on that date", and the live cluster is re-checked before
acting on it.

The inventory classifies each repo precisely, which is why it is trustworthy:

- **Complete** — every shard named in the weight index is present and the
  on-disk bytes match the index's `metadata.total_size`.
- **Partial** — some but not all shards present (may or may not be resumable
  depending on whether the source still exists).
- **Stub** — a config-only HuggingFace repo with no weight files at all.

A subtlety the inventory flags: hardlinked blob stores mean a plain `du` can
under-report a complete checkpoint's size, so completeness is judged against the
weight index, not a byte count. The inventory also notes shared/hardlinked
variant copies (for example a `config.json`-patched copy of a checkpoint for a
planned recipe) that occupy no extra space.

Because `MODELS.md` lags the live cluster, newer arrivals are recorded in
`HISTORY.md` first: on 2026-11-08 `Qwen/Qwen3-Embedding-4B` and
`Qwen/Qwen3-Reranker-4B` (7.5 GiB each) were downloaded to **both** nodes for
the new pooling recipes (rows 65–66). On 2026-11-09 the embedding checkpoint was
copied to `gx10-spark` over CX7, and `MODELS.md` now lists it on both nodes. Their
pinned container (`dgx-vllm-eugr-nightly-tf5:2026092702`, 24.8 GB) was streamed
to the worker the same day.

## Weight-safety rules

Weights are hard to replace, so handling them is deliberately conservative:

- **Check `MODELS.md` before launching** — confirm the checkpoint is complete on
  the target node(s) first.
- **Back up before deleting.** A checkpoint is backed up to
  `/mnt/nas/ai-models/model-backup/huggingface-hub/` before it is removed. (The history records a
  violation of this rule — a delete done while `/mnt/nas` was unmounted, so no
  backup was taken — as a cautionary case, which is exactly why the rule is
  explicit.)
- **Deletion is the operator's call**, not something automation decides.
- **Never run `hf cache prune` without `--dry-run`** first.

Whether a deleted checkpoint is recoverable depends on the source: some live
upstream and can be re-downloaded, while a partial whose source repo has since
disappeared is gone for good — another reason the inventory tracks source
availability alongside completeness.

## Preserved external validation record

`benchmarks/MIAAI-LAB-VALIDATION-RESULTS-2026-10-16.md` preserves the MiaAI-Lab
abliterated-recipe validation report (3 PASS serve-only, 4 blocked/gated, with
per-recipe patches and checkpoint cache status on both nodes). It was copied
into this repo before the external `miaai-runner` repo was deleted, so it is
now the only surviving copy of that evidence — including which drowzeys/keys
checkpoints were HF-gated (HTTP 403) at the time. The GLM-5.3-Flash EXL3
abliterated recipe adopted into this registry (row 64) traces back to that set.

## Related

- [Abliteration & Refusal Evaluation](../concepts/abliteration-and-refusal-eval.md)
- [Container Images & Provenance](./images-and-provenance.md)
