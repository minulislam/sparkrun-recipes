# AGENTS.md

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- Registry = git clone of main; recipe change visible only after commit to main + sparkrun registry update spark-forge; no PR step
- Always launch with --no-follow; load sparkrun:run skill before CLI
- Cluster dgx-pair: head gb10-spark 10.10.20.10; worker gx10-spark mgmt 10.10.20.11, CX7 data 10.99.10.11; clusters: dgx-pair, dgx-pair-ep, gb10-solo, gx10-solo (no 'default')
- Two-node comm pins in ~/.config/sparkrun/clusters/dgx-pair.yaml env: load-bearing; do not move into recipes
- Duplicate IPv4 on CX7 f0/f1 intentional; never run sparkrun setup cx7 or wizard on dgx-pair
- After worker reboot run sparkrun setup check --cluster dgx-pair before 2-node launch
- gpu_memory_utilization 0.70-0.82 (0.85 caused NVRM OOM at boot); Flash needs >=0.64
- Images with ENTRYPOINT vllm serve need executor_config entrypoint empty; digest-pinned images fail on worker (use tags)
- Serve logs at /tmp/sparkrun_serve.log inside container; co-tenant containers shrink auto-sized context
- No passwordless sudo on either node; root steps to user
- Never print secrets; never hf cache prune without --dry-run; weight deletion user's call; back up to /mnt/nas/dgx-spark/model-backup/ first
- Commit attribution: Claude-Session URL per workspace CLAUDE.md

### Key Decisions
- Decision: stop wedged sparkrun job and free head GPU — Reason: engine unrecoverable without worker rank; reversible by relaunch
- Decision: record 3 completed cells as partial, not VERIFIED — Reason: ladder incomplete, verdict requires full ladder
- Decision: no wifi/sudo credential handling by agent; user runs root steps in own terminal — Reason: repo rule, no passwordless sudo
- Decision: keep repo changes uncommitted — Reason: repo rule, commit only when asked
- Decision: work additively over CX7 link only — Reason: only remaining access path, avoid dropping it

<!-- handoff:learnings:end -->
