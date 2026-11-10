---
type: reference
title: Container Images & Provenance
description: The container-image selection order and provenance rules for recipes — the spark-arena-first tier list, the immutable-tag policy and why dated tags beat digest pins here, and the locally built deepseek-rank1 runtime-abliteration image.
tags: [images, containers, provenance, security, spark-arena, policy]
sources:
  - id: openwiki-source-a2371d6362e5db4bc834ad03
    resource: repo://CLAUDE.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-f6fa64275fc0add6809ef750
    resource: repo://IMAGE-POLICY.md
  - id: openwiki-source-7845db45164b8996bda8b203
    resource: repo://images/deepseek-rank1/README.md
  - id: openwiki-source-036e64f955b6e8c14e4c8d88
    resource: repo://notes/minimax-m3-sparkrun-port/README.md
  - id: openwiki-source-b1867d7f36dadf1642430baf
    resource: repo://recipes/qwen3-embedding-4b-tp1.yaml
generated: { by: "claude-code", at: "2026-11-09T21:00:11.445Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-09T21:00:11.445Z
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
strongest form, **but** sparkrun 0.3.10 failed to ship a digest-pinned image to
the worker node (see the operations pitfalls; unverified whether 0.4.2 still
does), so in practice a **dated tag**
(for example `...-b12x:20260926`) is the right form on this pair: immutable in
spirit and shippable to both nodes.

A known caveat the audit records: the b12x image line runs an **untagged vLLM
main** build, so it has full build labels but no release/CVE baseline — a
provenance win that is not a version-pinning win.

A worked example of the pinning rule: the upstream `@official` Qwen3-VL
embedding/reranker recipes name a floating `tf5:latest`; when they were adapted
as rows 65–66 (2026-11-08), the container was pinned to
`ghcr.io/spark-arena/dgx-vllm-eugr-nightly-tf5:2026092702` — the dated tf5
build already on disk — satisfying both the immutable-tag rule and the
reuse-on-disk-images rule at once. The worker did not hold that image (24.8 GB)
at adoption; on 2026-11-09 it was streamed to `gx10-spark` with `docker save |
ssh docker load`, so `gx10-solo` activations no longer need a pull.

## Images that must be built from source

The MiniMax-M3 port (`notes/minimax-m3-sparkrun-port/`) names an image that
**does not exist in any registry**: there is no published
`vllm-node-minimax-m3-b12x`. It must be built on the head node from a3refaat's
patched `spark-vllm-docker` checkout (branch `minimax-m3-4bit-w4a16`, two
patches applied, `./build-deploy.sh`, ~29 GB, 1–2 h cold); sparkrun then
distributes the built image to the worker itself via
`docker save | ssh docker load`. Like deepseek-rank1, the provenance lives in
the port's PROVENANCE notes rather than in a registry.

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
