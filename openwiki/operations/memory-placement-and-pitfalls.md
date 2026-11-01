---
type: operations
title: Memory, Placement & Known Pitfalls
description: The unified-memory operating envelope on the GB10 pair and the recurring failure modes — gpu_memory_utilization bounds, head-node earlyoom pressure, co-tenant context shrink, the one-model-per-node co-residency limit, and the sparkrun 0.3.10 defects.
tags: [memory, placement, operations, earlyoom, sparkrun, pitfalls]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
---

# Memory, Placement & Known Pitfalls

On a GB10 node, weights, KV cache, page cache, and the host OS all draw from the
**same ~121 GiB of unified memory**. Most launch failures on this pair are a
memory or placement problem, not a model problem. This page collects the
recurring ones.

## The gpu_memory_utilization envelope

The working range is **0.70–0.82**. Setting it to **0.85 has caused NVRM OOM at
boot**. Within the range, a given recipe may still have its own floor — a large
Flash checkpoint has needed ≥0.64 just to leave room for any KV at all — so the
value is tuned per recipe, not set globally.

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

## sparkrun 0.3.10 defects to work around

Three defects in the pinned sparkrun version shape day-to-day operations:

- **Self-rsync deletes symlinked HF blobs.** The resource transfer can delete
  symlinked HuggingFace cache blobs; hardlink them first so the transfer does
  not destroy the cache.
- **Digest-pinned images fail on the worker.** sparkrun cannot ship a
  digest-pinned image to the worker node, so recipes use a **dated tag** rather
  than a `@sha256:` digest even though digests are otherwise preferable.
- **`--no-rm` does not keep crashed containers.** It does not preserve a
  container that crashed, so it cannot be relied on to post-mortem a boot
  failure.

## Related

- [Cluster & Networking](../architecture/cluster-and-networking.md)
- [Benchmarking & Context Verification](../workflows/benchmarking.md)
