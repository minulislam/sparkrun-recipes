---
type: architecture
title: Cluster & Networking
description: The dgx-pair two-node DGX Spark topology, the load-bearing NCCL/Gloo comm pins, the intentional ConnectX-7 duplicate-IP layout, and the separation of the management plane from the CX7 data plane.
tags: [cluster, networking, dgx-spark, nccl, connectx-7, topology]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
---

# Cluster & Networking

Every recipe in this registry is launched and measured against one physical
target: a two-node **DGX Spark (GB10)** pair. Understanding its topology — and
the handful of networking facts that will silently break a two-node launch if
ignored — is a prerequisite for the launch, verify, and benchmark workflows.

## The `dgx-pair` cluster

`dgx-pair` is the sparkrun **default** cluster and the one every two-node recipe
targets. It has two members, both GB10 with ~121 GiB unified memory:

| Role | Hostname | Management IP | Endpoint |
|---|---|---|---|
| Head | `gb10-spark` | `10.10.20.10` | `http://10.10.20.10:8000/v1` |
| Worker | `gx10-spark` | `10.10.20.11` | — |

Three sibling clusters exist alongside it: `dgx-pair-ep` (for expert-parallel
recipes), `gb10-solo`, and `gx10-solo`. There is **no** cluster literally named
`default` — that is a common mistake; the default *is* `dgx-pair`. Single-node
launches use `--tp 1` (`--solo` is deprecated).

## Two-node communication pins live in the cluster, not the recipe

Multi-node tensor parallelism needs NCCL, Gloo, and the TCP store all bound to
the correct high-speed interfaces. Those bindings are pinned in the **cluster
definition** — `~/.config/sparkrun/clusters/dgx-pair.yaml` under its `env:`
block — and are deliberately kept out of individual recipes. The pinned set is
`NCCL_IB_HCA`, `NCCL_SOCKET_IFNAME`, `GLOO_SOCKET_IFNAME`, and
`TP_SOCKET_IFNAME`, all targeting the ConnectX-7 `f1` ports.

These pins are **load-bearing**: a recipe that redefines them trips the
`managed-comm-env` validator warning, and moving them into recipes is explicitly
disallowed. Cluster-level env also overrides sparkrun's live interface probe,
which is why the pins must live there.

## The ConnectX-7 duplicate-IP layout is intentional

Each ConnectX-7 NIC exposes two ports, `f0` and `f1`. Since 2026-09-29 each
`f0` port carries the **same IPv4 as its `f1` twin**, at a higher (worse) route
metric. This is deliberate and user-confirmed — it is not a misconfiguration to
"fix". sparkrun's live probe (through at least 0.3.10) lists the `f0` ports
first and would hand them to both the NCCL and the Gloo/TCPStore socket groups,
so the comm pins above point at the `f1` ports to override that.

Two consequences follow:

- **Never run `sparkrun setup cx7` or the setup wizard on `dgx-pair`.** Either
  can rewrite the duplicate-IP layout and drop the load-bearing pins.
- **After a worker reboot, run `sparkrun setup check --cluster dgx-pair`**
  before attempting a two-node launch, to confirm the fabric came back up
  correctly.

## Management plane vs. CX7 data plane

The two networks are separate and fail independently:

- **CX7 data plane** — the `10.99.x` RoCE fabric (200 Gb/s) that carries all
  tensor-parallel all-reduce traffic between ranks. This is what inference
  performance depends on.
- **Management plane** — the worker's wired NIC `enP7s7` holds the management
  address `10.10.20.11`, which sparkrun uses for orchestration and SSH.

The management NIC has proven unstable: `enP7s7` has repeatedly logged link-down
and at one point reached a hard **NO-CARRIER** state (a physical cable/switch
problem, not a host crash — the worker stayed up for days). Because the data
plane can be healthy while management is down, a two-node job can wedge even
though the CX7 fabric is fine.

A **temporary, non-persistent** workaround has been used to restore management
without the wired port: bring up the worker's wifi interface `wlP9s9`, join a
wifi network on the same `10.10.20.0/24` L2, and add `10.10.20.11/24` to
`wlP9s9` so the existing cluster config keeps working. This clears on reboot and
is a stopgap only — the wired NIC still needs a physical fix, and later sessions
have found the workaround not active (wifi down). Treat restored-over-wifi
management as a caveat to confirm, not a standing fact.

All of the above network repair steps require root, and there is **no
passwordless sudo** on either node — root steps are handed to the operator to
run in their own terminal.

## Related

- [Memory, Placement & Known Pitfalls](../operations/memory-placement-and-pitfalls.md)
- [Launching & Verifying a Recipe](../workflows/launching-and-verifying.md)
