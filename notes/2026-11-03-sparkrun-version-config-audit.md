# sparkrun version & configuration audit — 2026-11-03

Read-only audit. Every claim cites a command, file, or upstream URL. No state was changed.

## 1. Installed version — we are on the latest

- Installed: **sparkrun 0.4.2** (`sparkrun --version`), installed as a **uv tool**:
  `~/.local/bin/sparkrun → ~/.local/share/uv/tools/sparkrun/bin/sparkrun`, symlink dated **Nov 3 13:06** (upgraded today).
- Latest on PyPI: **0.4.2**, uploaded 2026-10-26 (`https://pypi.org/pypi/sparkrun/json`).
- Latest GitHub release: **v0.4.2**, published 2026-10-26T03:44:55Z
  (`gh api repos/spark-arena/sparkrun/releases`).
- **Version gap: none.** Note: repo docs (`CLAUDE.md` "sparkrun 0.3.10" gotchas) and the
  `dgx-pair-ep.yaml` comment still describe 0.3.10 behavior — see §6.

Releases between our previous notes (0.3.10, 2026-09-24) and now:

| Tag | Date | Highlights (release notes) |
|---|---|---|
| v0.4.0 | 2026-10-17 | Shared-blob model-cache transfer; **stop treating dangling symlinks as cached weights** (PR #300 — bears on the old "self-rsync deletes symlinked HF blobs" gotcha); LiteLLM router_settings from proxy.yaml + least-in-flight balancing (PR #317/#318); monitor/TUI redesign |
| v0.4.1 | 2026-10-19 | Plugin API: export collective providers (PR #328) |
| v0.4.2 | 2026-10-26 | stop/logs + relaunch eviction use cluster hardware inventory (PR #329); setup wizard SSH-verify fix (PR #330); TUI round 2 (PR #331) |

Sources: `https://github.com/spark-arena/sparkrun/releases/tag/v0.4.0` (and v0.4.1, v0.4.2).

## 2. Documentation matched to installed version (tag v0.4.2)

Docs directory at our exact version: `https://github.com/spark-arena/sparkrun/tree/v0.4.2/docs`
(listing verified via `gh api …/contents/docs?ref=v0.4.2`). Key pages:

- `docs/STARTUP_READINESS.md` — readiness semantics
- `docs/PROXY.md` — gateway/proxy
- `docs/SPARKROUTE.md` — the gateway we actually run
- `docs/DAEMON.md`, `docs/DAEMON_API.md` — daemon (we have the feature on, daemon not running)
- `docs/UPGRADING_0_4.md` — 0.3.x → 0.4 migration (read; quoted below)
- `docs/PLUGINS.md`, `docs/MODEL_CACHE.md`, `docs/SECURITY.md`, `docs/SETUP_STEPS.md`, `docs/OCI_RELAY.md`

Prefix any doc path with `https://github.com/spark-arena/sparkrun/blob/v0.4.2/` for the version-matched copy.

## 3. Features: enabled-vs-default and what they cause us

`sparkrun setup features list --all` (channel: stable). SOURCE=`config` means **we** enabled it
(non-default); SOURCE=`channel` is the stable-channel default.

| Feature | State | Source | What it causes us |
|---|---|---|---|
| `gateway.sparkroute` | on | **config** | SparkRoute selected as the active gateway (plugin diagnostics: "Selected gateway: sparkroute"). LiteLLM remains the upstream default; our selection persists even if the plugin disappears (UPGRADING_0_4.md). The running proxy on :4000 is SparkRoute. |
| `daemon` | on | **config** | Enables the durable local API service. Currently **not running** (`sparkrun daemon status` → `running: false`, binding 2f207e03342af53d3194). Cost while stopped: none, but core updates refuse replacement while runtime leases are live (UPGRADING_0_4.md) — stop daemon workers before upgrading. |
| `core.external_plugins` | on | **config** | Loads out-of-tree plugins at startup — required for sparkroute (0.3.4) and coldsnap (0.2.0), both git-sourced from `github.com/sparksq/*` on **branch `main`** with trust `scope: source` granted 2026-11-03 (plugins.yaml). Consequence: `sparkrun plugins update` can advance them to any future compatible commit from those repos without a new trust prompt. |
| `executor.local` | on | **config** | Experimental native (no-container) executor becomes available. Only used when a recipe/launch selects it; no effect on our Docker recipes otherwise. |
| `cli.setup.rdma_test` | on | **config** | Adds `sparkrun setup rdma-test` (per-link RDMA bandwidth/latency). Diagnostic only; consumes the CX7 links while running. |
| `cli.setup.tailscale` | on | **config** | Experimental `setup tailscale` command group (join nodes / publish endpoint on a tailnet). Risk is only if invoked — it can publish an endpoint off-LAN. |
| `cli.tune`, `gateway`, `gateway.litellm`, `executor.docker`, `cli.setup.wizard`, `setup.steps.*` | on | channel | Stable-channel defaults, not our doing. |

Plugins (`sparkrun plugins list --all`): in-tree k8s/lil **disabled**; litellm, oci_relay,
sparkarena **enabled** (in-tree defaults); external **coldsnap 0.2.0** and **sparkroute 0.3.4**
enabled, both `requires_sparkrun >=0.4,<0.5` — compatible with 0.4.2
(`~/.config/sparkrun/plugins.yaml`, `plugins-update-report.json` shows core 0.4.2, Python 3.13.14).

## 4. Registries, recipes, proxy, daemon (operational state)

- **10 registries** configured (`sparkrun registry list` / `registries.yaml`):
  official, experimental, community, eugr, atlas, sparkrun-testing (untrusted), sparkrun-transitional,
  coldsnap (plugin-provided, untrusted), coldsnap-vanilla (untrusted), and
  **spark-forge = `file:///home/devops/workspace/sparkrun-recipes`** (this repo, trusted).
- **118 recipes** visible across enabled registries (`sparkrun recipe search "" | grep -c '^@'`).
- **Proxy (SparkRoute) is RUNNING**: pid 1170448, **host 0.0.0.0, port 4000**, started
  2026-11-03T07:30:35Z, with autodiscovery (pid 1170472) sweeping cluster dgx-pair every 30 s
  (`sparkrun proxy status --json`). 5 model routes exposed:
  `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit`, `deepseek-v4-flash-vision-uncensored`,
  `qwen3.8-flash-next`, `qwen38-27b`, `qwen38-27b:low`.
  **But `sparkrun status --cluster dgx-pair` (15:43 today) showed both hosts idle with no
  sparkrun containers** — these routes are operator/static routes with no live backend right now;
  requests to them will fail until a workload is launched. Discovery warning: discovered
  `qwen38-27b` collides with a reserved operator route of the same name.
- Proxy config: `proxy.yaml` → `gateway: sparkroute`; aliases `default → qwen3.8-27b-uncensored`,
  `auto → '*'`; discovered_models: `qwen38-27b`.
- `proxy.env` holds **secrets** (HF_TOKEN, NGC_API_KEY, NVIDIA_API_KEY, OLLAMA_API_KEY — present,
  values not reproduced here), file mode 600. Plus HF_HOME/HF_CACHE/CUDA paths.
- **Daemon: not running** (`sparkrun daemon status` → `running: false`) despite feature enabled.

## 5. Cluster configuration audit (`~/.config/sparkrun/`)

- `config.yaml`: channel stable from PyPI; ssh user devops; **telemetry disabled**
  (installation_id present); features/plugins as in §3.
- `clusters/.default` = `dgx-pair`.
- **`clusters/dgx-pair.yaml` — load-bearing env pins all PRESENT** ✅:
  `NCCL_IB_HCA: rocep1s0f1,roceP2p1s0f1`; `NCCL_SOCKET_IFNAME: enp1s0f1np1,enP2p1s0f1np1`;
  `GLOO_SOCKET_IFNAME: enp1s0f1np1`; `TP_SOCKET_IFNAME: enp1s0f1np1`.
  transfer_interface cx7, topology switch, scheduler occupancy-sparse.
- `clusters/dgx-pair-ep.yaml`: same pins ✅ plus `max_gpu_memory_utilization: 0.95` with the
  2026-09-27 comment explaining the 0.3.10 EP fit-planner workaround (see §6 — re-verify on 0.4.2).
- `clusters/gb10-solo.yaml` / `gx10-solo.yaml`: single-host, cx7, occupancy-sparse — sane.
- `clusters/dgx-pair.manifest.yaml`: setup phases ssh_mesh/earlyoom/docker_group/nvidia_cdi/cx7 applied
  2026-09-28; **sudoers phase re-applied 2026-11-02** (`/etc/sudoers.d/sparkrun-chown-devops`);
  cx7 phase records the dual subnets 10.99.10.0/24 + 10.99.11.0/24 (the intentional f0/f1 duplicate-IP design).

## 6. Risks / follow-ups found

1. **Proxy binds 0.0.0.0:4000** — SparkRoute is reachable from any interface on the head node
   (including wifi/LAN), not just localhost/CX7. The workloads skill suggests
   `proxy start --host 127.0.0.1`. If exposure is unintended, restart with a narrower bind
   (user decision; proxy restart drops routes briefly).
2. **Stale 0.3.10 assumptions in repo docs.** `CLAUDE.md` gotchas ("sparkrun 0.3.10: self-rsync
   deletes symlinked HF blobs; digest-pinned images fail on worker; --no-rm") predate 0.4.x.
   v0.4.0 PR #300 specifically reworked shared-blob cache transfer and dangling-symlink handling —
   the rsync gotcha is plausibly fixed but **unverified on this pair**; keep hardlink-first until re-tested.
3. **`dgx-pair-ep.yaml` workaround may be obsolete.** Its 0.95 scheduling cap exists for the
   0.3.10 EP fit-planner bug; re-test `@atlas/minimax-m2.7-nvfp4-ep2` placement on 0.4.2 before
   relying on (or removing) the override.
4. **Plugins track `main` with source-scope trust** (sparkroute, coldsnap): future updates from
   those GitHub repos install without a new trust prompt. Pin a tag/commit if supply-chain
   tightening is wanted (pinned refs are not auto-advanced — UPGRADING_0_4.md).
5. **Untrusted registries enabled**: sparkrun-testing, coldsnap, coldsnap-vanilla are
   `trusted: false` but enabled — fine for search, but recipes from them warrant review before launch.
6. **Daemon feature on but service down** — harmless now; remember to drain daemon workers before
   core updates (UPGRADING_0_4.md) if it's ever started.
7. **Route-name collision warning** in proxy discovery: discovered `qwen38-27b` vs reserved
   operator route `qwen38-27b` (proxy status JSON) — cosmetic until both exist simultaneously.
8. Minor: `recipes-retired/` and `sparkroute/` operation logs accumulate under `~/.config/sparkrun/`
   (a few 0-byte and KB-size logs; no action needed).
