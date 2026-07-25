# gb10-lab benchmark & validation documents

All measurements taken live on the `default` cluster (head gb10-spark
10.10.20.10, worker gx10-spark 10.10.20.11 — both GB10, 121 GB unified memory)
with the stdlib harness described in each report. Reports are ordered; each
later one corrects or extends the earlier ones.

| Date | Document | What it is |
|---|---|---|
| 2026-07-18 | [BENCHMARKS-2026-07-18.md](BENCHMARKS-2026-07-18.md) | First head-to-head of the 8 registry recipes as originally shipped: speed (c=1 / prefill / 8-way), memory, KV capacity, quality probes, blockers. Two corrections were later edited in (Qwen-27B slowness = DFlash disabled; Gemma-31B failure = NVFP4_AWQ, not image drift). |
| 2026-07-18 | [AEON-FINDINGS-2026-07-18.md](AEON-FINDINGS-2026-07-18.md) | Root-cause analysis from the AEON-7 GitHub repos: what our recipes got wrong (disabled DFlash, dead env vars, wrong container for 31B, phantom step37 image) + the per-recipe fix table. |
| 2026-07-25 | [VALIDATION-2026-07-25.md](VALIDATION-2026-07-25.md) | The fixes applied + live-validated: before/after table (27B 9.5→23.7, 35B 43→82, 31B unbootable→31.3 tok/s), new DiffusionGemma recipe (~358 tok/s c=1), operational finds (HF_HUB_OFFLINE drafter pre-cache, digest pins, DFlash's aggregate-throughput cost). |
| 2026-07-25 | [GITHUB-RECIPES-COMPARE-2026-07-25.md](GITHUB-RECIPES-COMPARE-2026-07-25.md) | Survey of GitHub sparkrun-recipe repos covering the same models (eugr/spark-vllm-docker, spark-arena community); per-model best-version verdicts and techniques adopted. |

## Raw data

- `results_<label>.json` — harness output per model: streamed TTFT + decode
  tok/s (3 runs), long-context prefill rate, 8-way concurrent aggregate,
  quality-probe transcripts (code / reasoning / strict-JSON).
- `mem_<label>.txt` — vLLM log captures: "Model loading took", "GPU KV cache
  size", "Maximum concurrency" (nvidia-smi reports [N/A] on GB10 — these log
  lines are the ground truth).

## Current placement guidance (post-fix, measured)

| Lane | Pick | Why |
|---|---|---|
| Interactive, fastest | `diffusiongemma-26b-a4b-nvfp4` | ~358 tok/s c=1 (diffusion parallel decoding); TTFT ~1.5 s; no concurrency scaling |
| Interactive, agentic/tools | `gemma4-26b-aeon-vllm` | 76.8 tok/s c=1, clean strict-JSON, DFlash, 1.12M-token KV |
| Fleet / batch | `nemotron3-nano-omni-aeon-nvfp4` | 265 tok/s @ 8-way, 8.58M-token KV (42.9×); only audio-capable model |
| Batch Qwen alternative | `qwen36-35b-a3b-heretic-nvfp4-batch` | 224 tok/s @ 8-way drafterless (DFlash twin drops to 149) |
| Quality-critical dense | `gemma4-31b-deckard-heretic-nvfp4` | 31.3 tok/s c=1 on the dedicated NVFP4_AWQ container |
| Flagship quality | `qwen36-27b-aeon-ultimate-nvfp4` | 23.7 tok/s c=1 with DFlash; 0/100 refusal; vision |
