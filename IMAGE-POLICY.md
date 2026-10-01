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
