---
type: workflow
title: Authoring & Changing Recipes
description: How to add or change a recipe in this registry — search upstream first, copy with attribution and minimal changes, apply the image policy, keep one canonical copy, and publish by committing to main and refreshing the registry.
tags: [workflow, authoring, recipes, registry, contribution]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
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

## 3. Apply the image policy

Pick the `container:` by the selection order (spark-arena first), use an
**immutable tag** — a dated tag rather than a digest pin, since the worker
cannot receive digest-pinned images — and prefer an image already on disk.

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

## Related

- [Registry & Publishing Model](../architecture/registry-and-publishing.md)
- [Recipe Anatomy](../concepts/recipe-anatomy.md)
- [Container Images & Provenance](../reference/images-and-provenance.md)
