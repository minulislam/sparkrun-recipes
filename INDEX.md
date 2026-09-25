# spark-forge sparkrun recipes — index (DGX Spark: head gb10-spark 10.10.20.10 / worker gx10-spark 10.10.20.11)

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

## MiaAI-Lab Recipes (ported from https://github.com/MiaAI-Lab)

> **⚠️ Unverified** — these recipes were auto-generated from MiaAI-Lab's `start.sh` scripts
> and ported to sparkrun v2 YAML format with `command` fields.
> Please run `--dry-run` first, then launch, benchmark, and update this table with measured numbers.
> Each file has a `>>>` header block — replace it with your verified facts.
> **Ray-based recipes** (`vLLM-Ray`) need SSH mesh + Ray cluster ports open across all nodes.

| # | Recipe file | Model | Runtime | Nodes | Quant | Context | Notes |
|---|---|---|---|---|---|---|---|
| 12 | `qwen3.8-flash-next-nvfp4-tp1.yaml` | Mia-AiLab/Qwen3.8-Flash-Next-NVFP4 | vLLM | 1 | NVFP4 | 256k | MTP draft; source-validated by MiaAI-Lab |
| 13 | `glm-5.3-flash-nvfp4-tp2.yaml` | LibertAIDAI/GLM-5.3-Flash-NVFP4 | vLLM-Ray | 2 | NVFP4 | 262k | Multimodal MoE; Ray TP=2 |
| 14 | `deepseek-v4-flash-tp2.yaml` | deepseek-ai/DeepSeek-V4-Flash | vLLM | 2 | FP8 | 1M | MoE; FP8 KV cache |
| 15 | `deepseek-v4-flash-vision-exp-tp2.yaml` | deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | vLLM | 2 | NVFP4 | 1M | Multimodal image; DSpark; nvfp4_ds_mla KV |
| 16 | `qwen3.6-27b-nvfp4-tp1.yaml` | nvidia/Qwen3.6-27B-NVFP4 | vLLM | 1 | NVFP4 | 256k | vLLM nightly aarch64 |
| 17 | `qwen3.6-35b-a3b-nvfp4-tp1.yaml` | unsloth/Qwen3.6-35B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 256k | — |
| 18 | `qwen3.8-27b-nvfp4-tp1.yaml` | unsloth/Qwen3.8-27B-NVFP4 | vLLM | 1 | NVFP4 | 256k | RTX 6000 PRO variant |
| 19 | `gemma-4-31b-it-nvfp4-tp1.yaml` | nvidia/Gemma-4-31B-IT-NVFP4 | vLLM | 1 | NVFP4 | — | MTP; tool calling; thinking |
| 20 | `gemma-4-26b-a4b-nvfp4-tp1.yaml` | nvidia/Gemma-4-26B-A4B-NVFP4 | vLLM | 1 | NVFP4 | — | Concurrency testing |
| 21 | `nemotron-labs-3-puzzle-75b-nvfp4-tp1.yaml` | nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4 | vLLM | 1 | NVFP4 | 256k | Hybrid MoE (Mamba+MoE+Attention); MTP k=3 |
| 22 | `muse-glimmer-30b-nvfp4-tp1.yaml` | RedHatAI/Muse-Glimmer-30B-NVFP4 | vLLM | 1 | NVFP4 | 256k | W4A4 variant |
| 23 | `laguna-s-2.1-nvfp4-tp1.yaml` | poolside/Laguna-S-2.1-NVFP4 | vLLM | 1 | NVFP4 | 256k | DFlash speculative decoding |
| 24 | `ling-3.0-flash-int4-tp1-sglang.yaml` | inclusionAI/Ling-3.0-flash-int4 | SGLang | 1 | INT4 | — | DSpark speculative decoding |
| 25 | `ornith-1.5-35b-a3b-nvfp4-tp1.yaml` | spark-ai/Ornith-1.5-35B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 256k | In-checkpoint MTP; b12x |
| 26 | `hy3-295b-nvfp4-tp2.yaml` | kodelow/Hy3-NVFP4-W4A16 | vLLM-Ray | 2 | NVFP4 | — | 295B MoE; tool calling |
| 27 | `leanstral-1.5-119b-a6b-tp2.yaml` | mistralai/Leanstral-1.5-119B-A6B | vLLM | 2 | FP8 | 262k | MoE; enforce_eager |
| 28 | `mimo-v2.5-tp2.yaml` | Xiaomi/MiMo-V2.5 | vLLM-Ray | 2 | FP8 | — | Omni MTP1; NVFP4-KV |
| 29 | `glm-5.2-nvfp4-aqlm-tp3.yaml` | Mia-AiLab/GLM-5.2-NVFP4-AQLM | vLLM | 3 | AQLM | 380k | Multimodal; 380k ctx with MTP |
| 30 | `inkling-small-nvfp4-tp2-sglang.yaml` | thinkingmachines/Inkling-Small-NVFP4 | SGLang | 2 | NVFP4 | — | DSpark; fp4_mx_block16 KV |
| 31 | `deepseek-v4-flash-0731-tp1.yaml` | 0xSero/deepseek-v4-flash-0731-spark | ExllamaV3 | 1 | EXL3 | 384k | Pinned rev 22f28d32 |
| 32 | `glm-5.3-flash-exl3-tp2.yaml` | Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw | vLLM-Ray | 2 | EXL3 | 850k | Multimodal; Ray TP=2 |
| 33 | `qwen3.8-flash-next-nvfp4-tp2-sglang.yaml` | Mia-AiLab/Qwen3.8-Flash-Next-NVFP4 | SGLang | 2 | NVFP4 | 256k | FP8 dense; SGLang speculative |
| 34 | `qwen3.8-27b-nvfp4-tp1-sglang.yaml` | RadixArk/Qwen3.8-27B-NVFP4 | SGLang | 1 | NVFP4 | 256k | DFlash; 8 concurrent |
| 35 | `nemotron-3.5-lightning-30b-a3b-nvfp4-tp1-sglang.yaml` | nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 | SGLang | 1 | NVFP4 | 256k | DSpark; RTX 5090/6000 PRO |
| 36 | `qwen3.6-35b-a3b-nvfp4-unofficial-tp1.yaml` | unsloth/Qwen3.6-35B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 256k | b12x linear attention recipe |
| 37 | `qwen3.8-27b-nvfp4-tp1-alt.yaml` | RadixArk/Qwen3.8-27B-NVFP4 | vLLM | 1 | NVFP4 | 256k | RTX 5090 variant |
| 38 | `step-3.7-flash-nvfp4-tp2-miaai.yaml` | stepfun-ai/Step-3.7-Flash-NVFP4 | vLLM | 2 | NVFP4 | — | Custom container; MTP grafting support |

