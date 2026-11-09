---
type: operations
title: Proxy & Gateway Routing (SparkRoute)
description: How the SparkRoute gateway on the head node's port 4000 routes model requests — proxy.yaml as the single source of bindings, the sync-based workflow, the binding schema, proven cold_start behavior, the current 9-route model list, embedding/rerank limitations, the unauthenticated admin API, and the operator-route vs recipe-binding name conflict.
tags: [proxy, gateway, sparkroute, routing, operations, bindings]
sources:
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
generated: { by: "claude-code", at: "2026-11-07T21:00:21.382Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
---

# Proxy & Gateway Routing (SparkRoute)

Requests reach served models through a gateway on the head node. The active
gateway is the **SparkRoute** plugin (0.3.4, external, git-sourced), selected
via the `gateway.sparkroute` feature; LiteLLM remains sparkrun's upstream
default but is not what runs here. The proxy originally listened on
**0.0.0.0:4000** — any interface on the head — which the 2026-11-03 audit
flagged as an exposure risk; on 2026-11-07 it was restarted bound to
**127.0.0.1:4000** (loopback only).

## Bindings live only in `proxy.yaml`

There is **no CLI command to add or remove a binding**. The single source of
truth is `~/.config/sparkrun/proxy.yaml`; `sparkrun proxy sync` makes the
running gateway match the file **atomically**. The workflow is always:
edit `proxy.yaml`, then `sparkrun proxy sync`.

Recipe references in bindings must use the **qualified** form
`@spark-forge/<recipe>`. Plain recipe names are ambiguous — the local checkout
and the `spark-forge` registry both match — and the resolver demands an exact
recipe. A recipe not yet committed to `main` (invisible to the registry) can be
bound by **absolute file path** until it lands — the 2026-11-08
embedding/reranker recipes were bound this way.

Beware: **`sparkrun proxy unload` deletes the recipe's binding from
`proxy.yaml`**, not just the running deployment. After using it, restore the
binding by hand and re-sync.

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
  instead of erroring. `reject` would fail fast instead. This is **proven in
  practice**: a 2026-11-08 test request to the cold GLM-5.3-flash-abliterated
  binding held the HTTP connection through the entire boot and returned 200
  with the expected completion after **584 s (~9.7 min)**.
- **Idle-node-first** placement is encoded by `cluster_candidates` **order**
  (e.g. a TP1 recipe listing `gb10-solo` then `gx10-solo`). SparkRoute 0.3.4
  has no preempt-on-demand; eviction happens only via gateway idle timers on
  gateway-owned jobs.

## The current model list (2026-11-08: 9 routes)

The binding list was rebuilt on 2026-11-07 ("pick models carefully"): the
gateway had been left with **zero routable models** because console edits had
put all five sparkrun deployments into the operator set's
`excluded_deployments`. The exclusions were cleared via an admin-API CAS
replace (backup at
`~/.config/sparkrun/sparkroute/operator-set-backup-2026-11-07.json`) and the
list was re-picked to five VERIFIED recipes; on 2026-11-08 four more bindings
were added, bringing the gateway to **9 routes**:

| Route | Recipe (INDEX row) | Role |
|---|---|---|
| `qwen3.8-flash-next-abliterated` | row 59, dgx-pair | primary general chat |
| `glm-5.3-flash-abliterated` | row 62, dgx-pair | GLM lane — one long request at a time |
| `deepseek-v4-coder` | row 47, dgx-pair | coding agents |
| `deepseek-v4-flash-vision-uncensored` | row 43, dgx-pair | 1M context + vision |
| `Qwen/Qwen3.8-27B-FP8` | `qwen3.8-27b-fp8-mtp-tp1`, gb10-solo | head-only weights |
| `qwen36-35b-a3b` | heretic NVFP4, both solos | only complete-weights 35B-A3B MoE |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` | row 54, gb10-solo → gx10-solo | fast interactive lane |
| `Qwen/Qwen3-Embedding-4B` | row 65, new | RAG/agent-memory embeddings |
| `Qwen/Qwen3-Reranker-4B` | row 66, new | reranking (direct endpoint only — see below) |

## Embedding and rerank: what the gateway can and cannot route

- An embedding binding only routes if its recipe declares
  `sparkroute: {capabilities: [single_vector_embedding]}` (see recipe anatomy).
  Embedding through the gateway is VERIFIED (2560-dim vector, 1.7 s warm).
- The gateway's **embedding activation wait (~160 s) is shorter than the
  ~3–4 min cold boot**, so the first cold embedding request returns a 503
  (`activation_failed`) while the launch continues; a retry succeeds.
- **SparkRoute 0.3.4 has no `/v1/rerank` (score) route** — confirmed in the
  plugin source. The gateway 404s rerank calls even though the binding lists
  and cold-starts the model; callers (e.g. RAGFlow) must hit the serving
  container's endpoint directly. Reranking was verified direct on the node
  (test pair scored 0.726 vs 0.684).

## Admin API and operator routes

The gateway exposes an admin API on port 4000 with **no authentication**
(mitigated since 2026-11-07 by the 127.0.0.1 bind, but anything on the head
node can still drive it):

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
- [Recipe Anatomy](../concepts/recipe-anatomy.md)
