# Serving Gemma‑4‑26B‑A4B‑it‑Uncensored‑NVFP4 on your DGX Spark cluster

Two ready‑to‑run sparkrun recipes, plus the exact commands. **Run everything from the Mac.**

## TL;DR

- **Model:** `AEON-7/Gemma-4-26B-A4B-it-Uncensored-NVFP4` — weights live on **Hugging Face** (the GitHub URL you had is the *container* repo, `github.com/AEON-7/vllm-ultimate-dgx-spark`, not the weights).
- **It runs on ONE Spark, not two.** It's a 26B‑total / ~4B‑active MoE in NVFP4 — 15.3 GB on disk, ~16.25 GB loaded — so it fits with huge KV headroom on a single 128 GB DGX Spark. The vendor's production recipe is literally `--tensor-parallel-size 1`. **`--tp 2` is not warranted** (it'd add NCCL overhead for no gain and isn't the supported path). The head node (`10.10.20.10`) serves; the worker (`10.10.20.11`) stays free for something else.
- **Files:**
  - `gemma4-26b-aeon-vllm.yaml` — **recommended**, max performance (AEON container + DFlash speculative decoding, ~150 tok/s coding).
  - `gemma4-26b-stock-vllm.yaml` — **simplest**, guaranteed‑clean for sparkrun's template engine (stock vLLM, no DFlash, ~47–49 tok/s but higher aggregate throughput).

## How sparkrun recipes work (grounded in the docs)

A recipe is a **YAML file** — `model`, `runtime`, `container`, `command`, plus `defaults`/`env`/`metadata`. You do **not** need a built‑in recipe name; sparkrun's recipe‑discovery explicitly accepts **a local file path** (also URLs, registry names, and `@spark-arena/<id>`). So you can `sparkrun run ./gemma4-26b-aeon-vllm.yaml` directly. `{placeholder}` tokens in `command` are filled from `defaults` and can be overridden at launch with `-o key=value` or the standard flags (`--max-model-len`, `--gpu-mem`, etc.). Source: https://sparkrun.dev/recipes/format/

## Step 1 — (AEON recipe only) pre‑stage the DFlash drafter, once

sparkrun pre‑syncs only the primary `model`. DFlash needs a **second** model. Put it in the head node's HF cache once (sparkrun mounts that cache into the container):

```bash
ssh <DGX_USER>@10.10.20.10 'huggingface-cli download z-lab/gemma-4-26B-A4B-it-DFlash'
```
Skip this entirely if you use the stock recipe.

## Step 2 — verify the rendered command (always do this first)

```bash
# Put the recipe somewhere on the Mac, then dry-run to see the exact docker/vllm command:
sparkrun show ./gemma4-26b-aeon-vllm.yaml          # details + VRAM estimate (should show it fits 1 node)
sparkrun run  ./gemma4-26b-aeon-vllm.yaml --cluster dgxlab --solo --dry-run
```
The `--dry-run` prints what would run **without launching**. Confirm the `--speculative-config '{...}'` JSON rendered intact (see "If DFlash JSON breaks" below).

## Step 3 — launch (head node only)

```bash
# Recommended (AEON + DFlash). --hosts pins it to the head; or omit if dgxlab default is set.
sparkrun run ./gemma4-26b-aeon-vllm.yaml --cluster dgxlab --solo

# OR the simplest path (stock vLLM, no drafter needed):
sparkrun run ./gemma4-26b-stock-vllm.yaml --cluster dgxlab --solo
```
Ctrl+C only detaches from the logs — the model keeps serving.

## Step 4 — hit the OpenAI‑compatible endpoint (on the head, port 8000)

```bash
curl http://10.10.20.10:8000/v1/models

curl http://10.10.20.10:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gemma4-aeon-uncensored",
    "messages": [{"role":"user","content":"Write a Python function that reverses a linked list."}],
    "max_tokens": 512
  }'
```
The AEON recipe also exposes the aliases `gemma4-fast` and `gemma4-deep` (same model, vendor‑provided names). `--reasoning-parser gemma4` splits thinking output into a separate `reasoning_content` field.

