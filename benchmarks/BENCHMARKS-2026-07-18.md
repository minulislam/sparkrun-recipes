# spark-forge recipe benchmarks — live head-to-head (2026-07-18)

Measured on **gb10-spark** (head, 10.10.20.10), one recipe at a time, via the OpenAI
endpoint from the devops workstation. Harness: `bench.py` (this directory holds the raw
`results_*.json` + `mem_*.txt`). All AEON recipes ran on the **cached** unified image
`ghcr.io/aeon-7/aeon-vllm-ultimate@sha256:b47f2ce2…` (vLLM `0.24.0+aeon.sm121a.dflash`)
— see "Image drift" below for why that matters.

Method per model: 3× streamed 320-tok generations (median TTFT / decode), one ~2.7-3.1k-token
prefill probe, 8 concurrent 256-tok requests, and 3 quality probes at temperature 0
(code task, chickens-and-rabbits with a required `ANSWER:` line, strict-JSON-only output).

## Results

| Recipe | Ready | Load (GiB / s) | TTFT | Decode 1-stream | Prefill | 8-way agg | KV cache | Quality probes |
|---|---|---|---|---|---|---|---|---|
| `qwen36-27b-aeon-ultimate-nvfp4` | 520 s | 25.9 / 141 | 0.17 s | **9.5 tok/s** | 1,850 tok/s | 69 tok/s | 1.03M tok (3.9× @262k) | code ✓, answer ✗ (truncated mid-thinking), JSON ✗ |
| `gemma4-26b-aeon-vllm` (MoE+DFlash) | 325 s | 16.8 / 122 | 0.10 s | **76.8 tok/s** | 5,840 tok/s | 156 tok/s | 1.12M tok (4.3× @262k) | code ✓, answer ✓, JSON ✓ |
| `qwen36-35b-a3b-heretic-nvfp4` (MoE) | 340 s | 21.9 / 141 | 0.06 s | **43.4 tok/s** | 4,914 tok/s | **224 tok/s** | 3.07M tok (11.7× @262k) | code ✓, answer ✓, JSON ✗ (thinking leaks) |
| `nemotron3-nano-omni-aeon-nvfp4` | 290 s | 20.9 / 125 | 0.06 s | **72.7 tok/s** | 5,393 tok/s | **265 tok/s** | 8.58M tok (42.9× @200k) | code ✓, answer ✓, JSON ✗ (thinking leaks) |
| `gemma4-12b-k4-nvfp4-fp8` (dense) | 480 s | 9.1 / 45 | 0.10 s | 21.7 tok/s | 4,240 tok/s | 162 tok/s | 0.74M tok (5.6× @131k) | code ✓, answer ✓, JSON ✓ |
| `gemma4-31b-deckard-heretic-nvfp4` | — | — | — | **boot failure** | — | — | — | — |
| `gemma4-26b-stock-vllm` | — | — | — | **blocked** (image absent) | — | — | — | — |
| `step37-flash-…-nvfp4-tp2` | — | — | — | **blocked** (image absent) | — | — | — | — |

"Ready" = launch → first successful `/v1/models` (includes engine init + CUDA graph capture; weights all came from local HF cache).

## What this changes vs INDEX.md's spec-sheet numbers

- **The flagship Qwen-27B decodes at 9.5 tok/s, not ~50.** Confirmed by vLLM's own engine
  logs, so it's not a harness artifact. Worse, it's a *thinker*: at temp 0 it spent the whole
  600-token budget "thinking" and never emitted the required answer line. As configured today
  it is the slowest, least usable recipe of the five that boot. **Root cause found (see
  `AEON-FINDINGS-2026-07-18.md`): the recipe ships with DFlash speculative decoding commented
  out — 9.5 tok/s matches AEON's published no-DFlash stock baseline (~10.5); the ~50 tok/s
  claim was always a DFlash number.**
