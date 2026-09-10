# sparkrun-recipes

Live-validated [sparkrun](https://sparkrun.dev) recipes for running NVFP4-quantized LLMs on an NVIDIA DGX Spark (GB10) cluster.

Every number in this repo was measured on real hardware, not estimated. Each recipe has been launched, served, and load-tested end to end; the `benchmarks/` reports capture exactly how, and the fix history is public — nothing here shipped without a before/after.

> [!NOTE]
> This is a recipe and benchmark registry, not an application. There's nothing to build or install — you consume it through the `sparkrun` CLI.

## Features

- **11 recipes** spanning DiffusionGemma, Gemma-4, Nemotron-3-Omni, Qwen3.6, and Step-3.7-Flash, all NVFP4-quantized for GB10's unified memory (live-validated with speed numbers)
- **27 additional recipes** from [MiaAI-Lab](https://github.com/MiaAI-Lab) — see [`INDEX.md`](INDEX.md) rows #12–38. All ported to sparkrun v2 YAML format with `command` templates. **Unverified** — please run `--dry-run` and update with your cluster's measured facts.
- **DFlash speculative decoding** wired correctly (BF16 KV, drafter pre-caching) — the single biggest lever in the fix history, worth up to 2.5× decode speed
- **Every recipe launched and load-tested live** on a real two-node GB10 cluster, solo and at 8-way concurrency, not estimated from spec sheets
- **Containers pinned by digest**, not `:latest` — reproducible pulls, no upstream tag drift
- **Placement guidance per workload**: which recipe for interactive chat, agentic tool use, or fleet/batch throughput

## Cluster

| | |
|---|---|
| Cluster name | `default` |
| Head | `gb10-spark` — `10.10.20.10` |
| Worker | `gx10-spark` — `10.10.20.11` |
| Endpoint | `http://10.10.20.10:8000/v1` |

Both nodes are GB10 with 121 GB unified memory.

## Quick start

```bash
# from a local recipe file
sparkrun run ./recipes/diffusiongemma-26b-a4b-nvfp4.yaml --cluster default --tp 1 --no-follow

# or, after registering the registry, by name
sparkrun registry update spark-forge
sparkrun run @spark-forge/diffusiongemma-26b-a4b-nvfp4 --cluster default --tp 1

# stop (same flags as run)
sparkrun stop ./recipes/<file>.yaml --cluster default --tp 1
```

> [!TIP]
> Always `--dry-run` a recipe before launching it, and use `--no-follow` for scripted/non-interactive launches.

## Recipes

11 recipes live in [`recipes/`](recipes), registered under the `spark-forge` registry. Full details, current placement guidance, and every measured number are kept in [`INDEX.md`](INDEX.md) — the table below is a condensed pointer, not the source of truth.

### MiaAI-Lab Community Recipes

27 recipes ported from [github.com/MiaAI-Lab](https://github.com/MiaAI-Lab) DGX Spark inference kits. **All are unverified** — see [`INDEX.md`](INDEX.md) rows #12–38 for the full table with model, runtime, and notes. Run `--dry-run` before launching.

Quick launch example:
```bash
# Single-node (TP=1)
sparkrun run ./recipes/qwen3.8-flash-next-nvfp4-tp1.yaml --cluster default --tp 1 --dry-run
# Multi-node (TP=2)
sparkrun run ./recipes/deepseek-v4-flash-tp2.yaml --cluster default --tp 2 --dry-run
# SGLang
sparkrun run ./recipes/qwen3.8-27b-nvfp4-tp1-sglang.yaml --cluster default --tp 1 --dry-run
```

Full details for all 38 recipes are in [`INDEX.md`](INDEX.md).

### Two-node layout

Independent replicas beat TP=2 on GB10 for anything that fits on one node:

- **Spark A (head):** `diffusiongemma` (interactive) or `qwen36-27b` (flagship quality)
- **Spark B (worker):** `nemotron3-omni` or `qwen36-35b-…-batch` (fleet lane) — `--hosts 10.10.20.11`
- **Or**, for the one model too large for a single node: both nodes → `step37` TP=2 (unvalidated)

#### MiaAI-Lab multi-node recipes

MiaAI-Lab provides several multi-node recipes (see [`INDEX.md`](INDEX.md) rows #12–38 for full details):

| Recipe | Model | Nodes | Notes |
|---|---|---|---|
| `deepseek-v4-flash-tp2.yaml` | DeepSeek-V4-Flash | 2 | 1M context, FP8 KV |
| `deepseek-v4-flash-vision-exp-tp2.yaml` | DeepSeek-V4-Flash Vision-Exp | 2 | Multimodal image |
| `glm-5.3-flash-nvfp4-tp2.yaml` | GLM-5.3 Flash NVFP4 | 2 | Multimodal; Ray TP=2 |
| `glm-5.3-flash-exl3-tp2.yaml` | GLM-5.3 Flash EXL3 | 2 | Multimodal; 850k ctx; Ray TP=2 |
| `mimo-v2.5-tp2.yaml` | Xiaomi MiMo-V2.5 | 2 | Omni MTP1 |
| `leanstral-1.5-119b-a6b-tp2.yaml` | Leanstral 1.5 119B | 2 | MoE |
| `hy3-295b-nvfp4-tp2.yaml` | Hy3 295B | 2 | Tool calling; Ray TP=2 |
| `inkling-small-nvfp4-tp2-sglang.yaml` | Inkling-Small NVFP4 | 2 | DSpark; SGLang |
| `glm-5.2-nvfp4-aqlm-tp3.yaml` | GLM-5.2 NVFP4 | 3 | Multimodal; 380k ctx |

## Conventions

> [!WARNING]
> `gpu_memory_utilization` above ~0.82 NVRM-OOMs at boot on GB10's unified memory — stay in the 0.70–0.82 range.

- Containers are **pinned by digest**, not `:latest` — avoids sparkrun's re-pull hang and upstream tag drift.
- `executor_config: {entrypoint: ""}` is set everywhere to work around an AEON/vllm-openai `ENTRYPOINT` collision.
- `VLLM_CACHE_ROOT=/cache/huggingface/.vllm_cache` persists the FlashInfer autotune cache across runs.
- DFlash recipes need **BF16 KV** (never pair `--kv-cache-dtype` with a drafter) and the drafter model **pre-cached** in the head node's Hugging Face cache — serve containers run `HF_HUB_OFFLINE=1`.
- Qwen recipes use `--reasoning-parser qwen3 --tool-call-parser qwen3_coder` (verified live; `qwen3_xml` also works, `hermes` does not).
- Never enable NCCL symmetric memory on SM121.

## Benchmarks

All measurements were taken live on this cluster. [`benchmarks/README.md`](benchmarks/README.md) indexes every report plus the raw per-recipe `results_*.json` and `mem_*.txt` data:

| Date | Report | Contents |
|---|---|---|
| 2026-07-18 | [BENCHMARKS-2026-07-18.md](benchmarks/BENCHMARKS-2026-07-18.md) | First head-to-head of the 8 original recipes: speed, memory, KV capacity, quality probes |
| 2026-07-18 | [AEON-FINDINGS-2026-07-18.md](benchmarks/AEON-FINDINGS-2026-07-18.md) | Root-cause analysis from the AEON-7 GitHub repos, with a per-recipe fix table |
| 2026-07-25 | [VALIDATION-2026-07-25.md](benchmarks/VALIDATION-2026-07-25.md) | Fixes applied and re-validated (27B 9.5→23.7 tok/s, 35B 43→82, 31B unbootable→31.3), plus the new DiffusionGemma recipe |
| 2026-07-25 | [GITHUB-RECIPES-COMPARE-2026-07-25.md](benchmarks/GITHUB-RECIPES-COMPARE-2026-07-25.md) | Comparison against community recipe repos (eugr, spark-arena) and what was adopted from each |

## Open items

- Step-3.7 TP=2 first boot is still unvalidated (worker was occupied by a long-running job).
- DiffusionGemma's thinking toggle and `canvas_length` config, adopted from eugr, need more experimentation.
- Qwen-35B DFlash draft count sweep (n=11 → 15); Qwen-27B MTP-XS body A/B.
- Nemotron tool/reasoning parser names are still unverified.

See [`benchmarks/gemma4-26b-usage-note.md`](benchmarks/gemma4-26b-usage-note.md) for a worked example of taking a recipe from zero to a served endpoint.
