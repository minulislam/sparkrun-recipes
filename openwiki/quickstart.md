---
type: quickstart
title: Quickstart & Task Routing
description: What the sparkrun-recipes (spark-forge) registry is, the source files that are authoritative, and where to go for each task — launch, verify, benchmark, author, or debug a recipe.
tags: [quickstart, overview, routing, registry]
sources:
  - id: openwiki-source-01cb0b49f3e974bd03fec0b9
    resource: repo://.agents/skills/dgx-spark-skills/SKILL.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-453611660ffbf02a66fa4bf3
    resource: repo://skills-lock.json
generated: { by: "claude-code", at: "2026-11-17T14:41:15.503Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-17T14:41:15.503Z
---

# Quickstart & Task Routing

**sparkrun-recipes** is a recipe and benchmark **registry** (it publishes as the
sparkrun registry **`spark-forge`**), not an application — there is nothing to
build or install. Its product is a set of recipe YAML files that serve
NVFP4-quantized LLMs on a two-node DGX Spark (GB10) pair, plus benchmark reports
whose every number was measured live on that hardware. You consume it through
the `sparkrun` CLI — currently **0.4.2**, installed as a uv tool. (The
"sparkrun 0.3.10" gotchas listed in `CLAUDE.md` are from the earlier pinned
version; their workarounds stand until re-verified on 0.4.x — see the
pitfalls page and `notes/2026-11-03-sparkrun-version-config-audit.md`.)

## Repository layout

- `recipes/<family>/<name>.yaml` — one canonical recipe per served model,
  grouped by model family (`qwen/`, `glm/`, `deepseek/`, `gemma/`, `nemotron/`,
  `minimax/`, `inkling/`, …). The filename stem is the recipe name, so
  `recipes/qwen/qwen3.8-27b-nvfp4-tp1.yaml` is `@spark-forge/qwen3.8-27b-nvfp4-tp1`.
- `recipes/mods/<name>/` — runtime patches, referenced from recipes as
  `../mods/<name>`.
- `images/<name>/` — locally built images and their provenance.
- `benchmarks/` — reports, raw results and driver scripts.
- `.agents/skills/` — vendored NVIDIA agent skills (`dgx-spark-skills`,
  `nemo-rl-session-memory`), pinned by hash in `skills-lock.json` and symlinked
  into each agent's skill directory (`.claude/skills/`, `.roo/skills/`, …).
  They are reference tooling, not recipes.

There is no automated test suite. The pytest files that covered the Inkling
refusal dial were deleted with it on 2026-11-17. A recipe is checked with
`sparkrun recipe validate`, a dry run and a live verification.

Core commands:

```bash
sparkrun recipe validate recipes/<family>/<name>.yaml
sparkrun run ./recipes/<family>/<name>.yaml --cluster <c> --dry-run
sparkrun run ./recipes/<family>/<name>.yaml --cluster <c> --no-follow
sparkrun stop ./recipes/<family>/<name>.yaml --cluster <c>
sparkrun registry update spark-forge        # after the change is on local main
```

## Authoritative source files

The repo root is the source of truth; this wiki explains and connects it but the
files win:

| File | What it holds |
|---|---|
| `INDEX.md` | Every recipe with its status and measured numbers (stable row numbers). |
| `CONTEXT.md` | The status vocabulary (lints / serves / verified / benchmarked / unfit). |
| `MODELS.md` | Which checkpoints are complete/partial/stub on each node. |
| `IMAGE-POLICY.md` | Container image selection order and provenance. |
| `HISTORY.md` | Dated record of all work, standing rules, and open items. |
| `benchmarks/` | Measured reports and raw `results_*` / `mem_*` artifacts. |
| `.claude/skills/verify/SKILL.md` | The procedure that owns the "verified" bar. |

The live cluster is the ultimate source of truth; docs record what was measured
on a date, so re-check before acting. Do not read throughput or context numbers
out of this wiki — it points at `INDEX.md` and `benchmarks/` as the evidence.

## Where to go for each task

- **Understand what the repo is and how it publishes** →
  [Registry & Publishing Model](architecture/registry-and-publishing.md)
- **Understand the hardware and the networking that breaks launches** →
  [Cluster & Networking](architecture/cluster-and-networking.md)
- **Read a recipe file / know what a field does** →
  [Recipe Anatomy](concepts/recipe-anatomy.md)
- **Know what a status word means** →
  [Recipe Status Vocabulary](concepts/status-vocabulary.md)
- **Launch a recipe and prove it serves** →
  [Launching & Verifying a Recipe](workflows/launching-and-verifying.md)
- **Measure a recipe (throughput + full context)** →
  [Benchmarking & Context Verification](workflows/benchmarking.md)
- **Add or change a recipe** →
  [Authoring & Changing Recipes](workflows/authoring-recipes.md)
- **Debug a launch that OOMs, wedges, or won't place** →
  [Memory, Placement & Known Pitfalls](operations/memory-placement-and-pitfalls.md)
- **Route requests to a served model / understand the gateway** →
  [Gateway Routing (spark-loader)](operations/proxy-and-gateway-routing.md)
  — spark-loader on the head's `0.0.0.0:4000` loads `@spark-forge` catalog
  models on demand in front of LiteLLM on `127.0.0.1:4001`; SparkRoute was
  removed on 2026-11-17
- **Pick or vet a container image** →
  [Container Images & Provenance](reference/images-and-provenance.md)
- **Check what's on disk / handle weights safely** →
  [Model Inventory & Weight Safety](reference/model-inventory-and-weights.md)
- **Work with the uncensored models, the refusal dial, or a refusal eval** →
  [Abliteration & Refusal Evaluation](concepts/abliteration-and-refusal-eval.md)
