---
type: architecture
title: Registry & Publishing Model
description: How sparkrun-recipes operates as the spark-forge sparkrun registry — the git-clone-of-main publishing model, the commit-then-update visibility rule, consumption by @registry/name, and the one-canonical-copy discipline.
tags: [registry, sparkrun, publishing, workflow, git]
sources:
  - id: openwiki-source-048793832532c9756376e4df
    resource: repo://.sparkrun/registry.yaml
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
  - id: openwiki-source-036e64f955b6e8c14e4c8d88
    resource: repo://notes/minimax-m3-sparkrun-port/README.md
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "claude-code", at: "2026-11-17T14:41:15.503Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-17T14:41:15.503Z
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

`~/.config/sparkrun/registries.yaml` defines `spark-forge` as
`file:///home/devops/workspace/sparkrun-recipes` with subpath `recipes`, and
sparkrun keeps a clone of the repo's local `main` branch at
`~/.cache/sparkrun/registries/spark-forge`. The working tree is often on
`develop`, so check `git branch --show-current` before committing: a commit on
`develop` is invisible to sparkrun. Two consequences define the entire
publishing workflow:

1. **A recipe change is invisible to sparkrun until it is on `main`.** Editing a
   file in the working tree, or on any other branch, changes nothing that
   sparkrun can see.
2. **After committing to `main`, the clone must be refreshed** with
   `sparkrun registry update spark-forge`. Only then does `sparkrun run
   @spark-forge/<recipe>` pick up the change.

Work goes **straight to `main`** — there is no pull-request step in this repo's
workflow. (Committing and pushing is still done only when the operator asks.)
Because the registry clones the *local* `main` over `file://`, a commit that
reaches `main` only on the remote is also invisible: after pushing, fast-forward
the local `main` too, then run `sparkrun registry update spark-forge`.

## Family layout and mods

Since the 2026-11-17 reorg, recipes live at `recipes/<family>/<name>.yaml`
(`deepseek/`, `gemma/`, `glm/`, `qwen/`, `nemotron/`, `minimax/`, `inkling/`,
and one folder per single-recipe family). sparkrun names a recipe after its
filename stem, not its folder, so `@spark-forge/<name>` lookups and gateway
catalog entries kept working through the move. Two rules follow: stems must
stay unique across families, and no file may be renamed to a generic
`recipe.yaml`.

Shared runtime patches stay in `recipes/mods/`, which the in-repo
`.sparkrun/registry.yaml` declares as `mods_subpath`. sparkrun resolves a mod
relative to the recipe file, so recipes reference them as `../mods/<name>`. The
reorg briefly broke bare `mods/<name>` references (the dry run reported "Could
not resolve mod" or fell through to the eugr fallback) until they were rewritten.

## Consuming recipes

A recipe can be run two ways:

- **By local file**, straight from the working tree, which does not require the
  registry to be updated:
  `sparkrun run ./recipes/<family>/<name>.yaml --cluster dgx-pair --tp 1 --no-follow`
- **By registry name**, after the clone is refreshed:
  `sparkrun registry update spark-forge` then
  `sparkrun run @spark-forge/<name>`

The local-file path is how a change is verified before it is committed; the
registry-name path is how the published recipe is consumed afterward.

Gateway configuration always names the **registry copy**. spark-loader's catalog
(`~/.config/spark-loader/catalog.yaml`, outside this repo) lists models as
`@spark-forge/<name>`, so a recipe is servable through the gateway only once it
is on `main` and the clone is refreshed. The earlier SparkRoute bindings in
`proxy.yaml` followed the same qualified-name rule, because a plain name matched
both the local checkout and the registry. Those bindings were removed with
SparkRoute on 2026-11-17, and `proxy.yaml` now holds only aliases and proxy
settings.

Trust follows the source: a **locally-sourced recipe is auto-trusted**, so its
mods (injected as `pre_exec` hooks) run without a per-launch confirmation
prompt. The same recipe installed into an *untrusted* registry prompts on every
launch — `sparkrun registry trust <name>` removes the prompt if discoverability
by name is wanted.

## The registry landscape on this host

As of the 2026-11-03 audit (sparkrun 0.4.2), **10 registries** are configured:
official, experimental, community, eugr, atlas, sparkrun-transitional,
`spark-forge` (this repo, `file:///home/devops/workspace/sparkrun-recipes`,
trusted), plus three **untrusted** ones — sparkrun-testing, coldsnap
(plugin-provided), and coldsnap-vanilla. Roughly 118 recipes are visible across
the enabled registries. Untrusted registries are fine for search, but recipes
from them warrant review before launch.

## One canonical copy per recipe

Each served model has exactly **one** canonical recipe file under `recipes/<family>/`.
Variants that differ only in a tuning parameter are still expressed as their own
named files (for example a long-context profile or a coder-agent profile of the
same checkpoint), but there is never more than one file claiming to be the same
recipe. Benchmark reports and measured numbers do not live in the recipe files;
they live under `benchmarks/`, and the per-recipe status/measurements are indexed
in `INDEX.md` (whose row numbers are stable and must not be renumbered).

## Related

- [Recipe Anatomy](../concepts/recipe-anatomy.md)
- [Authoring & Changing Recipes](../workflows/authoring-recipes.md)
- [Gateway Routing (spark-loader)](../operations/proxy-and-gateway-routing.md)
