# spark-forge sparkrun recipes — index (DGX Spark: head gb10-spark 10.10.20.10 / worker gx10-spark 10.10.20.11)

> **Launch basics (re-verified live 2026-07-25):** cluster is **`default`**
> (`dgxlab` does not exist), global `ssh.user=devops`, single node =
> `--tp 1` (`--solo` is deprecated). Endpoint: `http://10.10.20.10:8000/v1`.
> Always `--dry-run` first; always `--no-follow` for scripted launches.
> **DFlash drafters must be pre-cached** — serve containers run
> `HF_HUB_OFFLINE=1` (see `benchmarks/VALIDATION-2026-07-25.md` §Operational).
> **Multi-node comm env:** pinned in the `dgx-pair` cluster definition
> (`~/.config/sparkrun/clusters/dgx-pair.yaml` → `env:`), not in recipes:
> `NCCL_IB_HCA=rocep1s0f1,roceP2p1s0f1`, `NCCL_SOCKET_IFNAME=enp1s0f1np1,enP2p1s0f1np1`,
> `GLOO_SOCKET_IFNAME=enp1s0f1np1`, `TP_SOCKET_IFNAME=enp1s0f1np1`. The f0 CX7
> ports show link-up but carry no IP and have no path to the peer; sparkrun's
> live probe (still in 0.3.10) lists them first and hands them to both NCCL and
> the Gloo/TCPStore socket groups (`Unable to find address for: enp1s0f0np0`).
> Cluster env overrides the probe; recipe-level pins trigger the
> `managed-comm-env` validator warning instead.

All speed numbers below are **measured on this cluster** (2026-07-18 baseline +
2026-07-25 post-fix validation, greedy decoding, stdlib harness —
`benchmarks/README.md` indexes the full reports).

| # | Recipe file | Model | Loaded | c=1 tok/s | 8-way | Modality | Placement | Use for |
|---|---|---|---|---|---|---|---|---|
| 1 | `diffusiongemma-26b-a4b-nvfp4.yaml` | DiffusionGemma-26B-A4B (NVIDIA NVFP4) | 18.0 GiB | **358** | 126 | text (+vision base) | 1 node | **Fastest interactive** (diffusion decoding; TTFT ~1.5 s; "thought"-marker quirk) |
| 2 | `gemma4-26b-aeon-vllm.yaml` | Gemma-4-26B-A4B AEON NVFP4 + DFlash | 16.8 GiB | 76.8 | 156 | text + vision | 1 node | **Interactive agents / tools** — clean strict-JSON |
| 3 | `nemotron3-nano-omni-aeon-nvfp4.yaml` | Nemotron-3-Nano-Omni NVFP4 | 20.9 GiB | 72.7 | **265** | text+image+audio+video | 1 node | **Fleet / batch champion**; only audio model |
| 4 | `qwen36-35b-a3b-heretic-nvfp4.yaml` | Qwen3.6-35B-A3B heretic NVFP4 + DFlash n=11 | 22.7 GiB | **82** | 149 | text + vision | 1 node | Interactive mid-MoE, 262K ctx |
| 5 | `qwen36-35b-a3b-heretic-nvfp4-batch.yaml` | same, drafterless batch twin | 21.9 GiB | 43.4 (41.5 fleet 2026-09-27) | **224** (193 → 107 at 32k depth, fleet) | text + vision | 1 node | Batch/fleet lane of #4 — the only recipe that holds up at 8-way × 32k context (`benchmarks/FLEET-2026-09-27.md`) |
| 6 | `qwen36-27b-aeon-ultimate-nvfp4.yaml` | Qwen3.6-27B AEON NVFP4 + DFlash n=10 | 29.3 GiB | 23.7 | 88 | text + vision | 1 node | **Flagship quality**, 0/100 refusal |
| 7 | `qwen36-27b-aeon-colocate.yaml` | same, 0.40 GPU co-location profile | ~30 GiB | 8.8 (fleet 2026-09-27) | 56.0 (→ **5.9** at 32k depth) | text + vision | shares 1 node | Second endpoint beside #2 (port 8001); interactive/short-context only — the 0.40 KV pool collapses at 8-way × 32k (TTFR 117 s) |
| 8 | `gemma4-31b-deckard-heretic-nvfp4.yaml` | Gemma-4-31B DECKARD NVFP4_AWQ + DFlash k=15 | 22.5 GiB | 31.3 | 114 | text + vision | 1 node | Quality-critical dense (dedicated container, vLLM 0.20.1) |
| 9 | `gemma4-12b-k4-nvfp4-fp8.yaml` | Gemma-4-12B K4 NVFP4-FP8 | 9.1 GiB | 21.7 | 162 | text + vision | 1 node | Smallest footprint; leaves room for a neighbor |
| 11 | `gemma4-26b-stock-vllm.yaml` | Gemma-26B on stock vLLM image | — | untested | — | text + vision | 1 node | No-DFlash fallback for #2 |