## Third-party Recipes

| # | Recipe file | Model | Runtime | Nodes | Quant | Context | Notes |
|---|---|---|---|---|---|---|---|
| 39 | `qwen38-27b-nvfp4-refusal-dial.yaml` | unsloth/Qwen3.8-27B-NVFP4 | vLLM | 1 | NVFP4 | 64k | Runtime rank-1 refusal projection; needs `pocharlies/vllm-qwen38-rank1` image; port 8101 |
| 40 | `minimax-m3-v0-nvfp4-reap25.yaml` | sparkarena/Minimax-M3-v0-NVFP4-REAP25 | SGLang | 2 | NVFP4 | 32k | REAP25-pruned MiniMax-M3; weights (175 GB) already staged on both nodes |
| 41 | `qwen3.8-27b-uncensored-nvfp4-tp1.yaml` | orcarouter/Qwen3.8-27B-Uncensored-NVFP4 | vLLM | 1 | NVFP4 | 256k | Abliterated Qwen3.8-27B (25 GB); gated repo; UNVERIFIED |
| 42 | `nex-n2.5-mini-uncensored-nvfp4-tp1.yaml` | orcarouter/Nex-N2.5-mini-Uncensored-NVFP4 | vLLM | 1 | NVFP4 | 256k | Abliterated Nex-N2.5 mini MoE (24 GB), vision; gated repo; UNVERIFIED |
| 43 | `deepseek-v4-flash-vision-uncensored-tp2.yaml` | orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | vLLM | 2 | FP4+FP8 | 256k | 168 GB weights, ~15 GB/node left for KV; container ENTRYPOINT cleared via `executor_config` (2026-09-26); gated repo; UNVERIFIED |
| 44 | `qwen3.8-flash-next-uncensored-nvfp4-tp2.yaml` | orcarouter/Qwen3.8-Flash-Next-Uncensored-NVFP4 | vLLM | 2 | NVFP4 | 64k | 184 GB weights, ~7 GB/node for KV (max_model_len capped at 65536); eugr b12x nightly; replaces the container-less sglang draft; gated repo; UNVERIFIED |
| 45 | `glm-5.3-flash-uncensored-nvfp4-tp2.yaml` | orcarouter/GLM-5.3-Flash-Uncensored-NVFP4 | vLLM | 2 | NVFP4 | 32k | 205 GB weights — marginal on this 2-node pair (~2.7 GB/node for KV at 0.87); eugr b12x nightly; gated repo; UNVERIFIED |
| 46 | `deepseek-v4-flash-vision-uncensored-ep2.yaml` | orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | vLLM | 2 | FP4+FP8 | 256k | #43 + `--enable-expert-parallel` (EP=2 for the MoE layers, attention stays TP2), FP8 KV; gated repo; UNVERIFIED |

