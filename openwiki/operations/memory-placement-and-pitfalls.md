---
type: operations
title: Memory, Placement & Known Pitfalls
description: The unified-memory operating envelope on the GB10 pair and the recurring failure modes — gpu_memory_utilization bounds, head-node earlyoom pressure, co-tenant context shrink, the one-model-per-node co-residency limit, 0.3.10-era sparkrun defects (now on 0.4.2), and HF-cache corruption from root-owned containers.
tags: [memory, placement, operations, earlyoom, sparkrun, pitfalls]
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-eedd5219d6290708f61cb7bf
    resource: repo://notes/2026-11-03-sparkrun-version-config-audit.md
  - id: openwiki-source-c60867cd14827f47e426d16c
    resource: repo://notes/minimax-m3-sparkrun-port/minimax-m3-w4a16-gptq-b12x-nvfp4-eagle3.yaml
  - id: openwiki-source-036e64f955b6e8c14e4c8d88
    resource: repo://notes/minimax-m3-sparkrun-port/README.md
  - id: openwiki-source-b1867d7f36dadf1642430baf
    resource: repo://recipes/qwen3-embedding-4b-tp1.yaml
  - id: openwiki-source-5c6fb7c964f2f95da074a267
    resource: repo://recipes/qwen3-reranker-4b-tp1.yaml
generated: { by: "claude-code", at: "2026-11-08T21:00:19.321Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
---

# Memory, Placement & Known Pitfalls

On a GB10 node, weights, KV cache, page cache, and the host OS all draw from the
**same ~121 GiB of unified memory**. Most launch failures on this pair are a
memory or placement problem, not a model problem. This page collects the
recurring ones.

## The gpu_memory_utilization envelope

The working range is **0.70–0.82**. Setting it to **0.85 has caused NVRM OOM at
boot**. Within the range, a given recipe may still have its own floor below
which no KV fits, so the value is tuned per recipe, not set globally.

The range is for full-size chat engines. Small pooling-runner recipes (the
2026-11-08 embedding/reranker pair, 7.5 GiB of weights each) deliberately run at
**0.3** so they can sit beside other work on a node — the envelope is an upper
bound driven by boot stability, not a target.

## Head-node earlyoom pressure

The head node runs `earlyoom` with an aggressive trigger (`-m 2`, ~2.49 GiB
available). A long-context prefill can drive head memory low enough that earlyoom
SIGTERMs a process — and the victim has included the vLLM worker and even
unrelated processes on the head. This is why a recipe that serves short and 40k
prompts can still be killed by a 250k-token prompt, and why the long-context GLM
profile was initially marked unfit: the kills came from ~3 GiB of extra head
residents eating the earlyoom margin, not from the recipe itself. **A quiet head
is a launch precondition** for long-context work; the needle harness reports a
head memory low-water mark precisely so this margin is visible.

## Co-tenants shrink auto-sized context

sparkrun only sees its **own** containers. Any other container on a node — a
vector DB, a reranker, another engine — consumes unified memory that the engine
can no longer use, which silently shrinks an `auto`-sized context (a large
enough co-tenant has collapsed it dramatically). **Before a large launch, check
`docker ps` and memory on both nodes**, not just sparkrun's view.

## One model per node — no two-node co-residency

Two multi-node models cannot share the pair. Repeated attempts to run a second
model beside a two-node Flash job failed every way: the co-tenant's warmup
starved KV, its boot memory-spiked the Flash rank to death, and sparkrun's
placement refuses to put a tensor-parallel rank on an already-occupied host
(`only placed 1 of 2 ranks`). What *does* work concurrently is **one solo
(`--tp 1`) model per node** — sparkrun places two single-node jobs happily; only
multi-node jobs demand exclusive hosts.

## Scheduler admission: occupancy-sparse vs. greedy

Under the `occupancy-sparse` scheduler (the 0.3.x default for new clusters),
sparkrun's **VRAM estimate is a hard admission check** — and the estimator can
be wrong in the direction that refuses a launch outright. The worked example is
the MiniMax-M3 port (`notes/minimax-m3-sparkrun-port/`): the estimator charges
4 KV heads across all 60 layers where the model's MSA layers carry 2, inflating
the figure to 115.2 GB per rank against a 121 GB accelerator, so placement fails
with `only placed 0 of 2 ranks` and **no** cluster-wide `--max-gpu-mem-util`
value can fix it. The escape is per-recipe `scheduler: greedy`, which places the
ranks and lets vLLM's own memory profiler — which knows the real KV geometry —
be the authority. The same reasoning applies to the per-host `[EXCEEDS]`
warning: when the estimate is known-wrong, measured reality (a 208,128-token KV
pool, in that case) wins, and `max_model_len` should not be lowered to appease
the estimator.

## sparkrun version gotchas (0.3.10-era, now on 0.4.2)

The installed sparkrun is now **0.4.2** (uv tool). Three defects observed on
0.3.10 shaped day-to-day operations, and their workarounds stand until
re-verified on 0.4.x:

- **Self-rsync deletes symlinked HF blobs** (0.3.10). The resource transfer
  could delete symlinked HuggingFace cache blobs; the workaround is to hardlink
  them first. v0.4.0 (PR #300) reworked shared-blob cache transfer and
  dangling-symlink handling, so this is **plausibly fixed but unverified on
  this pair** — keep hardlink-first until re-tested.
- **Digest-pinned images fail on the worker** (0.3.10). sparkrun could not ship
  a digest-pinned image to the worker node, so recipes use a **dated tag**
  rather than a `@sha256:` digest even though digests are otherwise preferable.
- **`--no-rm` does not keep crashed containers** (0.3.10). It did not preserve
  a container that crashed, so it could not be relied on to post-mortem a boot
  failure.
- **The `dgx-pair-ep` 0.95 scheduling cap is a 0.3.10 workaround.**
  `clusters/dgx-pair-ep.yaml` carries `max_gpu_memory_utilization: 0.95` solely
  to dodge the 0.3.10 EP fit-planner bug (per its 2026-09-27 comment). Re-test
  EP placement on 0.4.2 before relying on — or removing — the override.

## HF-cache corruption from root-owned containers

A 2026-11-03 TP2 relaunch crashed because the worker's HuggingFace cache ref
(`refs/main`) for a checkpoint pointed at a root-owned **empty** snapshot —
left behind by a root container weeks earlier — while the complete 196 GB
snapshot sat beside it. The fix was a one-line ref update to the complete
snapshot's hash; the proper cleanup for leftover root-owned cache dirs is
`sparkrun setup fix-permissions` (needs interactive sudo). When a launch dies
loading weights that are known to be on disk, check whether `refs/main`
resolves to a populated snapshot before suspecting the download.

## Related

- [Cluster & Networking](../architecture/cluster-and-networking.md)
- [Benchmarking & Context Verification](../workflows/benchmarking.md)