## Step 5 — manage it

```bash
sparkrun status                                  # what's running, with logs/stop hints
sparkrun logs  ./gemma4-26b-aeon-vllm.yaml       # re-attach (Ctrl+C safe)
sparkrun stop  ./gemma4-26b-aeon-vllm.yaml       # single-node stop (no --tp needed here)
sparkrun cluster monitor --cluster dgxlab        # live GPU/RAM across nodes
```

## Common overrides

```bash
# Shorter context / more concurrency for throughput benchmarking:
sparkrun run ./gemma4-26b-aeon-vllm.yaml --cluster dgxlab --solo -o max_model_len=32768 -o max_num_seqs=256
# Lower memory headroom (vendor's long-context production profile uses 0.68):
sparkrun run ./gemma4-26b-aeon-vllm.yaml --cluster dgxlab --solo --gpu-mem 0.68
```

## If the DFlash `--speculative-config` JSON breaks templating

The one risk in the AEON recipe is that sparkrun's `{placeholder}` engine could choke on the JSON's `{ }` braces (undocumented interaction — flagged below). If `--dry-run` shows the JSON mangled or `run` errors on it:
1. **Easiest:** use `gemma4-26b-stock-vllm.yaml` instead — fully functional, just no speculative speedup.
2. Or delete the final `--speculative-config ...` line from the AEON recipe (keeps the fast AEON container/kernels, drops only DFlash).
3. Or run the vendor's raw `docker run` from the model card directly on the head node (outside sparkrun).

## Verified vs. unverified

**Verified against the live model card + sparkrun docs (June 2026):**
- Repo id, architecture (Gemma 4 MoE, 26B/~4B active, top‑8/128, 30 layers, multimodal), NVFP4 compressed‑tensors, 15.3 GB disk / 16.25 GB loaded, 262,144 max context, BF16 KV requirement.
- Serving engine = vLLM; flags `--quantization compressed-tensors`, `--attention-backend triton_attn`, `--tool-call-parser gemma4`, `--reasoning-parser gemma4`, the env vars, container `ghcr.io/aeon-7/aeon-vllm-ultimate:latest`, drafter `z-lab/gemma-4-26B-A4B-it-DFlash`, and `--tensor-parallel-size 1` — all from the model card's reference recipe.
- sparkrun recipe schema (fields, file‑path recipes, `{placeholder}` substitution, `min_nodes/max_nodes`, `-o` overrides, `--dry-run`).

**Could NOT verify (test on the hardware):**
- **Whether sparkrun's command‑template engine passes the inline `--speculative-config` JSON braces through untouched.** Always `--dry-run` first; fallback documented above.
- **How the drafter resolves inside the AEON container under sparkrun** — I adapted the vendor's `-v /models/gemma4-dflash` bind‑mount into "reference the drafter by HF id from the mounted HF cache." Grounded in how sparkrun mounts the HF cache, but confirm on first run (the prereq download in Step 1 is what makes it resolvable).
- **Stock image NVFP4 behavior on your exact GB10/driver** — the card reports the community image boots it as of 2026‑05‑06; your driver/vLLM versions may differ. The pinned digest reduces drift.
- Exact `--served-model-name` multi‑alias handling by sparkrun's standardized `served_model_name` key (works as plain text in the command either way).

## Sources
- Model card — https://huggingface.co/AEON-7/Gemma-4-26B-A4B-it-Uncensored-NVFP4
- AEON vLLM container — https://github.com/AEON-7/vllm-ultimate-dgx-spark
- DFlash drafter — https://huggingface.co/z-lab/gemma-4-26B-A4B-it-DFlash
- sparkrun recipe format — https://sparkrun.dev/recipes/format/
- sparkrun run — https://sparkrun.dev/cli/run/
