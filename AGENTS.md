# AGENTS.md

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- spark-forge registry clones LOCAL main (file://); after committing on develop, fast-forward local main (never push main) then sparkrun registry update spark-forge
- Worker gx10-spark: mgmt 10.10.20.11 works again (ssh OK 2026-11-17) but has been flaky; CX7 data 10.99.10.11 for rsync
- Gateway: spark-loader on 0.0.0.0:4000 (on-demand load, default = largest running chat model, 30 min idle stop) in front of LiteLLM on 127.0.0.1:4001; SparkRoute removed 2026-11-17. Repo ~/workspace/llm/serving/spark-loader
- Embedder :8000 + reranker :8001 run OUTSIDE sparkrun (docker compose `spark-pinned` on gb10) because sparkrun 0.4.2 reserves a whole GPU per workload
- gh active account minulislam (rehanpatwary also logged in)
- sparkrun venv python: ~/.local/share/uv/tools/sparkrun/bin/python (import sparkrun internals)
- DGX Spark platform tier supplies CUTE_DSL_ARCH=sm_121a and PYTORCH_CUDA_ALLOC_CONF for vllm/sglang (sparkrun/platforms/dgx_spark.py:82)
- Platform default images are :latest (dgx_spark.py:23) — always set container:
- Head f1 ports now static: Wired connection 5 = 10.99.10.10/24, 4 = 10.99.11.10/24

### Key Decisions
- Decision: Throughput artifact rows in db collection recipes (owner-write, view-read) + built-in fallback — Reason: update numbers without republish
- Decision: Flash-Next solo 73.7 from HISTORY.md:784 — Reason: post-MTU-fix figure; raw file holds only c=8 row
- Decision: pin 42 vLLM/SGLang recipes to head refs/main SHA + --revision {model_revision} — Reason: sparkrun download_model calls snapshot_download every online launch (models/download.py:495) so unpinned drifts; SHA pin w/o --revision fails offline (no refs/, HF_HUB_OFFLINE=1). All 44 cached refs matched upstream at pin time
- Decision: Atlas EP2 recipes unpinned — Reason: Atlas runtime declares no model_revision_flags
- Decision: keep minimax/inkling comm env + glm TRITON_CACHE_DIR — Reason: measured workarounds in VERIFIED recipes; removal needs live retest

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
