# Container image policy and provenance audit

Audited 2026-10-01 across all recipe `container:` pins on dgx-pair.

## Selection order

1. **`ghcr.io/spark-arena/*`** — our own rebuilds. Preferred always.
2. **`eugr/*`** — consume via the spark-arena rebuild where one exists, not direct.
3. **Vendor image named by the model's own git / HF repo docs** — for non-official
   checkpoints, follow what the model publisher actually tests against.
4. **`vllm/vllm-openai`** official — fallback. Best upstream provenance but lacks
   the GB10 / NVFP4 / FlashInfer work, so it is not a default here.

Two standing rules on top:

- **Immutable tags only.** No `:latest`, no floating `:nightly`. Digest pins are
  allowed but note sparkrun 0.3.10 fails to ship digest-pinned images to the
  worker, so a dated tag is usually the right form.
- **A verified recipe's image must carry provenance labels** — either
  `dev.sparkrun.*` or OCI `org.opencontainers.image.*`. If it does not, mirror it
  into spark-arena so it does.

## Why that order is also the secure order

| Tier | Provenance available |
|---|---|
spark-arena | `dev.sparkrun.vllm-hash`, `vllm-version`, `flashinfer-hash`, `source-digest`, `source-tag`, `repo-commit` — fully reconstructible |
official vLLM | `ai.vllm.build.commit`, buildkite build URL, OCI source repo |
eugr direct | **no build labels at all** — digest pinnable, contents opaque without running it |
vendor per-model | varies; mostly none |

Consuming eugr through spark-arena's rebuild is what turns an opaque image into a
documented one. That is the security argument for tier 2 sitting below tier 1
rather than beside it.

## Local images: what they actually contain

Read out of the images, not inferred from their names.

| Image | Real vLLM | Built | Verdict |
|---|---|---|---|
`vllm-node:latest` | 0.28.1rc1.dev486+gd875ff5ba | 2026-09-07 | **not a local build** — a pull of `eugr/spark-vllm` re-tagged; shares its image ID. No build labels. |
`vllm-node-tf5:latest` | 0.23.1rc1.dev197+g01192139b | 2026-06-19 | stale, no provenance |
`sparkarena/spark-vllm-docker:mxfp4` | 0.1.dev12774+g459541683 | 2026-02-03 | **8 months old, untagged main. Delete or rebuild.** |
`vllm/vllm-openai:nightly-aarch64` | 0.30.1rc1.dev193+gddd6fbca1 | 2026-09-26 | official pipeline, good labels |
`ghcr.io/spark-arena/dgx-vllm-eugr-nightly:20260927` | 0.30.1rc1.dev220+g24c9772d1 | 2026-09-27 | **best available** — full label chain, real rc tag |
`ghcr.io/spark-arena/...-b12x:20260926` | 0.1.dev21510+g1794dcf18 | 2026-09-26 | full labels but vLLM is untagged main, so no CVE baseline |

The genuine build sources are `~/workspace/llm/spark-vllm-docker` (eugr fork) and
`~/workspace/projects/spark-vllm-docker` (a3refaat fork). Both currently carry
uncommitted local modifications.

## Findings, worst first

1. **`glm-5.3-flash-nvfp4-tp2.yaml` (row 13) is unrunnable.** Its image
   `mia/glm53-flash-spark:mm-ray-v1` is neither on disk nor pullable from any
   registry. Repoint it at `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks`, which
   is pullable.
2. **`sparkarena/spark-vllm-docker:mxfp4`** holds vLLM 0.1.dev from February —
   eight months of unpatched surface in a 24 GB image.
3. **The b12x line runs untagged main** (`0.1.dev21510`), so no release baseline
   exists for advisory comparison. The non-b12x `:20260927` at `0.30.1rc1` is the
   better default wherever a recipe does not specifically need b12x.
4. **One floating tag remains:** `ghcr.io/miaai-lab/mia-vllm-gb10-linear-b12x:latest`.
   Upstream publishes no fixed tag, so mirroring is the only durable fix.
5. **All 11 vendor images are single-maintainer GHCR repos with no mirror.** Any
   can disappear. Mirroring the ones behind verified recipes into spark-arena is
   the highest-value long-term action and promotes those recipes to tier 1.

Pullability at audit time: 22 of 23 recipe images were local or pullable; the one
exception is finding 1.

## Implementation status (2026-10-01)

| # | Finding | Status |
|---|---|---|
| 1 | row 13 image dead | **Documented, not patched.** Blocked on two counts, not one: the image was a local-only tag never published, AND `LibertAIDAI/GLM-5.3-Flash-NVFP4` is a 7.8 KB stub with no weights. The pullable MiaAI tags are all EXL3 builds, which serve row 32's quant, not this NVFP4 Ray build, so there is no like-for-like swap. Recipe now carries an UNRUNNABLE banner pointing at row 32. Fixing it properly needs an NVFP4-Ray image from the publisher plus a ~200 GB download. |
| 2 | `sparkarena/spark-vllm-docker:mxfp4` on vLLM 0.1.dev from February | **Done.** Deleted. Unreferenced since the gpt-oss-120b recipe was dropped, and re-pullable from Docker Hub, so reversible. Docker layer sharing meant little disk came back. |
| 3 | b12x line on untagged main | **Partly done.** `qwen3.8-27b-uncensored-nvfp4-tp1` moved to the non-b12x `:20260927` at vLLM 0.30.1rc1 and is now verified on it. Remaining b12x recipes need per-recipe testing, since some genuinely need the b12x loader. |
| 4 | floating `:latest` tag | **Done.** `qwen3.6-35b-a3b-nvfp4-unofficial-tp1` now pins `ghcr.io/miaai-lab/mia-vllm-gb10-linear-b12x@sha256:19627342…`. The ghcr tag list confirms upstream publishes only `latest`, so a digest is the only immutable handle. Safe because the recipe is single-node, so sparkrun 0.3.10's digest-ship defect on workers does not apply. |
| 5 | mirror vendor images into spark-arena | **BLOCKED — needs credentials.** `~/.docker/config.json` has auth for `nvcr.io` only; there is no GHCR push credential on this box, so nothing can be mirrored. Supply a GHCR token with `write:packages` for the target org and this becomes a scripted job. |

### Note on reclaiming disk by deleting images
Docker shares layers, so the sizes in `docker images` are not additive and
deleting a 24 GB image often returns almost nothing. Measure with `df`, not with
the image list.