- **Best all-rounder: `gemma4-26b-aeon-vllm`** — fastest single-stream (77 tok/s), fastest
  prefill, cleanest instruction-following (only model besides 12B to pass strict-JSON), loads
  in 17 GiB.
- **Best for concurrent/agent fleets: `nemotron3-nano-omni`** — 265 tok/s aggregate, 8.58M-token
  KV cache (~43 concurrent full-context requests), near-best TTFT, plus it's the only omni
  (audio) model. Caveat: reasoning text leaks into `content` (parser not configured).
- **`qwen36-35b-a3b` is the mid MoE workhorse** — 43 tok/s single, 224 tok/s aggregate, 3M-token
  KV cache, and it *does* reach correct answers through its thinking.
- **`gemma4-12b` is not "fastest"** single-stream (21.7 tok/s — dense decode is bandwidth-bound);
  its value is the 9 GiB footprint (leaves ~85 GiB free for a second model) and clean outputs.
- **Reasoning-parser flags matter**: both Qwens and Nemotron emit chain-of-thought into
  `content`. The recipes have `--reasoning-parser` lines commented out pending verified names —
  enabling them is the single highest-value recipe improvement this benchmark surfaced.

## Failures & blockers (with unblock paths)

1. **`gemma4-31b-deckard-heretic-nvfp4` does not boot on the unified image — and never could**
   (corrected from an earlier "image drift" hypothesis; the cached image is in fact the
   validated 2026-07-08 `v0.24.0-maxsafe` build): the Deckard checkpoint is quantized as
   `quant_algo=NVFP4_AWQ`, which the unified image's ModelOpt loader rejects on any build.
   AEON ships a dedicated container for this model
   (`ghcr.io/aeon-7/gemma-4-31b-uncensored-nvfp4-dflash:latest`) with the NVFP4_AWQ loader
   patch + DFlash — see `AEON-FINDINGS-2026-07-18.md` §5 for the recipe fix.
2. **`gemma4-26b-stock-vllm` blocked**: pinned image `vllm/vllm-openai@sha256:9eff9734…` exists
   on neither node and the lab's internet was throttled to ~0.7 MB/s all session. Unblock:
   pull when the uplink recovers (image ~10 GB+).
3. **`step37-flash-…-tp2` blocked**: container `vllm-openai:stepfun37` (a local-only tag) exists
   on neither node — it appears to have been pruned since the 07-08 validation. Unblock:
   rebuild/re-import that image, then rerun with `--tp 2`; the 116 GB of weights are still
   cached on the head (worker would need them distributed too).

## Operational gotchas found this session

- **sparkrun re-pulls `:latest` tags even when cached** (`containers/registry.py ensure_image`)
  and the launch *waits* on that pull — with ghcr throttled this stalled launches indefinitely
  with no error, just "pending: image pull". **Workaround (used for all runs above): pass
  `--image ghcr.io/aeon-7/aeon-vllm-ultimate@sha256:<digest>`** — digest/non-latest refs that
  exist locally skip the pull entirely.
- **The worker (gx10-spark) has no AEON images and had no AEON model caches.** The Gemma 12B +
  26B HF caches (~25 GB) were rsynced to it over the CX7 RoCE link this session (that works
  well); the 45 GB container image was not (blocked from raw docker save/load; use sparkrun's
  own push distribution or pull when the uplink recovers).
- nvidia-smi reports `[N/A]` for memory on GB10; use vLLM's "Model loading took" log line and
  host `free -g` instead (captured in `mem_*.txt`).

## Suggested placement (updates INDEX.md's suggestion)

- **Spark A (head):** `nemotron3-nano-omni` for agent fleets / omni, or `gemma4-26b-aeon` for
  the best interactive single-user experience.
- **Spark B (worker):** `gemma4-26b-aeon` or `gemma4-12b` (caches already seeded) — after the
  AEON image reaches the worker.
- **Do not deploy `qwen36-27b` as the flagship** until the 9.5 tok/s decode and the
  thinking-truncation behavior are resolved.
