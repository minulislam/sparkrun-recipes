---
type: architecture
title: Registry & Publishing Model
description: How sparkrun-recipes operates as the spark-forge sparkrun registry — the git-clone-of-main publishing model, the commit-then-update visibility rule, consumption by @registry/name, and the one-canonical-copy discipline.
tags: [registry, sparkrun, publishing, workflow, git]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
---

# Registry & Publishing Model

This repository is a **registry**, not an application. There is nothing to build
or install; its product is a set of recipe YAML files and benchmark reports that
are consumed through the `sparkrun` CLI. It publishes under the registry name
**`spark-forge`**.

## Repo name vs. registry name

The git repository is `minulislam/sparkrun-recipes`; the sparkrun registry it
publishes is `spark-forge`. The mismatch is **deliberate** — do not try to
"correct" one to match the other.

## The registry is a git clone of `main`

The `spark-forge` registry that sparkrun reads is a local git clone of this
repo's `main` branch. Two consequences define the entire publishing workflow:

1. **A recipe change is invisible to sparkrun until it is on `main`.** Editing a
   file in the working tree, or on any other branch, changes nothing that
   sparkrun can see.
2. **After committing to `main`, the clone must be refreshed** with
   `sparkrun registry update spark-forge`. Only then does `sparkrun run
   @spark-forge/<recipe>` pick up the change.

Work goes **straight to `main`** — there is no pull-request step in this repo's
workflow. (Committing and pushing is still done only when the operator asks.)

## Consuming recipes

A recipe can be run two ways:

- **By local file**, straight from the working tree, which does not require the
  registry to be updated:
  `sparkrun run ./recipes/<name>.yaml --cluster dgx-pair --tp 1 --no-follow`
- **By registry name**, after the clone is refreshed:
  `sparkrun registry update spark-forge` then
  `sparkrun run @spark-forge/<name>`

The local-file path is how a change is verified before it is committed; the
registry-name path is how the published recipe is consumed afterward.

## One canonical copy per recipe

Each served model has exactly **one** canonical recipe file in `recipes/`.
Variants that differ only in a tuning parameter are still expressed as their own
named files (for example a long-context profile or a coder-agent profile of the
same checkpoint), but there is never more than one file claiming to be the same
recipe. Benchmark reports and measured numbers do not live in the recipe files;
they live under `benchmarks/`, and the per-recipe status/measurements are indexed
in `INDEX.md` (whose row numbers are stable and must not be renumbered).

## Related

- [Recipe Anatomy](../concepts/recipe-anatomy.md)
- [Authoring & Changing Recipes](../workflows/authoring-recipes.md)
