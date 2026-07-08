# AEON‑7 NVFP4 sparkrun recipes — index (DGX Spark, head 10.10.20.10 / worker 10.10.20.11)

> **Verified launch (this Mac, 2026-07-01):** single-node -> `sparkrun run ./<recipe>.yaml --cluster dgxlab --solo`; Step-3.7 -> `sparkrun run ./step37-...yaml --cluster dgxlab --tp 2`. A bare `--hosts <ip>` SSHes as the wrong global user `agenticos` and fails (`run` has no `--user`; `--cluster dgxlab` carries the `devops` user).


Seven recipes, one per model selected as best‑for‑GB10. All single‑node on the head **except Step‑3.7**, which is tensor‑parallel across both Sparks. Specs come from the on‑Mac report (`AEON-7_DGX-Spark_uncensored_model_recommendations.md`); serving conventions reuse the **verified** Gemma‑4‑26B card (container, NVFP4 flags, `triton_attn`, parsers, DFlash).

**Always `--dry-run` first** to see the rendered command before launching.

| # | Recipe file | Model | Footprint | Speed (GB10) | Modality | Placement | Use it for |
|---|---|---|---|---|---|---|---|
| 1 | `qwen36-27b-aeon-ultimate-nvfp4.yaml` | Qwen3.6‑27B‑AEON‑Ultimate‑NVFP4 | 26 GB / ~30 GB | ~50 tok/s | text + vision | 1 node | **Flagship.** Highest quality, 0/100 refusal, production‑validated |
| 2 | `gemma4-26b-aeon-vllm.yaml` | Gemma‑4‑26B‑A4B‑NVFP4 (MoE) | 15.3 GB / 16.25 GB | 50 → **1,430 @128** | text (+vision*) | 1 node | **Fast agent fleets / max concurrency** (DFlash, verified) |
| 3 | `qwen36-35b-a3b-heretic-nvfp4.yaml` | Qwen3.6‑35B‑A3B‑heretic‑NVFP4 (MoE) | 21 GB / ~22 GB | **91** / 729 @64 | text + vision | 1 node | Mid MoE with vision + reasoning + 1M ctx (5/100 refusal) |
| 4 | `nemotron3-nano-omni-aeon-nvfp4.yaml` | Nemotron‑3‑Nano‑Omni‑NVFP4 | ~22 GB / ~24 GB | ~71 tok/s | **text+image+audio+video** | 1 node | **Omni** — the only audio‑capable model |
| 5 | `gemma4-12b-k4-nvfp4-fp8.yaml` | Gemma‑4‑12B‑K4‑NVFP4‑FP8 | 9.3 GB / ~10 GB | ~250+ @16 | text + vision | 1 node | **Smallest + fastest**; leaves room for a 2nd model |
| 6 | `gemma4-31b-deckard-heretic-nvfp4.yaml` | Gemma‑4‑31B‑DECKARD‑NVFP4 (dense) | 20.5 GB / ~21 GB | ~12–14 tok/s | text + vision | 1 node | Quality‑critical dense answers (slow decode) |
| 7 | `step37-flash-aeon-abliterated-nvfp4-tp2.yaml` | Step‑3.7‑Flash‑NVFP4 (198B MoE VLM) | ~124 GB | frontier | text + vision | **2 nodes (TP=2)** | Maximum capability; dedicates both Sparks |

> A simpler no‑DFlash fallback for model #2 also exists: `gemma4-26b-stock-vllm.yaml`.

## One‑line launch commands (run from the Mac)

```bash
# 1 — Qwen3.6 27B flagship
sparkrun run ./qwen36-27b-aeon-ultimate-nvfp4.yaml   --cluster dgxlab --solo --dry-run
# 2 — Gemma 26B MoE (fast)
sparkrun run ./gemma4-26b-aeon-vllm.yaml             --cluster dgxlab --solo --dry-run
# 3 — Qwen3.6 35B-A3B MoE
sparkrun run ./qwen36-35b-a3b-heretic-nvfp4.yaml     --cluster dgxlab --solo --dry-run
# 4 — Nemotron Omni (audio/vision)
sparkrun run ./nemotron3-nano-omni-aeon-nvfp4.yaml   --cluster dgxlab --solo --dry-run
# 5 — Gemma 12B (small/fast)
sparkrun run ./gemma4-12b-k4-nvfp4-fp8.yaml          --cluster dgxlab --solo --dry-run
# 6 — Gemma 31B dense (quality)
sparkrun run ./gemma4-31b-deckard-heretic-nvfp4.yaml --cluster dgxlab --solo --dry-run
# 7 — Step-3.7 198B (BOTH nodes, TP=2)
sparkrun run ./step37-flash-aeon-abliterated-nvfp4-tp2.yaml --cluster dgxlab --tp 2 --dry-run
```
Drop `--dry-run` to actually launch. Endpoint is OpenAI‑compatible on the head: `http://10.10.20.10:8000/v1/...`. Ctrl+C detaches from logs (never kills the job). Stop with `sparkrun stop ./<recipe>.yaml` (add `--tp 2` for Step‑3.7).

## Suggested two‑node layout (independent replicas beat TP=2 on GB10)
- **Spark A (10.10.20.10):** flagship `qwen36-27b` (quality) — or `nemotron3-omni` if you need audio.
- **Spark B (10.10.20.11):** `gemma4-26b` (fast agent fleet) — run it with `--hosts 10.10.20.11`.
- **Or** dedicate both to `step37` (TP=2) when you want the one frontier model.

## What's verified vs. flagged

**Verified** (from the live Gemma‑4‑26B card last session + the on‑Mac report): the sparkrun recipe schema; the unified AEON container claim (`ghcr.io/aeon-7/aeon-vllm-ultimate:latest`); NVFP4 conventions (`--quantization compressed-tensors`, `--attention-backend triton_attn` for Gemma, `gemma4` tool/reasoning parsers, BF16‑KV‑with‑DFlash, the NVFP4 env vars); each model's footprint, context, modality, tok/s, and single‑node‑vs‑TP2 placement.

**Flagged — confirm against each model card (web_fetch to huggingface.co was timing out this session, and the HF MCP tools were disallowed):**
- **Exact container image/tag per model.** I used the unified AEON image for all AEON models; the report also references family‑specific images (`vllm-spark-q36*`, `vllm-spark-gemma4-nvfp4*`, `vllm-nemotron-omni-aeon-ultimate`). **Step‑3.7's StepFun image (`vllm-openai:stepfun37`) registry/tag is a placeholder — set the real one before running.**
- **DFlash/EAGLE drafter repo ids** for Qwen‑27B, Qwen‑35B, and Gemma‑31B (spec‑decode left commented/optional; only Gemma‑26B's drafter `z-lab/gemma-4-26B-A4B-it-DFlash` is verified).
- **Quantization flag for ModelOpt builds** (Nemotron, Gemma‑31B, Step‑3.7) — left to vLLM auto‑detect; add `--quantization modelopt` if it mis‑detects.
- **Tool/reasoning parser names** for the non‑Gemma models (Qwen/Nemotron) — left commented.
- **Step‑3.7 context length** — `65536` placeholder; set the card's value.
- 1M‑context YaRN flags for Qwen‑35B (commented), and whether end‑to‑end NVFP4 + vision is validated on Gemma‑26B (card calls it untested).

## Sources
- On‑Mac report: `AEON-7_DGX-Spark_uncensored_model_recommendations.md`
- Verified serving card: https://huggingface.co/AEON-7/Gemma-4-26B-A4B-it-Uncensored-NVFP4
- sparkrun recipe format: https://sparkrun.dev/recipes/format/
