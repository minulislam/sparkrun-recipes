---
type: quickstart
title: Quickstart & Task Routing
description: What the sparkrun-recipes (spark-forge) registry is, the source files that are authoritative, and where to go for each task — launch, verify, benchmark, author, or debug a recipe.
tags: [quickstart, overview, routing, registry]
sources:
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "claude-code", at: "2026-11-08T21:00:19.321Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-09T21:00:11.445Z
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
- **Route requests to a served model / manage gateway bindings** →
  [Proxy & Gateway Routing (SparkRoute)](operations/proxy-and-gateway-routing.md)
  — the active gateway is the SparkRoute plugin 0.3.4 on the head node's
  loopback port 4000
- **Pick or vet a container image** →
  [Container Images & Provenance](reference/images-and-provenance.md)
- **Check what's on disk / handle weights safely** →
  [Model Inventory & Weight Safety](reference/model-inventory-and-weights.md)
- **Work with the uncensored models / run a refusal eval** →
  [Abliteration & Refusal Evaluation](concepts/abliteration-and-refusal-eval.md)
