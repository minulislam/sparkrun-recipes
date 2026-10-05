# Model inventory — what is actually on disk, and which recipes use it

Measured live on both nodes **2026-10-06**: head `gb10-spark` (10.10.20.10) and
worker `gx10-spark` (10.10.20.11), both GB10 / 121 GB unified memory.

A repo counts as **complete** only when every shard named in
`model.safetensors.index.json` resolves to a real file *and* the byte sum reaches
`metadata.total_size`. Repos with no weight files at all are **stubs** — HF
fetched the config and nothing else. Sizes are GiB of weight files only
(`.safetensors` / `.gguf` / `.bin`), not the whole cache directory.

> Do not use `du -sh` on a `models--*` directory to judge this. One repo
> (`orcarouter/Qwen3.8-27B-Uncensored-NVFP4`) keeps its weights in the shared
> content-addressed store at `hub/blobs/XX/…` after the hardlink repair in
> `benchmarks/FLEET-2026-09-27.md`, so plain `du` reports 669 MB for a complete
> 23 GiB checkpoint. Several repos also hold **two** snapshot revisions where only
> one carries weights.

Legend: **H** = complete on head, **W** = complete on worker. A TP2/EP2 recipe
needs its weights on **both** nodes.

## Primary checkpoints with recipes

| Model | Nodes | GiB | Recipes | Recipe files |
|---|---|---|---|---|
| `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` | H W | 156.3 | **3** | `deepseek-v4-flash-vision-uncensored-tp2`, `-ep2`, `-coder-tp2` |
| `AEON-7/Qwen3.6-27B-AEON-Ultimate-Uncensored-NVFP4` | H W | 25.8 | **2** | `qwen36-27b-aeon-ultimate-nvfp4`, `qwen36-27b-aeon-colocate` |
| `AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4` | H W | 21.8 | **2** | `qwen36-35b-a3b-heretic-nvfp4`, `qwen36-35b-a3b-heretic-nvfp4-batch` |
| `AEON-7/Gemma-4-26B-A4B-it-Uncensored-NVFP4` | H W | 15.3 | **2** | `gemma4-26b-aeon-vllm`, `gemma4-26b-stock-vllm` |
| `unsloth/Qwen3.8-27B-NVFP4` | H W | 21.8 | **2** | `qwen3.8-27b-nvfp4-tp1`, `qwen38-27b-nvfp4-refusal-dial` |
| `orcarouter/Qwen3.8-Flash-Next-Uncensored-NVFP4` | H W | 170.9 | 1 | `qwen3.8-flash-next-uncensored-nvfp4-tp2` |
| `thinkingmachines/Inkling-Small-NVFP4` | H W | 159.0 | 1 | `inkling-small-nvfp4-tp2-sglang` |
| `nvidia/MiniMax-M2.7-NVFP4` | H W | 130.3 | 1 | `minimax-m2.7-nvfp4-vllm-tp2` |
| `lukealonso/MiniMax-M2.7-NVFP4` | H W | 125.3 | 1 | `minimax-m2.7-nvfp4-atlas-ep2` |
| `stepfun-ai/Step-3.7-Flash-NVFP4` | H W | 120.4 | 1 | `step-3.7-flash-nvfp4-tp2-miaai` |
| `local-inference-lab/Qwen3.8-Flash-Next-NVFP4` | H W | 98.6 | 1 | `qwen3.8-flash-next-nvfp4-tp2` |
| `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4` | H W | 74.8 | 1 | `nemotron-3-super-120b-nvfp4-tp2` |
| `AEON-7/Nemotron-3-Nano-Omni-AEON-…-NVFP4` | H W | 20.4 | 1 | `nemotron3-nano-omni-aeon-nvfp4` |
| `AEON-7/Gemma-4-31B-it-DECKARD-HERETIC-…-NVFP4` | H W | 19.0 | 1 | `gemma4-31b-deckard-heretic-nvfp4` |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` | H W | 18.0 | 1 | `nemotron-3-nano-30b-nvfp4-tp1` |
| `AEON-7/Gemma-4-12B-it-AEON-Abliterated-K4-NVFP4-FP8` | H W | 8.7 | 1 | `gemma4-12b-k4-nvfp4-fp8` |
| `poolside/Laguna-S-2.1-NVFP4` | H | 92.9 | 1 | `laguna-s-2.1-nvfp4-tp1` |
| `Qwen/Qwen3.8-27B-FP8` | H | 28.7 | 1 | `qwen3.8-27b-fp8-mtp-tp1` |
| `orcarouter/Qwen3.8-27B-Uncensored-NVFP4` | H | 23.0 | 1 | `qwen3.8-27b-uncensored-nvfp4-tp1` |
| `cyankiwi/GLM-4.7-Flash-AWQ-4bit` | H | 18.8 | 1 | `glm-4.7-flash-awq-tp1` |
| `nvidia/diffusiongemma-26B-A4B-it-NVFP4` | H | 17.5 | 1 | `diffusiongemma-26b-a4b-nvfp4` |

**21 complete primary checkpoints, 27 recipes served.** Five are head-only
(`Laguna`, `Qwen3.8-27B-FP8`, `Qwen3.8-27B-Uncensored`, `GLM-4.7-Flash-AWQ`,
`diffusiongemma`) — all tp1 recipes, so that is correct, not a gap.

## Auxiliary artifacts (drafters, ablation tensors)

Not servable on their own; each is pulled in by a recipe's
`--speculative-config` or equivalent. They must be **pre-cached** — serve
containers run `HF_HUB_OFFLINE=1`.

| Artifact | Nodes | GiB | Used by |
|---|---|---|---|
| `z-lab/Qwen3.6-27B-DFlash` | H W | 3.2 | `qwen36-27b-aeon-ultimate-nvfp4` |
| `z-lab/gemma-4-31B-it-DFlash` | H W | 2.9 | `gemma4-31b-deckard-heretic-nvfp4` |
| `RadixArk/Inkling-Small-DSpark-Preview` | H W | 1.7 | `inkling-small-nvfp4-tp2-sglang` |
| `z-lab/gemma-4-26B-A4B-it-DFlash` | H W | 0.8 | `gemma4-26b-aeon-vllm` |
| `z-lab/Qwen3.6-35B-A3B-DFlash` | H W | 0.7 | `qwen36-35b-a3b-heretic-nvfp4` |
| `pocharlies/qwen38-27b-uncensored-abliterated-refusal-directions` | H W | 0.003 | `qwen38-27b-nvfp4-refusal-dial` |

The refusal-direction tensor is complete at 2.8 MB by design — it is a rank-1
ablation, not a checkpoint.

## Downloaded but no recipe uses them

Nothing in `recipes/` references these. **~226 GiB** in total.

| Model | Nodes | GiB | Note |
|---|---|---|---|
| `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` | W | 125.9 | **Worker-only, largest orphan.** 206 shards, complete. No recipe, and absent from the head, so unusable as-is |
| `openai/gpt-oss-20b` | H | 38.4 | The tp1 `gpt-oss-120b` attempts in `FLEET-2026-09-27.md` are a different, larger checkpoint |
| `nvidia/Qwen3.8-27B-NVFP4` | H | 20.4 | Complete, but every Qwen3.8-27B recipe points at the `unsloth` or `orcarouter` repo instead |
| `sakamakismile/Huihui-Qwen3.6-27B-abliterated-NVFP4-MTP` | H | 19.1 | Complete; no recipe was ever written for it |
| `google/gemma-4-E4B-it` | H | 14.9 | Base BF16, not a serving target here |
| `Qwen/Qwen2.5-3B-Instruct` | H | 5.7 | — |
| `Qwen/Qwen3-1.7B` | W | 3.8 | — |
| `unsloth/Qwen3.5-4B-MTP-GGUF` | W | 2.8 | — |
| `BAAI/bge-reranker-v2-m3` | W | 2.1 | Used by `benchmarks/redteam/RESTORE-vllm-reranker.sh`, not by a recipe |
| `Qwen/Qwen3-Embedding-0.6B` | H | 1.1 | Gateway embedding model, not a recipe target |

## Partial download — blocks a recipe

| Model | Nodes | On disk | Expected | Blocks |
|---|---|---|---|---|
| `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` | H | **81.6 GiB / 59 of 120 shards** | 163.7 GiB (`MANIFEST.json`, 328 files) | `glm-5.3-flash-exl3-tp2` |

This is the only sizeable GLM-5.3 checkpoint present anywhere, it is **half
downloaded**, and it is on the head only — a tp2 recipe needs both nodes. That
is why row 32 has never been benchmarked.

## Stubs — config only, no weights

Metadata-only caches. Each needs a full download before its recipe can run.

**Head (17):** `0xSero/GLM-5.3-Flash-EXL3-Spark` · `0xSero/deepseek-v4-flash-0731-spark` ·
`LibertAIDAI/GLM-5.3-Flash-NVFP4` · `RadixArk/Qwen3.8-27B-NVFP4` ·
`RadixArk/Qwen3.8-Flash-Next-NVFP4` (declares 125.9 GiB) · `Sebesky/MiniMax-M3-W4A16-GPTQ` ·
`XanuNetworks/North-Mini-Code-1.0-NVFP4` · `deepseek-ai/DeepSeek-V4-Flash-0731` (155.4 GiB) ·
`deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` (156.3 GiB) · `inclusionAI/Ling-3.0-flash-int4` ·
`kodelow/Hy3-NVFP4-W4A16` · `local-inference-lab/GLM-5.3-Flash-NVFP4-Spark` (174.7 GiB) ·
`mistralai/Mistral-Small-4-119B-2603` · `nvidia/DeepSeek-V4-Flash-NVFP4` ·
`nvidia/Qwen3.8-Flash-Next-NVFP4` · `orcarouter/GLM-5.3-Flash-Uncensored-NVFP4` ·
`turboderp/GLM-5.3-Flash-exl3`

**Worker (1):** `unsloth/Qwen3.8-Flash-Next-GGUF`

## By family, as asked

| Family | Repos cached | Complete | Partial | Stub | Complete GiB |
|---|---|---|---|---|---|
| **GLM** (head) | 7 | 1 (`GLM-4.7-Flash-AWQ-4bit`) | 1 (`GLM-5.3-Flash-EXL3-TR3-4bpw`) | 5 | 18.8 |
| **Qwen3.8** (head) | 10 | 6 + 1 ablation tensor | 0 | 3 | 363.4 |
| **DeepSeek** (head) | 5 | 1 (`DeepSeek-V4-Flash-Vision-Uncensored`) | 0 | 4 | 156.3 |

The six complete Qwen3.8 checkpoints are `orcarouter/…-Flash-Next-Uncensored`
(170.9), `local-inference-lab/…-Flash-Next` (98.6), `Qwen/…-27B-FP8` (28.7),
`orcarouter/…-27B-Uncensored` (23.0), `unsloth/…-27B-NVFP4` (21.8) and
`nvidia/…-27B-NVFP4` (20.4) — the last of which no recipe uses.

The worker holds **no GLM checkpoint at all**, which is why the newest recipe is
`glm-5.3-flash-exl3-1x-spark.yaml` (single Spark) rather than a tp2 variant.

## Regenerate

```bash
# run on each node; the worker needs the script copied over first
python3 - <<'PY'
import os,glob,json
hub=os.path.expanduser("~/.cache/huggingface/hub")
WEXT=(".safetensors",".gguf",".bin",".pt",".pth",".engine",".npz")
for d in sorted(glob.glob(hub+"/models--*")):
    repo="/".join(os.path.basename(d)[len("models--"):].split("--"))
    best=(0,0,0,0,0)
    for s in glob.glob(d+"/snapshots/*"):          # scan EVERY revision
        tot=n=0
        for root,_,fs in os.walk(s):
            for f in fs:
                if f.endswith(WEXT):
                    try: tot+=os.stat(os.path.join(root,f)).st_size; n+=1
                    except OSError: pass
        exp=miss=decl=0
        idx=os.path.join(s,"model.safetensors.index.json")
        if os.path.exists(idx):
            j=json.load(open(idx)); exp=j.get("metadata",{}).get("total_size",0)
            sh=sorted(set(j.get("weight_map",{}).values())); decl=len(sh)
            miss=sum(1 for x in sh if not os.path.isfile(os.path.join(s,x)))
        if tot>best[0]: best=(tot,n,exp,miss,decl)
    tot,n,exp,miss,decl=best
    st="STUB" if tot==0 else (f"PARTIAL {decl-miss}/{decl}" if miss else
        ("SHORT" if exp and tot<exp*0.999 else "COMPLETE"))
    print(f"{repo:62} {st:16} {tot/2**30:8.1f} GiB")
PY
```

Then map models to recipes with
`grep -l '^model: <repo>' recipes/*.yaml` (every recipe names its checkpoint in
`model:`; none loads from a local path).