## MiaAI-Lab Recipes (ported from https://github.com/MiaAI-Lab)

> **⚠️ Unverified by default — but check the row.** These recipes were
> auto-generated from MiaAI-Lab's `start.sh` scripts and ported to sparkrun v2
> YAML format with `command` fields. Many have since been launched and measured:
> **any row whose Notes say `VERIFIED <date>` carries live numbers from this
> cluster** and is no longer unverified. The banner applies only to rows without
> such a note. Run `--dry-run` first on those, then launch, benchmark, and fill
> in the Notes.
> Each file has a `>>>` header block — replace it with your verified facts.
> **Ray-based recipes** (`vLLM-Ray`) need SSH mesh + Ray cluster ports open across all nodes.
> **Weights are a separate question from the recipe**: a row can be correct and
> still unrunnable because its checkpoint is a metadata stub or a partial
> download. `MODELS.md` is the measured inventory of what is actually on each node.

| # | Recipe file | Model | Runtime | Nodes | Quant | Context | Notes |
|---|---|---|---|---|---|---|---|
| 12 | `qwen3.8-flash-next-nvfp4-tp1.yaml` | Mia-AiLab/Qwen3.8-Flash-Next-NVFP4 | vLLM | 1 | NVFP4 | 256k | MTP draft; source-validated by MiaAI-Lab |
| 13 | `glm-5.3-flash-nvfp4-tp2.yaml` | LibertAIDAI/GLM-5.3-Flash-NVFP4 | vLLM-Ray | 2 | NVFP4 | 262k | Multimodal MoE; Ray TP=2 |
| 14 | `deepseek-v4-flash-tp2.yaml` | deepseek-ai/DeepSeek-V4-Flash | vLLM | 2 | FP8 | 1M | MoE; FP8 KV cache |
| 15 | `deepseek-v4-flash-vision-exp-tp2.yaml` | deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | vLLM | 2 | NVFP4 | 1M | Multimodal image; DSpark; nvfp4_ds_mla KV |
| 16 | `qwen3.6-27b-nvfp4-tp1.yaml` | nvidia/Qwen3.6-27B-NVFP4 | vLLM | 1 | NVFP4 | 256k | vLLM nightly aarch64; `executor_config.entrypoint: ""` added 2026-09-27 (official images bake ENTRYPOINT) |
| 17 | `qwen3.6-35b-a3b-nvfp4-tp1.yaml` | unsloth/Qwen3.6-35B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 256k | — |
| 18 | `qwen3.8-27b-nvfp4-tp1.yaml` | unsloth/Qwen3.8-27B-NVFP4 | vLLM | 1 | NVFP4 | 256k | **MEASURED 2026-09-27**: 11.2 tok/s c=1, 56.7 at 8-way (32.6 at 32k depth), 1.21M KV tokens, loads in 128 s; needs `executor_config.entrypoint: ""` (image bakes ENTRYPOINT) |
| 19 | `gemma-4-31b-it-nvfp4-tp1.yaml` | nvidia/Gemma-4-31B-IT-NVFP4 | vLLM | 1 | NVFP4 | — | MTP; tool calling; thinking; `executor_config.entrypoint: ""` added 2026-09-27 |
| 20 | `gemma-4-26b-a4b-nvfp4-tp1.yaml` | nvidia/Gemma-4-26B-A4B-NVFP4 | vLLM | 1 | NVFP4 | — | Concurrency testing; `executor_config.entrypoint: ""` added 2026-09-27 |
| 21 | `nemotron-labs-3-puzzle-75b-nvfp4-tp1.yaml` | nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4 | vLLM | 1 | NVFP4 | 256k | Hybrid MoE (Mamba+MoE+Attention); MTP k=3 |
| 22 | `muse-glimmer-30b-nvfp4-tp1.yaml` | RedHatAI/Muse-Glimmer-30B-NVFP4 | vLLM | 1 | NVFP4 | 256k | W4A4 variant |
| 23 | `laguna-s-2.1-nvfp4-tp1.yaml` | poolside/Laguna-S-2.1-NVFP4 | vLLM | 1 | NVFP4 | **128k** | 99.7 GB on disk (48-layer/256-expert MoE, not "30B"): loads 93.2 GiB in 605 s; 262k needs more KV than the node has and 0.90 util trips earlyoom — now 0.85 / 131072. **VERIFIED 2026-09-27**: 16.9 tok/s c=1 (15.0 at 32k depth), 46.5 aggregate 8-way at depth 0; the 0.18M-token KV pool (1.34× of 131k) queues 8-way at depth (TTFR 85 s @ 32k) — single-stream/low-concurrency lane |
| 24 | `ling-3.0-flash-int4-tp1-sglang.yaml` | inclusionAI/Ling-3.0-flash-int4 | SGLang | 1 | INT4 | — | DSpark speculative decoding |
| 25 | `ornith-1.5-35b-a3b-nvfp4-tp1.yaml` | spark-ai/Ornith-1.5-35B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 256k | In-checkpoint MTP; b12x |
| 26 | `hy3-295b-nvfp4-tp2.yaml` | kodelow/Hy3-NVFP4-W4A16 | vLLM-Ray | 2 | NVFP4 | — | 295B MoE; tool calling |
| 27 | `leanstral-1.5-119b-a6b-tp2.yaml` | mistralai/Leanstral-1.5-119B-A6B | vLLM | 2 | FP8 | 262k | MoE; enforce_eager |
| 28 | `mimo-v2.5-tp2.yaml` | Xiaomi/MiMo-V2.5 | vLLM-Ray | 2 | FP8 | — | Omni MTP1; NVFP4-KV |
| 30 | `inkling-small-nvfp4-tp2-sglang.yaml` | thinkingmachines/Inkling-Small-NVFP4 | SGLang | 2 | NVFP4 | **1M** | **VERIFIED 2026-09-27** on the MiaAI-Lab champion image (`ghcr.io/drowzeys/inkling-sglang-gb10:kvquant`) + DSpark draft: 32.3 tok/s c=1, 66.9 at 8-way, coherence OK, ready in 385 s; 83.6 GB/rank; only ~4 GB host headroom at mem-fraction 0.85 |
| 32 | `glm-5.3-flash-exl3-tp2.yaml` | Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw | vLLM-Ray | 2 | EXL3 | 850k | Multimodal; Ray TP=2. **BLOCKED 2026-10-06 — partial weights.** The checkpoint is **half downloaded on the head and absent on the worker**: 59 of 120 shards, 81.6 GiB of the 163.7 GiB that `MANIFEST.json` declares (328 files). A tp2 recipe needs it complete on both nodes, so this cannot launch and has never been benchmarked. Finish the download, then stage to the worker with blobs **hardlinked** (sparkrun 0.3.10 self-rsync destroys symlinked blobs — `benchmarks/FLEET-2026-09-27.md` §3). Note `du -sh` on the cache dir is misleading here; see `MODELS.md`. **UNBENCHMARKED** |
| 33 | `qwen3.8-flash-next-nvfp4-tp2-sglang.yaml` | Mia-AiLab/Qwen3.8-Flash-Next-NVFP4 | SGLang | 2 | NVFP4 | 256k | FP8 dense; SGLang speculative |
| 34 | `qwen3.8-27b-nvfp4-tp1-sglang.yaml` | RadixArk/Qwen3.8-27B-NVFP4 | SGLang | 1 | NVFP4 | 256k | DFlash; 8 concurrent |
| 35 | `nemotron-3.5-lightning-30b-a3b-nvfp4-tp1-sglang.yaml` | nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 | SGLang | 1 | NVFP4 | 256k | DSpark; RTX 5090/6000 PRO |
| 36 | `qwen3.6-35b-a3b-nvfp4-unofficial-tp1.yaml` | unsloth/Qwen3.6-35B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 256k | b12x linear attention recipe |
| 37 | `qwen3.8-27b-nvfp4-tp1-alt.yaml` | RadixArk/Qwen3.8-27B-NVFP4 | vLLM | 1 | NVFP4 | 256k | RTX 5090 variant |
| 38 | `step-3.7-flash-nvfp4-tp2-miaai.yaml` | stepfun-ai/Step-3.7-Flash-NVFP4 | vLLM | 2 (TP2) | NVFP4 | 65k | **LAUNCHED 2026-10-01, first boot ever — COHERENT BUT WEDGES.** The recipe shipped with no `container:` at all, so it could never have run; sparkrun validates it anyway because the field is optional. Now pinned to `vllm/vllm-openai:stepfun37` (the base image of upstream's wrapper Dockerfile) with `executor_config.entrypoint: ""`, since the image bakes `ENTRYPOINT ["vllm","serve"]` and ate sparkrun's command on the first attempt. **Good news:** this build answers correctly — the exact prompt that returned `" order 8 3 "` noise on the AEON abliterated build (row 10, now removed) produced correct prose here, so the garbage was the AEON quant, NOT Step-3.7, NVFP4, or this pair. It is a reasoning model and leaks chain-of-thought into `content` with a bare `</think>`; set `--reasoning-parser` before exposing it. **Blocker:** the engine died after 2 requests / 196 generated tokens — decode ~10 tok/s, then 5x `shm_broadcast: no available block in 60s`, then `TimeoutError: RPC call to sample_tokens timed out` -> `EngineDeadError`, API server refusing connections while both containers still read "Up". Same failure class as the AEON build, so **the Step-3.7 TP=2 path is broken on this pair regardless of quant** — the earlier "AEON image is broken" conclusion was too narrow. CUDA graphs captured clean (15 s, 1.74 GiB), so graphs are not the cause; `--enforce-eager`, bf16 KV and NCCL-over-TCP were all already spent on the AEON build and all still hung. Measured: 58.4 GiB/rank (same as AEON), weight load 164.4 s, init engine 82.35 s, KV 30.65 GiB = 2,395,878 tokens (36.56x at 65k), launch wall 342.5 s including the 129 GB worker sync over cx7. Image is from 2026-05-28 (vllm 0.1.dev16944) and no newer `stepfun37` tag exists; a newer vLLM is the only untried lever. Weights now on BOTH nodes, blobs hardlinked, so a retry costs only the boot. **Do not put in a serving rotation** |

Retired 2026-09-26: `deepseek-v4-flash-0731-tp1.yaml` (#31) declared `runtime: exllamav3`, which no
sparkrun release knows, and had no container. Its upstream (MiaAI-Lab/DeepSeek-v4-Flash-One-DGX-Spark)
actually serves the 0xSero EXL3 checkpoint through vLLM + sparkinfer in a docker-compose project with an
image-provided serve script and a weight-coalescing pre-step — port it as a proper vLLM recipe if wanted.

## Third-party Recipes

| # | Recipe file | Model | Runtime | Nodes | Quant | Context | Notes |
|---|---|---|---|---|---|---|---|
| 39 | `qwen38-27b-nvfp4-refusal-dial.yaml` | unsloth/Qwen3.8-27B-NVFP4 | vLLM | 1 | NVFP4 | 64k | Runtime rank-1 refusal projection; needs `pocharlies/vllm-qwen38-rank1` image; port 8101. **MEASURED 2026-09-27**: 19.5 tok/s c=1, 47.4 at 8-way, but only 180k KV tokens — 8-way × 32k collapses to 3.8 tok/s (TTFR 169 s) |
| 41 | `qwen3.8-27b-uncensored-nvfp4-tp1.yaml` | orcarouter/Qwen3.8-27B-Uncensored-NVFP4 | vLLM | 1 | NVFP4 | **262k** (native) | **VERIFIED 2026-10-01 — first boot ever.** Weights were a 669 MB metadata stub until today; 24.69 GB downloaded and checksum-verified. Three fixes were needed first: container off b12x onto `dgx-vllm-eugr-nightly:20260927` (`instanttensor` is only verified on the non-b12x loader here — b12x needs io_uring, which rootless seccomp forbids, same reason row 48 moved to safetensors), util 0.82 -> 0.80 to match row 52, and `--speculative-config` REMOVED because config.json declares no `num_nextn_predict_layers` and the repo ships no draft weights. Startup: weights load in **2.05 s** via instanttensor, 22.36 GiB model, KV 64.47 GiB = **2,029,356 tokens** (7.74x at 262k), init engine 374 s. **Full context proven: needle-in-haystack 21/21 correct at 10/50/90% depth up to 247,670 tokens**, HTTP 400 beyond as expected, no late-context blind spot. **But a 13x prefill cliff sits between 148k and 204k tokens**: 13,248 tok/s peak collapses to ~1,000 and wall goes 12 s -> 369 s; accuracy unaffected and KV is not the constraint, so past ~150k this is batch-only. **Refusal eval (JailbreakBench JBB-Behaviors, 100 harmful + 100 matched benign): 100/100 compliance on BOTH splits, zero refusals in all 10 policy categories**; the one refusal in the padded run is a grader false positive (hedge then complies). Benign compliance with 1,750-char substantive answers is what shows the abliteration is complete rather than the model being damaged. **Correctness measured 2026-10-01: GSM8K 144/150 = 96.0%** (reasoning on) and **MMLU 125/150 = 83.3%** (reasoning off, 0 unparsed) — both in-band for a healthy Qwen3-class 27B, so abliteration cost little or no capability. **Caveat: with the default chat template it reasons past any modest `max_tokens` and returns EMPTY content** — 68% of a 512-token run had no answer at all; callers need a large budget or `enable_thinking: false`. Full writeup: `benchmarks/redteam/RESULTS-qwen3.8-27b-uncensored-2026-10-01.md` |
| 42 | `nex-n2.5-mini-uncensored-nvfp4-tp1.yaml` | orcarouter/Nex-N2.5-mini-Uncensored-NVFP4 | vLLM | 1 | NVFP4 | 256k | Abliterated Nex-N2.5 mini MoE (24 GB), vision; gated repo; UNVERIFIED |
| 43 | `deepseek-v4-flash-vision-uncensored-tp2.yaml` | orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | vLLM | 2 | FP4+FP8 | **1M** | **VERIFIED 2026-09-26** — eugr b12x image (the anemll one cannot load the vision tower), fp8 KV mandatory, safetensors loader; ~57 tok/s; needs the pair to itself (a 33 GB co-tenant silently collapses the context to 576 tokens) |
| 44 | `qwen3.8-flash-next-uncensored-nvfp4-tp2.yaml` | orcarouter/Qwen3.8-Flash-Next-Uncensored-NVFP4 | vLLM | 2 | NVFP4 | **256k** (native) | 183.5 GB weights of which the 102 GB shard is a **bf16 per-layer-embedding table** → `VLLM_PLE_TABLE_MEMORY=ram` maps 47.7 GiB/rank of host memory, so util is 0.50; `--hf-overrides` renames its `qwen_sparse_attention` layers for the eugr image; safetensors loader (b12x needs io_uring). **UNFIT on dgx-pair 2026-09-27** (3 utilizations measured): the bf16 PLE table in RAM is 47.7 GiB/rank of the same unified pool → fixed non-KV ≈ 93 GiB/rank; util 0.40 loads but KV = **−44.5 GiB**, 0.50/0.81 kill the worker rank at startup. Use row 48 (base, nvfp4 PLE, VERIFIED) or fix seccomp/io_uring — see recipe banner + `benchmarks/FLEET-2026-09-27.md` §5; gated repo. 2026-09-28: the `VLLM_PLE_CPU_OFFLOAD=1` escape path (util 0.70, 131k ctx) was tried as a variant — **failed to serve**, rank-0 `TimeoutError: port` after 1872 s. PLE CPU-offload did not rescue it on this image; row 48 stays the only working Flash-Next route |
| 45 | `glm-5.3-flash-uncensored-nvfp4-tp2.yaml` | orcarouter/GLM-5.3-Flash-Uncensored-NVFP4 | vLLM | 2 | NVFP4 | 32k | 205 GB weights — marginal on this 2-node pair (~2.7 GB/node for KV at 0.87); eugr b12x nightly; gated repo; UNVERIFIED |
| 46 | `deepseek-v4-flash-vision-uncensored-ep2.yaml` | orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | vLLM | 2 | FP4+FP8 | 256k | #43 + `--enable-expert-parallel` (EP=2 for the MoE layers, attention stays TP2), FP8 KV; gated repo; UNVERIFIED |
| 47 | `deepseek-v4-flash-vision-uncensored-coder-tp2.yaml` | orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | vLLM | 2 | FP4+FP8 | 256k | #43 tuned for CLI coding agents: thinking off, `kv_cache_bytes` 12 GiB (0.44M KV tokens, 1.7 × 262k), readiness 3600 s for the ~93 GiB/node safetensors cold load. **VERIFIED 2026-09-27** after `max_num_batched_tokens` 8192 → 2048 (at 8192 the 8k-depth prefill livelocked the worker node twice): 30.2 tok/s c=1 (27.3 at 32k depth, spec decode), 45.6 aggregate 8-way; prefill 388 tok/s at 8k depth (TTFR 5.3 s). KV pool 1.24M tokens — see `benchmarks/FLEET-2026-09-27.md` |
| 49 | `minimax-m2.7-nvfp4-atlas-ep2.yaml` | lukealonso/MiniMax-M2.7-NVFP4 | **Atlas** | 2 (EP=2) | NVFP4 | 12k | **VERIFIED 2026-09-27** — fork of `@atlas/minimax-m2.7-nvfp4-ep2`: 27.7 tok/s c=1 (18.6 at 8k depth, TTFT 13 s), no batching win (`max_batch_size 1`). Needs `--cluster dgx-pair-ep`, the Aug-27 Atlas image, and three memory knobs — `benchmarks/FLEET-2026-09-27.md` §4b |
| 50 | `minimax-m2.7-nvfp4-vllm-tp2.yaml` | nvidia/MiniMax-M2.7-NVFP4 | vLLM | 2 (TP2) | NVFP4 | 196k | NEW 2026-09-27, copy of `@official/minimax-m2.7-nvfp4-vllm` — the vLLM route for M2.7 (compare row 49). Weights on both nodes. Community-verified class: ~24-27 tok/s decode on 2 Sparks. **VERIFIED 2026-09-29 at FULL 196,608 context** (util 0.82): prefill 13,565 tok/s @ 64k depth (TTFT 4.8s), decode ~250 tok/s, needle-recall correct at 64 & 64k. The pass-8 "zero cells" was NOT a model fault — it was a comm-stack failure (head f1 ports had lost IPv4 → Gloo/NCCL/RoCE all broke; fixed via static IPv4 + GID-table alignment on the head, see FLEET §7-8) plus a benchmark harness under-provisioning max_tokens. Also needs autotune disabled (`--no-enable-flashinfer-autotune`, hangs 70min+ on sm121) and mbt 2048. Known quirk: some prompt shapes return empty generation (prefill OK, 0 output tokens) — infra sound, model/parser follow-up. This is now a real M2.7 route alongside row 49 (Atlas EP2) |
| 52 | `qwen3.8-27b-fp8-mtp-tp1.yaml` | Qwen/Qwen3.8-27B-FP8 | vLLM | 1 | FP8 | 262k | NEW 2026-09-27, copy of `@official/qwen3.8-27b-fp8-mtp-vllm` (MTP spec 3, fp8 KV, FlashInfer). Native-FP8 sibling of rows 39-42. **VERIFIED 2026-09-27**: 12.3 tok/s c=1 (flat to 32k), 73.4 aggregate 8-way — 30 % better batch lane than the NVFP4 build, same c=1 |
| 53 | `glm-4.7-flash-awq-tp1.yaml` | cyankiwi/GLM-4.7-Flash-AWQ-4bit | vLLM | 1 | AWQ4 | 202k | NEW 2026-09-27, copy of `@experimental/glm-4.7-flash-awq-vllm`. eugr's header warns the vLLM path is suboptimal (~40 tok/s expected, MLA patch no longer applies). **VERIFIED 2026-09-27**: 42.2 tok/s c=1, 110 aggregate 8-way, 17.7 GiB load — prediction matched |
| 54 | `nemotron-3-nano-30b-nvfp4-tp1.yaml` | nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 | vLLM | 1 | NVFP4 | 262k | NEW 2026-09-27, copy of `@experimental/nemotron-3-nano-nvfp4-vllm`. Upstream marks it single-node only. **VERIFIED 2026-09-27**: 58.4 tok/s c=1 / 154.6 aggregate 8-way, flat to 32k, 18.9M-token mamba KV (72×) — fastest single-node lane after heretic-35B; the `mods:` plugin launched fine from the registry |
| 56 | `nemotron-3-super-120b-nvfp4-tp2.yaml` | nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 | vLLM | 2 (TP2) | NVFP4 | 262k | NEW 2026-09-27, copy of `@experimental/nemotron-3-super-nvfp4-vllm` (TRITON_ATTN, fp8 KV, mamba cache fp32, trtllm allreduce). **VERIFIED 2026-09-27**: 24.7 tok/s c=1 (community's ~24 reproduced), 40.6 aggregate 8-way, 16.3M-token KV (62×); note an odd c=1 dip to 16.4 at 8k depth (22.6 at 32k) |
| 57 | `north-mini-code-1.0-nvfp4-tp1.yaml` | XanuNetworks/North-Mini-Code-1.0-NVFP4 | vLLM | 1 | NVFP4 | 262k | NEW 2026-10-01, local copy of `@community/north-mini-code-1.0-nvfp4-vllm-XanuNetworks`. Closes one of the six gaps logged in `379aa6f` (no registry carried this model on 2026-09-27; the community registry published one since). Cohere 30B / 3B-active MoE agentic coder, fp8 KV, `cohere_command4` tool + reasoning parsers. Container pinned to `:20260927`. Upstream `pre_exec` pip-installs `cohere_melody` at launch, so the run needs egress; the validator flags this as an inline-script suggestion and it is retained deliberately to stay faithful to the verified upstream recipe. **CORRECTION 2026-10-01: NO WEIGHTS.** The earlier note here said "weights on head only"; that was wrong — `XanuNetworks/North-Mini-Code-1.0-NVFP4` is a 0.5 MB metadata-only cache stub on the head and absent on the worker. Needs a full download before it can run. **UNBENCHMARKED** |
| 58 | `deepseek-v4-flash-nvfp4-atlas-ep2.yaml` | nvidia/DeepSeek-V4-Flash-NVFP4 | **Atlas** | 2 (EP=2) | NVFP4 | 32k | NEW 2026-10-01, local copy of `@atlas/deepseek-v4-flash-nvfp4-ep2`. Closes another `379aa6f` gap. EP=2 is mandatory: the ~153 GB checkpoint exceeds one GB10's 119.7 GB, and DeepSeek-V4 is MQA (`num_key_value_heads=1`) so TP>1 is impossible — do **not** pass `--tp 2`. Needs `--cluster dgx-pair-ep`; `expert_parallel: 2` added locally so sparkrun's fit planner sizes two ranks (same fix as row 49). Container pinned to `ghcr.io/atlas-inf/atlas-gb10:sha-bdcccc2`. **CORRECTION 2026-10-01: NO WEIGHTS ANYWHERE.** The earlier note said "weights are on the head only"; that was wrong — `nvidia/DeepSeek-V4-Flash-NVFP4` is a 0 MB metadata-only cache stub on the head and absent on the worker, so the ~153 GB checkpoint must be downloaded first, then staged on both nodes with the blobs hardlinked (sparkrun 0.3.10 self-rsync destroys symlinked blobs). Atlas reports ~15.5 tok/s decode. **UNBENCHMARKED** |
| 48 | `qwen3.8-flash-next-nvfp4-tp2.yaml` | local-inference-lab/Qwen3.8-Flash-Next-NVFP4 | vLLM | 2 | NVFP4 | **256k** (native) | **VERIFIED 2026-09-27** — local copy of `@eugr/qwen3.8-flash-next-nvfp4-cluster` with the safetensors loader (b12x needs io_uring, blocked by rootless seccomp) and a readiness block: 46–55 tok/s c=1, ~92 at 8-way flat to 32k depth, 2.5M KV tokens, 51.4 GiB/node, ready in 859 s cold |

The orcarouter recipes (#41-46) are abliterated/uncensored builds, one per
[orcarouter](https://huggingface.co/orcarouter/collections) collection; #46 is the
expert-parallel variant of #43. The five HuggingFace repos are **gated with
auto-approval**: the account behind sparkrun's HF token must open each model page once and
click "Agree and access repository", or every download returns 403. Each recipe pins its
HF commit and mirrors the serve flags of the matching base-model recipe in this repo or in
the `@eugr`/`@official` registries.

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
- **Or** both nodes → `minimax-m2.7-nvfp4-vllm-tp2` TP=2 (verified 2026-09-29 at full 196k context)

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

- `CONTEXT.md` — the glossary. What *verified* means here versus *benchmarked*,
  *serves*, *promoted* and *unfit*, and what *complete* / *partial* / *stub*
  mean for a checkpoint. Read it before reporting any coverage number.
- `MODELS.md` — measured inventory of checkpoints on each node (complete /
  partial / metadata-stub), which recipes use each one, and the orphans no
  recipe references. Check this before launching: a correct recipe still fails
  if its weights are a stub.
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

## Uncensored model quality — MEASURED 2026-10-01/02

Nine abliterated checkpoints with weights on disk, same suite each: JailbreakBench
JBB-Behaviors (100 harmful + 100 matched benign), GSM8K n=150, MMLU n=150.
Full writeup and the four findings: `benchmarks/redteam/RANKING-uncensored-2026-10-02.md`.

| # | Recipe | GB | Harmful | Benign | GSM8K | MMLU | avg |
|---|---|---|---|---|---|---|---|
| **1** | `gemma4-26b-aeon-vllm` | 16 | 100% | 100% | **96.7** | 86.0 | **91.3** |
| **2** | `qwen38-27b-nvfp4-refusal-dial` | 23 | 100% | 100%* | 96.0 | 86.0 | **91.0** |
| **3** | `gemma4-12b-k4-nvfp4-fp8` | **9** | 100% | 100% | 96.0 | 84.0 | **90.0** |
| 4 | `qwen3.8-27b-uncensored-nvfp4-tp1` | 25 | 100% | 100% | 96.0 | 83.3 | 89.7 |
| 5 | `qwen36-27b-aeon-ultimate-nvfp4` | 28 | 100% | 100% | 75.3 | **87.3** | 81.3 |
| 6 | `gemma4-31b-deckard-heretic-nvfp4` | 20 | 100% | 99% | 64.7 | 74.0 | 69.3 |
| — | `nemotron3-nano-omni-aeon-nvfp4` | 22 | **93%** | 100% | 92.7 | 73.3 | 83.0 |
| — | `qwen36-35b-a3b-heretic-nvfp4-batch` | 23 | **74%** | 99% | 79.3 | **88.0** | 83.7 |
| — | `deepseek-v4-flash-vision-uncensored-tp2` | 168 | 100% (58/58) | **CRASHED** | — | — | — |

\* benign split reached 59 of 100 before a stage timeout; all 59 complied.
Dashed rows are disqualified: the first two REFUSE a meaningful share of harmful
requests, the third does not survive sustained load.

**Read before picking one:**
- **"Uncensored" has meant three different things here** — compliance spans
  74%–100% across rows the index described identically, and naming does not
  predict it (AEON spans 93–100%; the "heretic" build is the least abliterated).
- **Abliteration quality beats size.** Gemma-4-12B (9 GB) scores 90.0 while
  Gemma-4-31B DECKARD (20 GB) scores 69.3. Bigger is not better.
- **Runtime abliteration (row 39's refusal-dial) preserves capability better**
  than baked abliteration: +2.7 MMLU over the same-family baked model, both at
  full compliance.
- **Base family sets the capability shape**: Qwen3.6 is knowledge-strong and
  math-weak; Gemma-4-26B/12B and Qwen3.8 sit near 96 on math.
- `deepseek-v4-flash-vision-uncensored-tp2` is marked VERIFIED from a short
  benchmark sweep but **crashed under 200 sustained requests** with the pair to
  itself. Verified and production-ready are different claims.

## Open items

- **16 of the 48 models in the HF cache are metadata-only stubs, not downloaded weights.**
  A stub holds config.json and friends and reads as a present model to any `ls` of
  `~/.cache/huggingface/hub`. This has mislead gap analysis more than once, including
  commit 379aa6f's "models with weights on disk" list and two rows in this file on
  2026-10-01. Size the snapshot, do not trust the directory's existence. Current stubs
  include `nvidia/DeepSeek-V4-Flash-NVFP4` (row 58), `XanuNetworks/North-Mini-Code-1.0-NVFP4`
  (row 57), and three of the four GLM-5.3 variants.

- Still recipe-less in all 8 registries (re-checked 2026-10-01): `openai/gpt-oss-20b`,
  `sakamakismile/Huihui-Qwen3.6-27B-abliterated-NVFP4-MTP`, `google/gemma-4-E4B-it`.
  These need custom recipes written and a launch window to verify. The other three from
  `379aa6f` are closed: North-Mini-Code and DeepSeek-V4-Flash-NVFP4 became rows 57-58,
  and Ornith-1.0-35B was deleted from both nodes on 2026-09-29.

- Step-3.7 TP=2 hangs on this pair for BOTH quants. Row 38 booted 2026-10-01 and
  served coherent output, then wedged on a `sample_tokens` RPC timeout after 2
  requests. Only untried lever is a newer vLLM than the 2026-05-28 `stepfun37`
  image; `--enforce-eager`, bf16 KV and NCCL-over-TCP are already spent. Weights
  are staged on both nodes, so a retry costs only the boot. 262144 context is
  untested and pointless until the hang is fixed.
- Row 38 needs a `--reasoning-parser` before it is exposed to clients: it emits
  chain-of-thought into `message.content` and closes with a bare `</think>`.
- DiffusionGemma thinking toggle (`--default-chat-template-kwargs`) and
  `--diffusion-config canvas_length` experiments (adopted from eugr — see the
  compare report).
- Qwen-35B DFlash n=11 → 15 sweep; Qwen-27B MTP-XS body A/B.
- Nemotron tool/reasoning parser names still unverified.
- MiaAI-Lab recipe validation: please run `--dry-run` and update recipe headers
  with your cluster's measured facts (GPU memory, endpoint, throughput, tok/s).
