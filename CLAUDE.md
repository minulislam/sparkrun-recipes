# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
date; re-check before acting on them. `README.md` is the public face and is
older than the rest (it still names a cluster `default`, which does not exist).

## Commands

There is nothing to build. The work is YAML recipes run through the `sparkrun`
CLI (0.4.2, uv tool).

```bash
sparkrun recipe validate recipes/<family>/<name>.yaml        # one file per call; warnings do not block
sparkrun recipe show ./recipes/<family>/<name>.yaml          # render the working-tree copy
sparkrun recipe show @spark-forge/<name>            # render what the registry (= main) serves
sparkrun run ./recipes/<family>/<name>.yaml --cluster <c> --dry-run
sparkrun run ./recipes/<family>/<name>.yaml --cluster <c> --no-follow
sparkrun stop ./recipes/<family>/<name>.yaml --cluster <c>
sparkrun registry update spark-forge                # after committing to main
sparkrun proxy sync                                 # make the gateway match proxy.yaml
```

To re-measure weights for `MODELS.md`, run the script under its *Regenerate*
section on each node (copy it to the worker first).

## How the pieces connect

- **Recipe → registry.** `~/.config/sparkrun/registries.yaml` defines
  `spark-forge` as `file:///home/devops/workspace/sparkrun-recipes`, subpath
  `recipes`. sparkrun keeps a clone of local `main` at
  `~/.cache/sparkrun/registries/spark-forge`. The working tree is often on
  `develop`, so a commit there is invisible to sparkrun until it reaches `main`.
  Check `git branch --show-current` before committing.
- **Registry → gateway.** `spark-loader` (`~/workspace/llm/serving/spark-loader`,
  user unit `spark-loader.service`) listens on `0.0.0.0:4000`. Its catalog
  `~/.config/spark-loader/catalog.yaml` names `@spark-forge/<name>` recipes; a
  request for a catalog model that isn't running loads it through the sparkrun
  daemon, else falls back to `default` (largest running chat model). It forwards
  to LiteLLM (`sparkrun-proxy.service`, `127.0.0.1:4001`), whose model list
  comes from sparkrun discovery. `proxy.yaml` keeps only aliases and proxy
  settings; SparkRoute and its bindings were removed 2026-11-17.
- **Recipe → weights.** `model:` names the HF repo. `model_revision:` alone does
  not reach vLLM; the `command:` must also pass `--revision {model_revision}`.
  A recipe that loads a local directory sets `model_path:` instead, using the
  container path `/cache/huggingface/...` (the host's `~/.cache/huggingface`).
- **Overlays and images.** `recipes/mods/<name>/` holds runtime patches that
  recipes reference by name. `images/<name>/` holds locally built images (e.g.
  `images/deepseek-rank1/` for the DeepSeek refusal-dial recipe).
- **Evidence.** `benchmarks/` holds reports, `benchmarks/results/` raw runs,
  `benchmarks/scripts/` the drivers. `openwiki/` is generated nightly; do not
  hand-edit it. Design docs live in `docs/superpowers/specs/`.

## Rules

- **Registry is a clone of local `main`.** A recipe change is invisible to
  sparkrun until it is committed to `main` and
  `sparkrun registry update spark-forge` has run. There is no PR step. Commit
  and push only when asked.
- **Search before writing a recipe.** Run `sparkrun registry update`, then
  `sparkrun recipe search` across every registry. If upstream has one, copy it
  with an attribution header and change only what this pair needs.
- **Images:** spark-arena builds first, then eugr, then the model publisher's
  own docs, then official vLLM. Immutable tags only. Reuse images already on
  disk.
- **Weights are hard to replace.** Check `MODELS.md` before launching. Back up
  to `/mnt/nas/ai-models/model-backup/huggingface-hub/` before deleting a
  checkpoint. Deleting weights is the user's call.
- **Never run `hf cache prune` for real.** Its dry run lists about 1.2 TB here,
  including detached revisions that recipes pin. Delete with `hf cache rm`
  (dry run first). Repo blobs are hardlinks or symlinks into a shared store at
  `~/.cache/huggingface/hub/blobs/<2-char>/<sha256>`, so `hf cache rm` frees
  nothing until the unreferenced store files go too.
- **A TP2/EP2 recipe needs its weights on both nodes.** `MODELS.md` lists which
  ones have them; as of 2026-11-10 most two-node checkpoints are head-only.
- **Layout:** `recipes/<family>/<recipe-name>.yaml` (deepseek, gemma, glm,
  qwen, nemotron, minimax, inkling, and one folder per single-recipe family).
  The filename stem is the recipe name sparkrun resolves, so keep it unique
  across families and never rename it to `recipe.yaml`. Shared mods stay in
  `recipes/mods/`; reference them as `../mods/<name>` so they resolve next to
  the recipe for both `./recipes/...` and `@spark-forge/...` launches (a bare
  `mods/<name>` only resolves through the eugr fallback).
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
- Seen on sparkrun 0.3.10 (not re-checked on 0.4.2): self-rsync deletes
  symlinked HF blobs (hardlink first), digest-pinned images fail on the worker
  (use tags), `--no-rm` does not keep crashed containers.
- `sparkrun proxy start`/`alias add` can fail with `ResourceBusy` while the
  proxy runs under `sparkrun-proxy.service`. Edit `proxy.yaml`, then
  `sparkrun proxy sync`, or restart the unit
  (`sudo -n systemctl restart sparkrun-proxy.service` is allowed without a password).
- No passwordless sudo on either node, apart from start/stop/restart of
  `sparkrun-proxy.service` on the head. Hand other root steps to the user.

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

<!-- OPENWIKI:START -->

## OpenWiki

@AGENTS.md

<!-- OPENWIKI:END -->
