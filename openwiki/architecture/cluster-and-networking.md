---
type: architecture
title: Cluster & Networking
description: The dgx-pair two-node DGX Spark topology, the load-bearing NCCL/Gloo comm pins, the intentional ConnectX-7 duplicate-IP layout, and the separation of the management plane from the CX7 data plane.
tags: [cluster, networking, dgx-spark, nccl, connectx-7, topology]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-09T21:00:11.445Z
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

- **CX7 data plane** — the dual `10.99.10.0/24` + `10.99.11.0/24` RoCE fabric
  (two 200 Gb/s cables) that carries all tensor-parallel all-reduce traffic
  between ranks. This is what inference performance depends on.
- **Management plane** — the worker's wired NIC `enP7s7` holds the management
  address `10.10.20.11`, which sparkrun uses for orchestration and SSH. Only
  rendezvous/bootstrap traffic rides this path; NCCL data stays on the CX7
  fabric, so a degraded (even wifi) management link is acceptable for launches.

The management NIC has proven unstable: `enP7s7` has repeatedly lost physical
link (NO-CARRIER, 69 carrier flaps recorded since one boot — a marginal
cable/switch port, hardware fix still pending as of 2026-11-03). Because the
data plane can be healthy while management is down, a two-node job can wedge
even though the CX7 fabric is fine. During one outage, launches fell back to
the CX7 addresses directly (`--hosts 10.99.10.10,10.99.10.11` plus
`HF_HUB_OFFLINE=1`) instead of `--cluster dgx-pair`.

The current workaround (2026-11-03) is a dedicated WiFi SSID **"Citadel LAB"**
bridged onto `10.10.20.0/24`, configured on the worker with static
`10.10.20.11` and `ipv4.route-metric 200` so the wired path auto-wins once the
cable/port is repaired. Beware: the worker's NetworkManager has flipped back to
the old "Rayan's Mesh" profile (DHCP `10.10.10.158`) mid-session, breaking
management again — the fix is `sudo nmcli con up "Citadel LAB"` plus an
autoconnect-priority adjustment on the worker.

All of the above network repair steps require root, and there is **no
passwordless sudo** on either node — root steps are handed to the operator to
run in their own terminal.

## The 2026-11-03 CX7 MTU repair

A long-standing jumbo-frame blackhole on the fabric was root-caused and fixed
on 2026-11-03: on the head node, the `f1` interfaces (`enp1s0f1np1`,
`enP2p1s0f1np1`) sat at MTU 1500 because NetworkManager auto-profiles covered
them while the netplan `40-cx7.yaml` only set the `f0` functions. That capped
RoCE `active_mtu` at 1024 on exactly the HCAs the cluster pins NCCL to. After
`nmcli con mod ... 802-3-ethernet.mtu 9000`, all 8 HCAs across both nodes
report `active_mtu 4096`, DF-ping at 8972 bytes passes on both subnets, and
`sparkrun setup rdma-test` measures 111.6 Gb/s per link — **195.6 Gb/s of the
200 Gb/s aggregate** — at 1.8 µs latency. Benchmarks re-run after the fix
improved sharply (see the benchmarking page).

A follow-up experiment on 2026-11-03 tried widening the NCCL pin to all four
HCA functions (`rocep1s0f0,rocep1s0f1,roceP2p1s0f0,roceP2p1s0f1`). The result
was **negative**: the b12x RoCE transport caps at 2 HCAs and takes the first
two listed — both PCIe functions of the *same* physical cable — which is
strictly worse than the existing f1-per-subnet pin that already drives both
cables. The `dgx-pair.yaml` pin stays as-is.

## sparkrun version and gateway

The CLI is **sparkrun 0.4.2** (installed as a uv tool; the 0.3.10-era gotchas
recorded elsewhere in repo docs predate 0.4.x). The active inference gateway is
the **SparkRoute** plugin (0.3.4), running as the proxy on the head node. It
originally bound **0.0.0.0:4000** — reachable from any interface on the head —
which the 2026-11-03 version audit flagged as an exposure risk; on 2026-11-07
the proxy was restarted bound to **127.0.0.1:4000** (loopback only). See the
proxy & gateway routing page for the binding model and current routes.

## Related

- [Memory, Placement & Known Pitfalls](../operations/memory-placement-and-pitfalls.md)
- [Launching & Verifying a Recipe](../workflows/launching-and-verifying.md)
- [Proxy & Gateway Routing (SparkRoute)](../operations/proxy-and-gateway-routing.md)
