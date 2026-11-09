---
type: workflow
title: Authoring & Changing Recipes
description: How to add or change a recipe in this registry — search upstream first, copy with attribution and minimal changes, apply the image policy, keep one canonical copy, and publish by committing to main and refreshing the registry.
tags: [workflow, authoring, recipes, registry, contribution]
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-b117507d3a6ecf93d700bb10
    resource: repo://notes/minimax-m3-sparkrun-port/PROVENANCE.md
  - id: openwiki-source-036e64f955b6e8c14e4c8d88
    resource: repo://notes/minimax-m3-sparkrun-port/README.md
  - id: openwiki-source-a96b242eacfe664db229043f
    resource: repo://notes/minimax-m3-sparkrun-port/sync-mods.sh
  - id: openwiki-source-67c295973f38e30669ebf01c
    resource: repo://recipes/glm-5.3-flash-exl3-abliterated-tp2.yaml
  - id: openwiki-source-5c02b2143bb9723499b2edf3
    resource: repo://recipes/mods/glm53-exl3-gb10-topk/run.sh
generated: { by: "claude-code", at: "2026-11-08T21:00:19.321Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
---

# Authoring & Changing Recipes

Adding or editing a recipe follows a fixed path: reuse before writing, change as
little as possible, keep provenance, and publish only through the registry's
commit-then-update mechanism.

## 1. Search before writing

Do not start from a blank file. Run `sparkrun registry update`, then
`sparkrun recipe search` **across every registry**. If an upstream recipe for
the model already exists, copy it rather than authoring from scratch — upstream
recipes encode engine flags that are easy to get wrong.

## 2. Copy with attribution, change only what the pair needs

When a copied recipe is the starting point, keep an **attribution header** that
names the upstream source, and change only what this specific cluster requires —
typically the container (per the image policy), the fit knobs
(`gpu_memory_utilization`, `max_model_len`, KV controls), the served name, and
any env workarounds for this hardware. The recipe header should record *why*
each deviation from upstream was made, so a later reader can tell a deliberate
change from an accident. See recipe anatomy for the fields themselves.

The 2026-11-08 pooling recipes are the worked example of adapting when **no
exact upstream exists**: `qwen3-embedding-4b-tp1` and `qwen3-reranker-4b-tp1`
copy the serve shape of the `@official` Qwen3-VL 8B embedding/reranker pair but
substitute the text-only 4B checkpoints (no 4B exists in the VL series), pin
the container from `:latest` to a dated tf5 build already on disk, and say all
of that — plus the then-unverified status — in their `# >>> ADAPTED from …`
headers.

## 3. Apply the image policy

Pick the `container:` by the selection order (spark-arena first), use an
**immutable tag** — a dated tag rather than a digest pin, since the worker
cannot receive digest-pinned images — and prefer an image already on disk.

## 3b. Patch the image with a mod, not a rebuild

When a prebuilt image needs a platform fix (a GB10/SM121 kernel workaround, an
upstream overlay edit the image lacks), add a directory under `recipes/mods/`
with a `run.sh` that applies the edit idempotently inside each rank's
container pre-serve, and list it under the recipe's `mods:` key. Carry upstream
attribution/licensing files in the mod directory when the edit is ported from
another project. See recipe anatomy for the mechanics and the worked
`glm53-exl3-gb10-topk` example.

## 4. Keep one canonical copy

Each served model has exactly one canonical recipe file. A genuinely different
operating profile of the same checkpoint (long-context, coder-agent, EP) is its
own named file; a near-duplicate that only tweaks a value is not. Measured
numbers go in `benchmarks/` and the status row in `INDEX.md`, never duplicated
into the recipe as a second source of truth, and `INDEX.md` row numbers are not
renumbered.

## 5. Verify, then publish

A new or changed recipe is only trustworthy once it clears the **verified** bar
(the model answered a request) — a lint or dry run does not qualify. See the
launch-and-verify workflow for that procedure.

Publishing is the registry mechanism: the change is invisible to sparkrun until
it is **committed to `main`** and `sparkrun registry update spark-forge` has
refreshed the clone. Work goes straight to `main`; there is no pull-request
step. **Commit and push only when the operator asks** — authoring and verifying
a recipe does not imply permission to commit it.

An uncommitted recipe is still usable before it lands: `sparkrun run` takes a
file path directly, and a SparkRoute binding can reference the recipe by
**absolute path** until the commit makes the registry name resolvable (the
embedding/reranker pair ran and was gateway-bound this way on 2026-11-08).

## Staging ground: unverified ports under `notes/`

A recipe that has not cleared verification does not belong in `recipes/` or
`INDEX.md`. The MiniMax-M3 sparkrun port
(`notes/minimax-m3-sparkrun-port/`) is the standing example: an agent-authored
port of tonyd2wild's community lane-A config (428B 4-bit, 36 tok/s on a
direct-cabled pair), preserved with a `PROVENANCE.md` before the source
directory disappeared. It passed `recipe validate` and a two-node `--dry-run`
(serve command byte-equivalent to the verified upstream line) but was **never
booted here** — the image is unbuilt and the 224 GB weights unstaged — so it
stays under `notes/` until a verify pass promotes it. Its README also records
transferable lessons: `scheduler: greedy` to bypass a wrongly-inflated VRAM
admission estimate, explicit `distribution_config` for a drafter sparkrun's
auto-detection misses, and running by file path so locally-sourced mods are
auto-trusted. It also shows the heavyweight end of the `mods:` pattern: the
recipe needs **9 mods**, which are not vendored but staged into a gitignored
`mods/` directory by `sync-mods.sh` from a3refaat's MIT-licensed branch (the
script also applies the required prometheus graceful-skip patch — without it,
mods running under `set -euo pipefail` abort the whole launch on a missed
anchor).

## Related

- [Registry & Publishing Model](../architecture/registry-and-publishing.md)
- [Recipe Anatomy](../concepts/recipe-anatomy.md)
- [Container Images & Provenance](../reference/images-and-provenance.md)
