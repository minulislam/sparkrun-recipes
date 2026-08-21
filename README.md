# sparkrun-recipes

Live-validated [sparkrun](https://sparkrun.dev) recipes for running NVFP4-quantized LLMs on an NVIDIA DGX Spark (GB10) cluster.

Every number in this repo was measured on real hardware, not estimated. Each recipe has been launched, served, and load-tested end to end; the `benchmarks/` reports capture exactly how, and the fix history is public — nothing here shipped without a before/after.

> [!NOTE]
> This is a recipe and benchmark registry, not an application. There's nothing to build or install — you consume it through the `sparkrun` CLI.

## Features

- **11 recipes** spanning DiffusionGemma, Gemma-4, Nemotron-3-Omni, Qwen3.6, and Step-3.7-Flash, all NVFP4-quantized for GB10's unified memory
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
sparkrun registry update gb10-lab
sparkrun run @gb10-lab/diffusiongemma-26b-a4b-nvfp4 --cluster default --tp 1

# stop (same flags as run)
sparkrun stop ./recipes/<file>.yaml --cluster default --tp 1
```

> [!TIP]
> Always `--dry-run` a recipe before launching it, and use `--no-follow` for scripted/non-interactive launches.

## Recipes

11 recipes live in [`recipes/`](recipes), registered under the `gb10-lab` registry. Full details, current placement guidance, and every measured number are kept in [`INDEX.md`](INDEX.md) — the table below is a condensed pointer, not the source of truth.

| Recipe | Model | c=1 tok/s | 8-way | Best for |
|---|---|---:|---:|---|
| `diffusiongemma-26b-a4b-nvfp4` | DiffusionGemma-26B-A4B (NVFP4) | **358** | 126 | Fastest interactive (diffusion decoding) |
| `gemma4-26b-aeon-vllm` | Gemma-4-26B-A4B AEON NVFP4 + DFlash | 76.8 | 156 | Interactive agents / tools, clean strict-JSON |
| `nemotron3-nano-omni-aeon-nvfp4` | Nemotron-3-Nano-Omni NVFP4 | 72.7 | **265** | Fleet / batch champion, only audio-capable model |
| `qwen36-35b-a3b-heretic-nvfp4` | Qwen3.6-35B-A3B heretic NVFP4 + DFlash | **82** | 149 | Interactive mid-MoE, 262K context |
| `qwen36-35b-a3b-heretic-nvfp4-batch` | same, drafterless batch twin | 43.4 | **224** | Batch/fleet lane of the 35B |
| `qwen36-27b-aeon-ultimate-nvfp4` | Qwen3.6-27B AEON NVFP4 + DFlash | 23.7 | 88 | Flagship quality, 0/100 refusal |
| `qwen36-27b-aeon-colocate` | same, 0.40 GPU co-location profile | — | — | Second endpoint beside the 27B (port 8001) |
| `gemma4-31b-deckard-heretic-nvfp4` | Gemma-4-31B DECKARD NVFP4_AWQ + DFlash | 31.3 | 114 | Quality-critical dense (dedicated vLLM 0.20.1 container) |
| `gemma4-12b-k4-nvfp4-fp8` | Gemma-4-12B K4 NVFP4-FP8 | 21.7 | 162 | Smallest footprint |
| `step37-flash-aeon-abliterated-nvfp4-tp2` | Step-3.7-Flash abliterated NVFP4 (198B MoE) | untested | — | Frontier, requires 2 nodes (TP=2) |
| `gemma4-26b-stock-vllm` | Gemma-26B on stock vLLM image | untested | — | No-DFlash fallback |

### Two-node layout

Independent replicas beat TP=2 on GB10 for anything that fits on one node:

- **Spark A (head):** `diffusiongemma` (interactive) or `qwen36-27b` (flagship quality)
- **Spark B (worker):** `nemotron3-omni` or `qwen36-35b-…-batch` (fleet lane) — `--hosts 10.10.20.11`
- **Or**, for the one model too large for a single node: both nodes → `step37` TP=2 (unvalidated)

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

See [`gemma4-26b-usage-note.md`](gemma4-26b-usage-note.md) for a worked example of taking a recipe from zero to a served endpoint.
