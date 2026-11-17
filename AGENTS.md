# AGENTS.md

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- spark-forge registry clones LOCAL main (file://); after pushing main also fast-forward local main then sparkrun registry update spark-forge
- Worker gx10-spark: mgmt 10.10.20.11 works again (ssh OK 2026-11-17) but has been flaky; CX7 data 10.99.10.11 for rsync
- Gateway: spark-loader on 0.0.0.0:4000 (on-demand load, default = largest running chat model, 30 min idle stop) in front of LiteLLM on 127.0.0.1:4001; SparkRoute removed 2026-11-17. Repo ~/workspace/llm/serving/spark-loader
- Embedder :8000 + reranker :8001 run OUTSIDE sparkrun (docker compose `spark-pinned` on gb10) because sparkrun 0.4.2 reserves a whole GPU per workload
- gh active account minulislam (rehanpatwary also logged in)

### Key Decisions
- Decision: layout recipes/<family>/<name>.yaml, filename stem unchanged — Reason: sparkrun recipe name = file stem; recipe.yaml everywhere would collide
- Decision: local mods referenced as ../mods/<name> — Reason: sparkrun resolves mods adjacent to recipe file; mods/<name> broke after reorg (fell to eugr fallback)
- Decision: Inkling refusal-dial text-only via --limit-mm-per-prompt image 0 — Reason: b12x image's mark_b12x_eager_shapes crashes on Inkling (encoder_rows None)
- Decision: Inkling mod run.sh chmod 0644 refusal dirs — Reason: cp kept 0600 as root; vLLM uid 1000 PermissionError
- Decision: Inkling gpu_memory_utilization 0.82 — Reason: 0.85 above repo ceiling, NVRM OOM risk
- Decision: Throughput artifact rows in db collection recipes (owner-write, view-read) + built-in fallback — Reason: update numbers without republish
- Decision: Flash-Next solo 73.7 from HISTORY.md:784 — Reason: post-MTU-fix figure; raw file holds only c=8 row

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
