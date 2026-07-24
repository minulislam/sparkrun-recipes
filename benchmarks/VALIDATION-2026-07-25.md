# Recipe fixes applied + live-validated (2026-07-25)

All changes from `AEON-FINDINGS-2026-07-18.md` are now applied to `recipes/` and
live-validated on gb10-spark (10.10.20.10), one model at a time. The worker
(10.10.20.11) was running a pre-existing 44-hour UI-launched job the whole time
and was not touched. Raw harness outputs: `results_*-dflash.json`,
`results_diffusiongemma-26b.json`; memory captures: `mem_*.txt`.

## Results — before vs after

| Recipe | 07-18 (as shipped) | 07-25 (fixed) | Change |
|---|---|---|---|
| qwen36-27b (DFlash n=10) | 9.5 tok/s c=1, 69 8-way | **23.7 tok/s c=1** (TTFT 0.34 s, prefill 1682, 8-way 87.8) | **2.5× c=1** |
| qwen36-35b (DFlash n=11) | 43.4 tok/s c=1, 224 8-way | **82 tok/s c=1** (TTFT 0.12 s, prefill 4486, 8-way 148.6) | **1.9× c=1**, but 8-way −34% |
| gemma4-31b (dedicated container) | **unbootable** (NVFP4_AWQ rejected) | **31.3 tok/s c=1** (TTFT 0.27–0.39 s, prefill 1623, 8-way 113.8) | boots + 2.8× AEON's drafterless 11 |
| diffusiongemma-26b (NEW) | — | **~358 tok/s c=1** (TTFT 1.2–1.6 s, prefill 2278, 8-way 126.3) | fastest c=1 model in the fleet |
| step37 (unified image + modelopt) | phantom image | offline-validated only | TP=2 boot untested — needs both nodes; worker busy |

Memory (from vLLM logs):

| Model | Loaded | KV capacity | Concurrency at max_model_len |
|---|---|---|---|
| qwen36-27b + drafter | 29.31 GiB | 497,137 tok | 3.79× @ 131,072 |
| qwen36-35b + drafter | 22.69 GiB | 1,119,076 tok | 4.27× @ 262,144 |
| gemma4-31b + drafter | 22.51 GiB | 61,960 tok | 0.95× @ 65,536 → recipe capped to 61,440 |
| diffusiongemma-26b | 17.96 GiB | 1,154,675 tok | 35.24× @ 32,768 |

Boot times (cold, weights cached): qwen27b 743 s, qwen35b 370 s, gemma31b 465 s
(including its container pull), diffusiongemma 232 s.

## Reading the numbers

- **Qwen-27B at 23.7, not AEON's 38–56**: their band is per-category peaks on the
  lighter `…-Multimodal-NVFP4-MTP-XS` body; ours is the heavy body under greedy
  thinking-heavy probes. Still 2.5× our drafterless baseline. Switching bodies
  remains the documented next step if more speed is wanted.
- **DFlash trades aggregate for latency**: 35B 8-way fell 224 → 148.6 (draft
  overhead at concurrency). 27B 8-way *rose* (69 → 87.8) because its drafterless
  baseline was so slow. Placement rule: DFlash recipes for interactive lanes;
  for batch fleets consider dropping the `--speculative-config` line via
  `-o`-style overrides or a variant recipe (nemotron remains the 8-way champion
  at 265).
- **Parsers verified working**: Qwen thinking now lands in the `reasoning` field
  (this fork's name for it), fixing the 07-18 thinking-leak / strict-JSON
  failures. Note for harnesses: count `delta.reasoning` too when measuring.
- **Gemma-31B**: the dedicated container ships **vLLM 0.20.1** (not 0.24) with
  the NVFP4_AWQ loader patch; all our 0.24-era flags happen to work on it.
  Pinned by digest `6986488e…`. KV reality at 0.82 utilization is 61,960 tokens
  — AEON's advertised 65,536 max_model_len doesn't quite fit one full request,
  so the recipe caps at 61,440.
- **DiffusionGemma** (`nvidia/diffusiongemma-26B-A4B-it-NVFP4`, 18 GB, cached on
  the head): the unified AEON image serves the `diffusion_gemma` arch out of the
  box. Diffusion parallel decoding makes it the fastest single-stream model we
  have (~358 tok/s) but concurrency barely scales (126 aggregate @ 8-way) and
  TTFT is ~4× the AR models. Output quality on probes: correct code, correct
  reasoning, near-strict JSON — but every response starts with a literal
  "thought" marker + thinking text (no reasoning parser for this arch yet).

## Operational finds

1. **sparkrun serve containers run `HF_HUB_OFFLINE=1`** — an uncached DFlash
   drafter fails boot with "Invalid repository ID or local directory" (first
   qwen27b launch died this way). Drafters/second models MUST be pre-cached.
   No hf CLI on the hosts; use a one-off container:
   `docker run --rm --network host -v /home/devops/.cache/huggingface:/cache/huggingface -e HF_HOME=/cache/huggingface --entrypoint python3 <image> -c "from huggingface_hub import snapshot_download; snapshot_download('<repo>')"`
2. **Digest pins work**: every pinned launch skipped the `:latest` re-pull hang
   and went straight to serve. The 31B container was pulled once via `:latest`,
   then pinned to its RepoDigest.
3. **Uplink recovered** vs 07-18: HF CDN 14–40 MB/s, ghcr healthy (31B container
   pulled in minutes). The drafter/weight downloads that were blocked are done:
   head now caches all three z-lab drafters + diffusiongemma.
4. **`VLLM_CACHE_ROOT=/cache/huggingface/.vllm_cache`** added to all AEON
   recipes; all 07-25 boots were cold (first run with the new path), so the
   warm-restart benefit (~13 min → ~2 min autotune) is expected but not yet
   observed — check the next launch.
5. Bench harness gotcha: this fork streams thinking as `delta.reasoning`
   (not `reasoning_content`); bench.py updated accordingly.

## Still open

- Step-3.7 TP=2 first boot (needs both nodes idle).
- Qwen-27B MTP-XS body A/B.
- Nemotron parser names remain unverified.
- DiffusionGemma "thought"-marker stripping / future reasoning parser.
