---
type: workflow
title: Launching & Verifying a Recipe
description: The launch-to-verified path — lint, dry-run fit check, run with --no-follow, inline HF_TOKEN for gated repos, poll readiness against the in-container serve log, and clear the verified bar by making the model answer a request.
tags: [workflow, launch, verify, sparkrun, readiness]
sources:
  - id: openwiki-source-4f8c5f213160a2befb6f5465
    resource: repo://.claude/skills/verify/SKILL.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-39c3295efc089133e87a9c80
    resource: repo://CONTEXT.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
generated: { by: "claude-code", at: "2026-11-17T14:41:15.503Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-17T14:41:15.503Z
---

# Launching & Verifying a Recipe

Getting a recipe from a file to **verified** is a fixed sequence. The bar at the
end is specific: a recipe is verified only when the **model answers a request** —
`sparkrun recipe validate` and `--dry-run` are lint, not verification. Load the
`sparkrun:run` skill before using the CLI, and always launch with `--no-follow`.

## Launch sequence

1. **Lint** — `sparkrun recipe validate recipes/<family>/<name>.yaml`. Cheap; proves only
   that the file is well-formed.
2. **Dry-run the fit** — `sparkrun run ./recipes/<family>/<name>.yaml --dry-run`. Shows
   the per-host VRAM estimate so you catch a model that will not fit before
   spending a boot.
3. **Run** — `sparkrun run ./recipes/<family>/<name>.yaml --no-follow`.

`--no-follow` is required for launches (`CLAUDE.md`); readiness is then checked
separately through the serve log and the endpoint, not by following the launch
output. For a local file you launch the file directly; for a published
recipe you launch `@spark-forge/<name>` after a registry update. The installed
CLI is sparkrun **0.4.2** (uv tool).

**Mgmt-link-down fallback:** when the worker's management link is unusable,
two-node launches have been done over the CX7 addresses directly —
`--hosts 10.99.10.10,10.99.10.11` plus `HF_HUB_OFFLINE=1` — instead of
`--cluster dgx-pair`. This works because only rendezvous/bootstrap traffic
rides the management path; NCCL data is on the CX7 fabric either way. It is a
fallback, not the committed configuration.

## HF_TOKEN for gated repos

A gated checkpoint needs `HF_TOKEN`, but **non-interactive shells do not get it**
— `~/.bashrc` returns early for them, so the export never runs. Pass it inline on
the launch command for any gated repo. Never print the token into output or
files.

## Poll readiness against the in-container serve log

Because `run` returns before the endpoint is live, poll two things together: the
HTTP socket (`/v1/models` returning 200) and the in-container serve log. The
vLLM output is **not** in `docker logs` — it is at `/tmp/sparkrun_serve.log`
*inside* the container, reached with `docker exec <container> tail
/tmp/sparkrun_serve.log`. Budget real time here: on a large MoE, image sync,
container start, weight load, and CUDA-graph/speculative-decode capture can add
up to roughly 25 minutes from launch to first token.

## Clearing the verified bar

Once the endpoint serves, send a real request and confirm the model answers
coherently. Only that clears **verified** — serving is necessary but not
sufficient, because a recipe can serve and still return garbage (which is the
`unfit` outcome). After a worker reboot, run
`sparkrun setup check --cluster dgx-pair` before a two-node launch. From here, a
verified recipe can go on to be benchmarked.

A launch does not have to be driven by `sparkrun run` directly. The
spark-loader gateway on `:4000` loads a catalog model (`@spark-forge/<name>`)
on demand when a request names it and the model is not running, so a request
through the gateway can also trigger a boot. An answer obtained that way clears
the verified bar the same as a direct one, as long as the access path is recorded
alongside the status (see status vocabulary). Only published recipes are in
that catalog. A working-tree change has to be launched by file path. Under the
earlier SparkRoute gateway, a `cold_start: wait` binding did the same: a
2026-11-08 request to the cold `glm-5.3-flash-abliterated` binding returned 200
after **584 s (~9.7 min)**.

## Verifying pooling runners (embedding / rerank)

Pooling-runner recipes break two assumptions above:

- **sparkrun's readiness probe never turns green** for them — it expects a chat
  token the pooling endpoint will never send. Ignore the probe and verify
  against the pooling endpoint itself.
- The "real request" is not a chat completion. The embedding recipe was
  verified **through the gateway** (`/v1/embeddings` → 200 with a 2560-dim
  vector, 1.7 s warm); the reranker had to be verified **direct against the
  container's `/v1/rerank`** because SparkRoute 0.3.4 has no rerank route (the
  gateway 404s it). Today neither runs as a sparkrun workload: the embedder
  (`:8000`) and reranker (`:8001`) are the `spark-pinned` docker compose stack
  on gb10. Re-verify them by calling those ports directly.

## Related

- [Recipe Status Vocabulary](../concepts/status-vocabulary.md)
- [Benchmarking & Context Verification](./benchmarking.md)
- [Gateway Routing (spark-loader)](../operations/proxy-and-gateway-routing.md) — how requests reach the served model after launch
- [Cluster & Networking](../architecture/cluster-and-networking.md)
