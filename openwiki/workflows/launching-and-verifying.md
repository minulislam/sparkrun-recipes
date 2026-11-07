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
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
generated: { by: "claude-code", at: "2026-11-05T21:00:18.164Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-06T21:00:17.440Z
---

# Launching & Verifying a Recipe

Getting a recipe from a file to **verified** is a fixed sequence. The bar at the
end is specific: a recipe is verified only when the **model answers a request** —
`sparkrun recipe validate` and `--dry-run` are lint, not verification. Load the
`sparkrun:run` skill before using the CLI, and always launch with `--no-follow`.

## Launch sequence

1. **Lint** — `sparkrun recipe validate recipes/<name>.yaml`. Cheap; proves only
   that the file is well-formed.
2. **Dry-run the fit** — `sparkrun run ./recipes/<name>.yaml --dry-run`. Shows
   the per-host VRAM estimate so you catch a model that will not fit before
   spending a boot.
3. **Run** — `sparkrun run ./recipes/<name>.yaml --no-follow`.

`--no-follow` is mandatory for scripted launches: `sparkrun run` returns as soon
as the containers are up, long before vLLM actually serves, so following logs
only blocks. For a local file you launch the file directly; for a published
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

## Related

- [Recipe Status Vocabulary](../concepts/status-vocabulary.md)
- [Benchmarking & Context Verification](./benchmarking.md)
- [Proxy & Gateway Routing (SparkRoute)](../operations/proxy-and-gateway-routing.md) — how requests reach the served model after launch
- [Cluster & Networking](../architecture/cluster-and-networking.md)
