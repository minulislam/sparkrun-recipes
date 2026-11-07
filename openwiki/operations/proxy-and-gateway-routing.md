---
type: operations
title: Proxy & Gateway Routing (SparkRoute)
description: How the SparkRoute gateway on the head node's port 4000 routes model requests — proxy.yaml as the single source of bindings, the sync-based workflow, the binding schema, cold_start and placement policy, the unauthenticated admin API, and the operator-route vs recipe-binding name conflict.
tags: [proxy, gateway, sparkroute, routing, operations, bindings]
sources:
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
generated: { by: "claude-code", at: "2026-11-05T21:00:18.164Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-06T21:00:17.440Z
---

# Proxy & Gateway Routing (SparkRoute)

Requests reach served models through a gateway on the head node. The active
gateway is the **SparkRoute** plugin (0.3.4, external, git-sourced), selected
via the `gateway.sparkroute` feature; LiteLLM remains sparkrun's upstream
default but is not what runs here. The proxy listens on **0.0.0.0:4000** — any
interface on the head, not just localhost — which the 2026-11-03 audit flags as
an exposure decision the operator should make deliberately.

## Bindings live only in `proxy.yaml`

There is **no CLI command to add or remove a binding**. The single source of
truth is `~/.config/sparkrun/proxy.yaml`; `sparkrun proxy sync` makes the
running gateway match the file **atomically**. The workflow is always:
edit `proxy.yaml`, then `sparkrun proxy sync`.

Recipe references in bindings must use the **qualified** form
`@spark-forge/<recipe>`. Plain recipe names are ambiguous — the local checkout
and the `spark-forge` registry both match — and the resolver demands an exact
recipe.

Companion file `proxy.env` holds secrets (HF/NGC/NVIDIA/Ollama API keys, mode
600). Never print its contents into output or files.

## Binding schema

Upstream docs omit the binding schema; the **installed plugin source** at
`~/.config/sparkrun/plugins/sparkroute/*/payload/` is authoritative. The fields
are:

- `recipe` — qualified recipe reference
- `cluster` or `cluster_candidates` — placement target(s)
- `cold_start` — `wait` or `reject`
- `model` — public model name exposed by the gateway
- `overrides`, `capabilities`

## Cold start and placement policy

- **`cold_start: wait`** is used on all bindings here: a request for a model
  that is not currently serving **queues through the multi-minute model swap**
  instead of erroring. `reject` would fail fast instead.
- **Idle-node-first** placement is encoded by `cluster_candidates` **order**
  (e.g. a TP1 recipe listing `gb10-solo` then `gx10-solo`). SparkRoute 0.3.4
  has no preempt-on-demand; eviction happens only via gateway idle timers on
  gateway-owned jobs.

## Admin API and operator routes

The gateway exposes an admin API on port 4000 with **no authentication** (and
the proxy is bound to 0.0.0.0, so treat it as LAN-reachable):

- `GET`/`PUT /v1/config/managed-sets/operator` — read/replace operator routes
- a validate endpoint
- compare-and-swap updates via `expected_active_revision`

Operator (static) routes and sparkrun recipe bindings share one namespace:
**strict validation rejects a sparkrun binding whose public name an operator
route already owns**. On 2026-11-03 three stale operator virtual models were
removed via an admin-API CAS replace for exactly this reason (backup kept at
`~/.config/sparkrun/sparkroute/operator-set-backup-2026-11-03.json`);
`qwen38-27b` and `qwen38-27b:low` were kept as operator routes.

## Routes are not backends

The proxy advertises model routes regardless of whether anything is serving.
The 2026-11-03 audit caught the proxy exposing 5 routes while **both hosts were
idle with no sparkrun containers** — requests to such routes fail (or, with
`cold_start: wait`, block) until a workload launches. Autodiscovery sweeps the
`dgx-pair` cluster every 30 s to pick up live backends, and a discovered model
name can collide with a reserved operator route of the same name (observed with
`qwen38-27b`).

## Related

- [Cluster & Networking](../architecture/cluster-and-networking.md)
- [Launching & Verifying a Recipe](../workflows/launching-and-verifying.md)
