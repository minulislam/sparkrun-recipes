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
