# What we got wrong — AEON-7 GitHub cross-check (2026-07-18)

Sources: [AEON-7/vllm-ultimate-dgx-spark](https://github.com/AEON-7/vllm-ultimate-dgx-spark),
[Qwen3.6-27B-…-DFlash](https://github.com/AEON-7/Qwen3.6-27B-AEON-Ultimate-Uncensored-DFlash),
[Qwen3.6-35B-A3B-heretic-NVFP4-DFlash](https://github.com/AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4-DFlash),
[Gemma-4-31B-Uncensored-NVFP4-DFlash](https://github.com/AEON-7/Gemma-4-31B-Uncensored-NVFP4-DFlash).
These explain every anomaly in `BENCHMARKS-2026-07-18.md`.

## 1. Qwen3.6-27B at 9.5 tok/s — we benchmarked AEON's *stock baseline*, not their recipe

AEON's own numbers: stock vanilla vLLM ≈ **10.5 tok/s**; with DFlash ≈ **38–56 tok/s** by
category. Our recipe ships with `--speculative-config` **commented out** ("drafter id
unverified") — so 9.5 tok/s is exactly the expected no-DFlash number. The "~50 tok/s" in
INDEX.md was always a DFlash figure. Now verified from their repos:

- Drafter: **`z-lab/Qwen3.6-27B-DFlash`** (3.3 GB, 5-layer SWA, public).
- **`num_speculative_tokens: 10`** — their n=8/10/12/15 sweep found n=10 optimal on Spark;
  **n=12 is crash-correlated** (Torch-Inductor device-side asserts). Our commented block said 10 — fine.
- Add **`--mamba-cache-dtype float32`** (better GDN recurrent state, higher acceptance);
  leave `--mamba-block-size` unset; leave drafter attention backend default;
  do **not** set `--kv-cache-dtype` (non-causal DFlash needs BF16 KV).
- Parser names verified: **`--reasoning-parser qwen3 --tool-call-parser qwen3_coder`**
  (fixes the thinking-leak / strict-JSON failures we measured).
- They use `--max-num-batched-tokens 32768` (ours: 16384) and `VLLM_USE_FLASHINFER_SAMPLER=1`.
- Body choice: our 26 GB compressed-tensors `-NVFP4` body works, but their benchmarked Spark
  path is the 21 GB **`-Multimodal-NVFP4-MTP-XS`** body (`--quantization modelopt`) + DFlash —
  DFlash on the XS body beat the heavy body by ~18% TPOT in their A/B.

## 2. Our env var did nothing — removed upstream in v0.24.0

Recipes set `VLLM_NVFP4_GEMM_BACKEND=flashinfer-cutlass`. **v0.24.0 removed that env var**
(and `VLLM_USE_FLASHINFER_MOE_*`); the replacement is `--linear-backend flashinfer_cutlass` /
`--moe-backend cutlass`. On our v0.24.0-maxsafe image the env was silently ignored.
(Benign for Gemma-26B/Qwen-27B — checkpoints with per-input global scales auto-select CUTLASS —
but the recipe's intent no longer executes. Caution: do NOT force `flashinfer_cutlass` on
checkpoints lacking those scales; it crashes them.)

## 3. Qwen3.6-35B-A3B at 43 tok/s — same DFlash omission

Their measured numbers with drafter **`z-lab/Qwen3.6-35B-A3B-DFlash`** (905 MB, public,
8-layer full-attention): **~97 tok/s average single-stream** (75–124 by category), ~740–800
tok/s aggregate at c=32–64. Config: `num_speculative_tokens: 11`, no attention-backend
override, no mamba flags needed. Our 43.4 tok/s is simply the drafterless rate.

## 4. Gemma-26B — we got this one right

Our 76.8 tok/s matches AEON's current-image single-stream (~71–73; their 144–202 figures are
v0.23-era *category peaks* — coding/extraction — and c≥16 aggregates). Recipe already carries
the verified drafter, `flash_attn` drafter backend, BF16 KV. No change needed.

## 5. Gemma-31B boot failure — wrong container, and it was never going to work

**Correction to BENCHMARKS-2026-07-18.md:** not image drift. Our cached image
(`0.24.0+aeon.sm121a.dflash`) is the 2026-07-08 `v0.24.0-maxsafe` build — same era the
recipes were validated. The real cause: the Deckard checkpoint is quantized as
**`quant_algo=NVFP4_AWQ`**, which the unified image's vLLM ModelOpt loader does not accept —
on *any* build. AEON ships a **dedicated container** for this model:
`ghcr.io/aeon-7/gemma-4-31b-uncensored-nvfp4-dflash:latest` — with an NVFP4_AWQ loader patch
(pre_quant_scale registration + NaN block-scale scrub), gemma4 parsers, and DFlash k=15 via
`z-lab/gemma-4-31B-it-DFlash`. Their numbers on it: **38.8 tok/s c=1** (vs 11 stock — so
INDEX.md's "~12–14 tok/s" was the no-DFlash baseline), 427 tok/s aggregate at c=32.
Recipe fix: swap container, mount the drafter, keep `gpu_memory_utilization≈0.82`,
`max_model_len 65536`, `max_num_batched_tokens 32768`. This also means the recipe's 07-08
"live-validated" status could not have included a boot-to-ready check.

## 6. Step-3.7 — the placeholder image was never needed

The unified image's validated-models table lists
`AEON-7/Step-3.7-Flash-AEON-Ultimate-Abliterated-NVFP4` as 🟡 "expected to work" with
**`--quantization modelopt`** — on `aeon-vllm-ultimate:latest` itself. The recipe's
`vllm-openai:stepfun37` placeholder should just become the unified image. Caveats from their
docs: **TP=2 is wired in but untested upstream** (they have one Spark; we have two), and
**never enable NCCL symmetric memory on SM121**.

## 7. Operational finds

- **Cold-start**: FlashInfer FP4 autotune costs ~13 min cold; mounting a persistent
  `-v …:/root/.cache/vllm` warms restarts in ~2 min. Our sparkrun launches always start cold
  (fresh containers, ready in 290–520 s with cache in the HF dir only) — worth adding a
  vllm-cache volume to the recipes.
- **Image pinning**: current `:latest` = `:2026-07-16-v0.25.1` (MRv2 lm_head fix); our cached
  build = `:2026-07-08-v0.24.0-maxsafe` (rollback tag). Recipes should pin dated tags —
  avoids both the sparkrun `:latest` re-pull hang and silent behavior changes.
- The v0.25.x notes flag nothing that would change our measured ranking: their own 0.24→0.25
  fleet A/B is throughput-parity.

## Recipe changes this implies (not yet applied)

| Recipe | Change |
|---|---|
| `qwen36-27b-aeon-ultimate-nvfp4` | Enable DFlash (`z-lab/Qwen3.6-27B-DFlash`, n=10), add `--mamba-cache-dtype float32`, uncomment parsers as `qwen3`/`qwen3_coder`, drop dead `VLLM_NVFP4_GEMM_BACKEND` env, raise `max_num_batched_tokens` to 32768; consider MTP-XS body |
| `qwen36-35b-a3b-heretic-nvfp4` | Enable DFlash (`z-lab/Qwen3.6-35B-A3B-DFlash`, n=11), parsers `qwen3`/`qwen3_coder`, drop dead env |
| `gemma4-31b-deckard-heretic-nvfp4` | Switch container to `ghcr.io/aeon-7/gemma-4-31b-uncensored-nvfp4-dflash:latest`, add drafter `z-lab/gemma-4-31B-it-DFlash` |
| `step37-flash-…-tp2` | Container → `ghcr.io/aeon-7/aeon-vllm-ultimate:<dated tag>`, `--quantization modelopt` |
| all AEON recipes | Pin dated image tags; add persistent vllm-cache volume |

Expected effect: Qwen-27B ≈ 9.5 → 35–55 tok/s; Qwen-35B ≈ 43 → 90–100 tok/s; Gemma-31B
unbootable → ~39 tok/s; Step-3.7 launchable. Drafters are small (0.9–3.3 GB) but must be
downloaded (uplink currently throttled) and DFlash recipes need the drafter present on the
serving node.