The orcarouter recipes (#41-46) are abliterated/uncensored builds, one picked from each
of the [orcarouter](https://huggingface.co/orcarouter/collections) collections (#46 is an
expert-parallel variant of #43). All five HuggingFace repos are **gated with
auto-approval**: open each model page once with the account whose token sparkrun uses and
click "Agree and access repository", or every download returns 403 (done for
`asmminulislam` on 2026-09-26). Each recipe mirrors the container and serve flags of the
matching base-model recipe already in this repo, pins the HF commit, and carries its own
fit note from a `--dry-run` VRAM estimate. Only #43 has been launched so far (2026-09-26:
reached the model download; not yet served).

## Launch

```bash
# interactive default
sparkrun run ./recipes/diffusiongemma-26b-a4b-nvfp4.yaml --cluster default --tp 1 --no-follow
# fleet default
sparkrun run ./recipes/nemotron3-nano-omni-aeon-nvfp4.yaml --cluster default --tp 1 --no-follow
# stop (same flags as run)
sparkrun stop ./recipes/<file>.yaml --cluster default --tp 1
```

By registry name (after `sparkrun registry update spark-forge`):
`sparkrun run @spark-forge/<recipe-name> --cluster default --tp 1`

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
- `benchmarks/gemma4-26b-usage-note.md` — usage notes for the Gemma-26B endpoint

## MiaAI-Lab Conventions

MiaAI-Lab recipes use several **custom container images** (not Spark Arena standard images).
Before launching, check each recipe's `container:` field:
- Pull or build the required image from the source repo.
- **Ray-based recipes** (`vLLM-Ray`): GLM-5.3, MiMo, Hy3, GLM-5.3-EXL3 — need SSH mesh + Ray cluster ports open across all nodes.
- Some recipes require **HuggingFace authentication** — set `HF_TOKEN` in your environment.
- GB10 memory ceiling: `gpu_memory_utilization` in the **0.70–0.85** range is safe; 0.85+ risks NVRM OOM at boot.
- All MiaAI-Lab recipes are **marked UNVERIFIED** — run `--dry-run` first, then launch and update the `>>>` header with your measured cluster facts.

## Open items

- Step-3.7 TP=2 first boot (worker currently occupied by a long-running job);
  when testing, try eugr-style `max_model_len 262144` and 0.8 utilization.
- DiffusionGemma thinking toggle (`--default-chat-template-kwargs`) and
  `--diffusion-config canvas_length` experiments (adopted from eugr — see the
  compare report).
- Qwen-35B DFlash n=11 → 15 sweep; Qwen-27B MTP-XS body A/B.
- Nemotron tool/reasoning parser names still unverified.
- MiaAI-Lab recipe validation: please run `--dry-run` and update recipe headers
  with your cluster's measured facts (GPU memory, endpoint, throughput, tok/s).
