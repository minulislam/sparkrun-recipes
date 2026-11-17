---
type: operations
title: Gateway Routing (spark-loader)
description: How requests reach served models on the head node — spark-loader on :4000 loads catalog recipes on demand and forwards to LiteLLM on 127.0.0.1:4001; the embedder and reranker run outside sparkrun; SparkRoute was removed on 2026-11-17.
tags: [proxy, gateway, spark-loader, litellm, routing, operations, sparkroute]
sources:
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
generated: { by: "claude-code", at: "2026-11-17T14:41:15.503Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-17T14:41:15.503Z
---

# Gateway Routing (spark-loader)

Requests reach served models through a two-layer gateway on the head node
(`gb10-spark`). Since **2026-11-17** the front door is **spark-loader**. The
SparkRoute plugin that used to own port 4000 has been removed, along with its
bindings.

```
client ──► spark-loader  0.0.0.0:4000   (spark-loader.service, user unit)
              │  catalog: ~/.config/spark-loader/catalog.yaml
              │  loads missing catalog models via the sparkrun daemon
              ▼
           LiteLLM       127.0.0.1:4001 (sparkrun-proxy.service)
              │  model list from sparkrun discovery
              ▼
           running sparkrun workloads (dgx-pair / gb10-solo / gx10-solo)
```

## spark-loader: on-demand loading in front of LiteLLM

spark-loader is a separate project (`~/workspace/llm/serving/spark-loader`), not
part of this repo. It runs as the user unit `spark-loader.service` and listens
on **`0.0.0.0:4000`**, which is every interface on the head. Treat it as
reachable from the LAN.

- **Catalog.** `~/.config/spark-loader/catalog.yaml` lists the models it may
  load, each named by a qualified registry recipe, `@spark-forge/<name>`. A
  recipe is therefore loadable through the gateway only after it is on `main` and
  `sparkrun registry update spark-forge` has run (see the registry page).
- **On-demand load.** A request for a catalog model that is not running is
  loaded through the sparkrun daemon.
- **Default fallback.** A request for a model that is neither running nor
  in the catalog falls back to `default`, which spark-loader resolves to the
  **largest running chat model**.
- **Idle stop.** Models spark-loader started are stopped after about 30 minutes
  idle.

Behind it, **LiteLLM** runs as `sparkrun-proxy.service` on `127.0.0.1:4001`,
loopback only. Its model list comes from sparkrun's own discovery of running
workloads. `~/.config/sparkrun/proxy.yaml` now holds only aliases and proxy
settings; there are no bindings left in it.

### Operating the LiteLLM layer

While `sparkrun-proxy.service` is up, `sparkrun proxy start` and `alias add` can
fail with `ResourceBusy`. Edit `proxy.yaml` and run `sparkrun proxy sync`, or
restart the unit with `sudo -n systemctl restart sparkrun-proxy.service`. That
restart is the one root command allowed without a password.

The companion file `proxy.env` holds secrets (HF/NGC/NVIDIA/Ollama API keys,
mode 600), according to the 2026-11-03 audit. Never print secrets into output
or files.

## Embeddings and reranking bypass the gateway path

The embedder (`:8000`) and reranker (`:8001`) are **not** sparkrun workloads.
They run as the `spark-pinned` docker compose stack on `gb10-spark`, because
sparkrun 0.4.2 reserves a whole GPU per workload. Callers reach them on those
ports directly. Their recipes (`recipes/qwen/qwen3-embedding-4b-tp1.yaml`,
`recipes/qwen/qwen3-reranker-4b-tp1.yaml`) remain the record of the verified
serve shape. The memory page covers how this stack interacts with large
launches on the head.

## History: SparkRoute (removed 2026-11-17)

From early November until 2026-11-17, port 4000 was the SparkRoute plugin
(0.3.4). Its model was different. Each served model was a **binding** in
`proxy.yaml` (`recipe: '@spark-forge/<name>'`, `cluster` or
`cluster_candidates`, `cold_start: wait`), and changes were applied with
`sparkrun proxy sync`. Several lessons from that era are recorded in
`HISTORY.md` and `INDEX.md`:

- Bindings had to name recipes as `@spark-forge/<name>`, because a plain name
  matched both the working tree and the registry. spark-loader's catalog keeps
  the same convention.
- `cold_start: wait` held a request open through a full cold boot. In a
  2026-11-08 test, a request returned 200 after 584 s.
- SparkRoute had no rerank route, and its embedding activation wait was shorter
  than a cold boot. The embedding recipe still carries the
  `sparkroute: {capabilities: [single_vector_embedding]}` block that SparkRoute
  required. That block is now vestigial.
- The 2026-11-03 audit flagged the `0.0.0.0:4000` bind. SparkRoute was briefly
  rebound to loopback on 2026-11-07. spark-loader is again bound to all
  interfaces.

Do not try to manage spark-loader through SparkRoute commands or the old admin
API (`/v1/config/managed-sets/operator`). Those no longer exist on this host.

## Related

- [Registry & Publishing](../architecture/registry-and-publishing.md)
- [Memory, Placement & Known Pitfalls](../operations/memory-placement-and-pitfalls.md)
- [Cluster & Networking](../architecture/cluster-and-networking.md)
