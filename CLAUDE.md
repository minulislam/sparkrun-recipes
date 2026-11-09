# spark-forge recipe registry

sparkrun recipes for a two-node DGX Spark pair: head `gb10-spark` (10.10.20.10)
and worker `gx10-spark` (10.10.20.11), both GB10 with about 121 GiB unified
memory. The repo is `minulislam/sparkrun-recipes`; the sparkrun registry it
publishes is named `spark-forge`. The name mismatch is deliberate.

## Read first

| File | Use it for |
|---|---|
| `CONTEXT.md` | Vocabulary. *Verified* means the model answered a request on this pair; a lint or dry run never qualifies |
| `MODELS.md` | Which checkpoints are complete, partial or stubs on each node, and which recipes use them |
| `INDEX.md` | Every recipe with its status and measured numbers. Do not renumber rows |
| `HISTORY.md` | Dated record of all work, the user's standing rules, and open items. Append to it after each block of work |
| `IMAGE-POLICY.md` | Which container image to choose and how to pin it |
| `.claude/skills/verify/SKILL.md` | How to launch a recipe and prove it serves |

The live cluster is the source of truth. Docs record what was measured on a
date; re-check before acting on them.

## Rules

- **Registry is a git clone of `main`.** A recipe change is invisible to
  sparkrun until it is committed to `main` and
  `sparkrun registry update spark-forge` has run. Work goes straight to `main`;
  there is no PR step. Commit and push only when asked.
- **Search before writing a recipe.** Run `sparkrun registry update`, then
  `sparkrun recipe search` across every registry. If upstream has one, copy it
  with an attribution header and change only what this pair needs.
- **Images:** spark-arena builds first, then eugr, then the model publisher's
  own docs, then official vLLM. Immutable tags only. Reuse images already on
  disk.
- **Weights are hard to replace.** Check `MODELS.md` before launching. Back up
  to `/mnt/nas/dgx-spark/model-backup/` before deleting a checkpoint. Deleting
  weights is the user's call. Never run `hf cache prune` without `--dry-run`.
- **Keep what runs on two nodes; drop what needs three.**
- **One canonical copy of each recipe.** Benchmark reports live in
  `benchmarks/`.
- **Report a status only at the bar you reached**: lints, serves, verified or
  benchmarked.
- **Never print secrets** (HF token, API keys) into output or files.

## Cluster facts that bite

- Clusters: `dgx-pair` (default), `dgx-pair-ep` (EP-only recipes), `gb10-solo`,
  `gx10-solo`. There is no cluster named `default`.
- Two-node comm pins live in `~/.config/sparkrun/clusters/dgx-pair.yaml` under
  `env:`. They are load-bearing; do not move them into recipes.
- The duplicate IPv4 on the f0 and f1 port of each ConnectX-7 NIC is
  intentional. Do not re-address it. Do not run `sparkrun setup cx7` or the
  setup wizard on `dgx-pair`.
- After a worker reboot, run `sparkrun setup check --cluster dgx-pair` before a
  two-node launch.
- `gpu_memory_utilization` 0.70–0.82. 0.85 has caused NVRM OOM at boot.
- A co-tenant on a node shrinks auto-sized context. Check `docker ps` and
  `nvidia-smi` on both nodes before a large launch; sparkrun only sees its own
  containers.
- Images that bake `ENTRYPOINT ["vllm","serve"]` need
  `executor_config: {entrypoint: ""}`.
- Serve logs are in `/tmp/sparkrun_serve.log` inside the container.
- Always launch with `--no-follow`. Load the `sparkrun:run` skill before using
  the CLI.
- sparkrun 0.3.10: self-rsync deletes symlinked HF blobs (hardlink first),
  digest-pinned images fail on the worker (use tags), `--no-rm` does not keep
  crashed containers.
- No passwordless sudo on either node. Hand root steps to the user.

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- Bindings live ONLY in proxy.yaml; no CLI add/remove command; sparkrun proxy sync makes gateway match file atomically
- Gateway admin API on 127.0.0.1:4000 (bound 0.0.0.0, NO auth): GET/PUT /v1/config/managed-sets/operator, validate endpoint, CAS via expected_active_revision
- SparkRoute plugin source (installed 0.3.4) at ~/.config/sparkrun/plugins/sparkroute/*/payload/ is authoritative; upstream docs omit binding schema (fields: recipe, cluster/cluster_candidates, cold_start wait|reject, model, overrides, capabilities)
- sparkrun 0.4.2 via uv tool; always rtk-prefix shell commands; worker gx10-spark mgmt 10.10.20.11 flaky, CX7 data 10.99.10.11

### Key Decisions
- Decision: bindings qualified as @spark-forge/<recipe> — Reason: plain names ambiguous (local checkout and spark-forge registry both match); resolver demands exact recipe
- Decision: cold_start: wait on all bindings — Reason: requests queue through multi-minute model swaps instead of erroring
- Decision: idle-node-first policy encoded via cluster_candidates order (TP1 recipe: gb10-solo then gx10-solo) — Reason: SparkRoute 0.3.4 has no preempt-on-demand; eviction only via gateway idle timers on gateway-owned jobs
- Decision: removed 3 operator virtual models (qwen3.8-flash-next, bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit, deepseek-v4-flash-vision-uncensored) and their stale adopted deployments via admin API CAS replace — Reason: strict validation rejects a sparkrun binding whose public name an operator route owns; backup at ~/.config/sparkrun/sparkroute/operator-set-backup-2026-11-03.json
- Decision: kept qwen38-27b and :low as operator routes — Reason: :low is a manual request profile; no recipe sparkroute block exists

<!-- handoff:learnings:end -->

<!-- OPENWIKI:START -->

## OpenWiki

@AGENTS.md

<!-- OPENWIKI:END -->
