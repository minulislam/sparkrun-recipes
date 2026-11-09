# AGENTS.md

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

## Model storage

- Model backup is `/mnt/nas/ai-models/model-backup/huggingface-hub/` (NFS `10.10.20.2:/volume1/ai-models`, automount). The old `/mnt/nas/dgx-spark` share is removed; do not reference it. It held Proxmox backups, so never write to or read from that path.
- Back up a checkpoint there before deleting it. Deleting weights is the user's call.

<!-- OPENWIKI:START -->

## OpenWiki

This repository has a generated `openwiki/` evidence index. It is optional just-in-time context, not required startup reading.

- Do not enumerate, preload, or search wikis at task start. Use retrieval when the user asks for it, when unfamiliar architecture or dependency behavior materially affects the task, or when source inspection leaves an important uncertainty. Stop once the question is grounded.
- When those conditions apply and OpenWiki retrieval tools are available, use `openwiki_search` for just-in-time context and `openwiki_read` for the relevant complete sections. If search returns `workspace_required`, ask which listed workspace to use and retry with its ID.
- Use `openwiki_list_workspaces` or `openwiki_list_wikis` when workspace membership itself needs to be discovered.
- If the retrieval tools are unavailable, read `openwiki/quickstart.md` and follow its links to the relevant pages.
- Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements.
- Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->
