---
type: reference
title: Container Images & Provenance
description: The container-image selection order and provenance rules for recipes — the spark-arena-first tier list, the immutable-tag policy and why dated tags beat digest pins here, and the locally built deepseek-rank1 runtime-abliteration image.
tags: [images, containers, provenance, security, spark-arena, policy]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-01T03:42:59.995Z
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-f6fa64275fc0add6809ef750
    resource: repo://IMAGE-POLICY.md
  - id: openwiki-source-7845db45164b8996bda8b203
    resource: repo://images/deepseek-rank1/README.md
generated: { by: "claude-code", at: "2026-11-01T03:42:59.995Z" }
---

# Container Images & Provenance

Every recipe pins a `container:`. Which image, and in what form, is governed by
a policy whose ordering is also a security ordering: more-reconstructible
provenance ranks higher.

## Selection order

1. **`ghcr.io/spark-arena/*`** — the project's own rebuilds. Preferred always.
2. **`eugr/*`** — consumed **via** the spark-arena rebuild where one exists, not
   pulled direct.
3. **Vendor image named by the model's own git/HF repo docs** — for non-official
   checkpoints, follow what the model publisher actually tests against.
4. **`vllm/vllm-openai` official** — fallback. Best upstream provenance, but it
   lacks the GB10 / NVFP4 / FlashInfer work, so it is not a default here.

## Why that order is also the secure order

The ranking tracks how reconstructible an image's build is. spark-arena rebuilds
carry a full provenance label chain (`dev.sparkrun.vllm-hash`, `vllm-version`,
`flashinfer-hash`, `source-digest`, `source-tag`, `repo-commit`) and are fully
reconstructible; official vLLM carries OCI/buildkite provenance; a **direct eugr
pull has no build labels at all** — digest-pinnable but opaque without running
it. Consuming eugr *through* spark-arena's rebuild is exactly what turns an
opaque image into a documented one, which is why tier 2 sits below tier 1 rather
than beside it. The standing rule is that a **verified recipe's image must carry
provenance labels** (`dev.sparkrun.*` or OCI `org.opencontainers.image.*`); if
it does not, it should be mirrored into spark-arena so it does.

## Immutable tags, and why dated tags beat digests here

**Immutable tags only** — no `:latest`, no floating `:nightly`, because a
floating tag can move or disappear under a recipe. Digest pins are otherwise the
strongest form, **but** sparkrun 0.3.10 fails to ship a digest-pinned image to
the worker node (see the operations pitfalls), so in practice a **dated tag**
(for example `...-b12x:20260926`) is the right form on this pair: immutable in
spirit and shippable to both nodes.

A known caveat the audit records: the b12x image line runs an **untagged vLLM
main** build, so it has full build labels but no release/CVE baseline — a
provenance win that is not a version-pinning win.

## The locally built deepseek-rank1 image

One recipe needs an image upstream does not publish. `spark-forge/vllm-dsv4-rank1`
is built locally for `deepseek-v4-flash-0731-refusal-dial-tp2`: it layers the
pocharlies rank-1 refusal-projection patch and its direction file onto an anemll
dspark-vLLM base, and exists only on the two nodes. Its README records the exact
source commit, base image, direction-file hash, and a reproducible rebuild +
`docker save | ssh docker load` push to the worker — the provenance that tier-1
policy demands, kept with the image rather than in a registry. (Mirroring vendor
images into spark-arena generally is blocked for want of a GHCR push credential
on this box.)

## Related

- [Recipe Anatomy](../concepts/recipe-anatomy.md)
- [Memory, Placement & Known Pitfalls](../operations/memory-placement-and-pitfalls.md)
