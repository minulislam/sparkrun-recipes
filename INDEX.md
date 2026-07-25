# gb10-lab sparkrun recipes — index (DGX Spark: head gb10-spark 10.10.20.10 / worker gx10-spark 10.10.20.11)

> **Launch basics (re-verified live 2026-07-25):** cluster is **`default`**
> (`dgxlab` does not exist), global `ssh.user=devops`, single node =
> `--tp 1` (`--solo` is deprecated). Endpoint: `http://10.10.20.10:8000/v1`.
> Always `--dry-run` first; always `--no-follow` for scripted launches.
> **DFlash drafters must be pre-cached** — serve containers run
> `HF_HUB_OFFLINE=1` (see `benchmarks/VALIDATION-2026-07-25.md` §Operational).

All speed numbers below are **measured on this cluster** (2026-07-18 baseline +
2026-07-25 post-fix validation, greedy decoding, stdlib harness —
`benchmarks/README.md` indexes the full reports).

| # | Recipe file | Model | Loaded | c=1 tok/s | 8-way | Modality | Placement | Use for |
|---|---|---|---|---|---|---|---|---|
| 1 | `diffusiongemma-26b-a4b-nvfp4.yaml` | DiffusionGemma-26B-A4B (NVIDIA NVFP4) | 18.0 GiB | **358** | 126 | text (+vision base) | 1 node | **Fastest interactive** (diffusion decoding; TTFT ~1.5 s; "thought"-marker quirk) |
| 2 | `gemma4-26b-aeon-vllm.yaml` | Gemma-4-26B-A4B AEON NVFP4 + DFlash | 16.8 GiB | 76.8 | 156 | text + vision | 1 node | **Interactive agents / tools** — clean strict-JSON |
| 3 | `nemotron3-nano-omni-aeon-nvfp4.yaml` | Nemotron-3-Nano-Omni NVFP4 | 20.9 GiB | 72.7 | **265** | text+image+audio+video | 1 node | **Fleet / batch champion**; only audio model |
| 4 | `qwen36-35b-a3b-heretic-nvfp4.yaml` | Qwen3.6-35B-A3B heretic NVFP4 + DFlash n=11 | 22.7 GiB | **82** | 149 | text + vision | 1 node | Interactive mid-MoE, 262K ctx |
| 5 | `qwen36-35b-a3b-heretic-nvfp4-batch.yaml` | same, drafterless batch twin | 21.9 GiB | 43.4 | **224** | text + vision | 1 node | Batch/fleet lane of #4 |
| 6 | `qwen36-27b-aeon-ultimate-nvfp4.yaml` | Qwen3.6-27B AEON NVFP4 + DFlash n=10 | 29.3 GiB | 23.7 | 88 | text + vision | 1 node | **Flagship quality**, 0/100 refusal |
| 7 | `qwen36-27b-aeon-colocate.yaml` | same, 0.40 GPU co-location profile | ~30 GiB | — | — | text + vision | shares 1 node | Second endpoint beside #2 (port 8001) |
| 8 | `gemma4-31b-deckard-heretic-nvfp4.yaml` | Gemma-4-31B DECKARD NVFP4_AWQ + DFlash k=15 | 22.5 GiB | 31.3 | 114 | text + vision | 1 node | Quality-critical dense (dedicated container, vLLM 0.20.1) |
| 9 | `gemma4-12b-k4-nvfp4-fp8.yaml` | Gemma-4-12B K4 NVFP4-FP8 | 9.1 GiB | 21.7 | 162 | text + vision | 1 node | Smallest footprint; leaves room for a neighbor |
| 10 | `step37-flash-aeon-abliterated-nvfp4-tp2.yaml` | Step-3.7-Flash abliterated NVFP4 (198B MoE) | ~124 GB | untested | — | text + vision | **2 nodes TP=2** | Frontier; TP=2 boot still unvalidated |
| 11 | `gemma4-26b-stock-vllm.yaml` | Gemma-26B on stock vLLM image | — | untested | — | text + vision | 1 node | No-DFlash fallback for #2 |

## Launch

```bash
# interactive default
sparkrun run ./recipes/diffusiongemma-26b-a4b-nvfp4.yaml --cluster default --tp 1 --no-follow
# fleet default
sparkrun run ./recipes/nemotron3-nano-omni-aeon-nvfp4.yaml --cluster default --tp 1 --no-follow
# stop (same flags as run)
sparkrun stop ./recipes/<file>.yaml --cluster default --tp 1
```

By registry name (after `sparkrun registry update gb10-lab`):
`sparkrun run @gb10-lab/<recipe-name> --cluster default --tp 1`

## Two-node layout (independent replicas beat TP=2 on GB10)

- **Spark A (head):** `diffusiongemma` (interactive) or `qwen36-27b` (flagship quality)
- **Spark B (worker):** `nemotron3-omni` or `qwen36-35b-…-batch` (fleet lane) — `--hosts 10.10.20.11`
- **Or** both nodes → `step37` TP=2 (once validated)

## Conventions (all live-verified)

- Containers **pinned by digest** — avoids sparkrun's `:latest` re-pull hang and
  upstream tag drift. Unified AEON image = `@sha256:b47f2ce2…`
  (`:2026-07-08-v0.24.0-maxsafe`, vLLM `0.24.0+aeon.sm121a.dflash`).
- `executor_config: {entrypoint: ""}` everywhere (AEON/vllm-openai ENTRYPOINT collision).
- `VLLM_CACHE_ROOT=/cache/huggingface/.vllm_cache` persists FlashInfer autotune.
- DFlash needs **BF16 KV** (never `--kv-cache-dtype` with a drafter) and the
  drafter **pre-cached** in the head's HF cache.
- Qwen parsers: `--reasoning-parser qwen3 --tool-call-parser qwen3_coder`
  (tool_calls parse verified live; `qwen3_xml` also works, `hermes` does not).
- GB10 memory: 0.70–0.82 `gpu_memory_utilization`; 0.85 NVRM-OOMs at boot.
- Never enable NCCL symmetric memory on SM121.

## Documents

- `benchmarks/README.md` — index of all benchmark/validation reports + raw data
- `benchmarks/GITHUB-RECIPES-COMPARE-2026-07-25.md` — how these recipes compare
  to the GitHub recipe repos (eugr, spark-arena) and what we adopted
- `gemma4-26b-usage-note.md` — usage notes for the Gemma-26B endpoint

## Open items

- Step-3.7 TP=2 first boot (worker currently occupied by a long-running job);
  when testing, try eugr-style `max_model_len 262144` and 0.8 utilization.
- DiffusionGemma thinking toggle (`--default-chat-template-kwargs`) and
  `--diffusion-config canvas_length` experiments (adopted from eugr — see the
  compare report).
- Qwen-35B DFlash n=11 → 15 sweep; Qwen-27B MTP-XS body A/B.
- Nemotron tool/reasoning parser names still unverified.
