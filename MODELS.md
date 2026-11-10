# Model inventory — what is actually on disk, and which recipes use it

Measured live on both nodes **2026-11-10** with the script under *Regenerate*:
head `gb10-spark` (10.10.20.10) and worker `gx10-spark` (10.10.20.11), both GB10 /
121 GB unified memory. Free space after today's cleanup: head **618 GiB**, worker
**2.5 TiB**. The previous full pass was 2026-10-13; this page replaces it.

> **Read first: the worker holds only 5 checkpoints.** Every TP2/EP2 recipe needs its
> weights on **both** nodes, and only one of them (`glm-5.3-flash-abliterated-nvfp4kv-long-tp2`)
> has that today. The other 14 two-node recipes have weights on the head only, including
> five gateway bindings in `~/.config/sparkrun/proxy.yaml` (Flash-Next abliterated, GLM-5.3
> abliterated and EXL3, both DeepSeek-V4-Vision recipes). Their first cold start has to copy
> or download the weights to the worker first. This page does not record when the worker
> copies went away; it records what is there on 2026-11-10.

A repo counts as **complete** only when every shard named in
`model.safetensors.index.json` resolves to a real file *and* the byte sum reaches
`metadata.total_size`. Repos with no weight files at all are **stubs**. Sizes are GiB
of weight files only (`.safetensors` / `.gguf` / `.bin`), not the cache directory.

> - Do not use `du -sh` on a `models--*` directory. Repo blobs on the head are hardlinks
>   (and, for `Qwen/Qwen3-Reranker-4B`, symlinks) into a shared content store at
>   `~/.cache/huggingface/hub/blobs/<2-char>/<sha256>`. `hf cache rm` removes the repo
>   side only, so no space comes back until the store copy goes too. Before deleting
>   from the store, exclude every file that a hardlink or a symlink still references.
> - **Never run `hf cache prune` here.** Its dry run on 2026-11-10 listed 1.2 TB,
>   including detached revisions that recipes pin
>   (`orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` `2ef3d5c`,
>   `orcarouter/Qwen3.8-27B-Uncensored-NVFP4` `69d2134`).
> - Several repos keep 2–4 snapshot revisions. Most share the same weight files, but
>   three repos have a weightless `main` and keep their weights in an older revision:
>   `AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4`, `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored`
>   and `orcarouter/Qwen3.8-27B-Uncensored-NVFP4`. Their recipes pin that revision and
>   pass `--revision {model_revision}` to vLLM; a new recipe for them must do the same.
> - The script reports `local-inference-lab/Qwen3.8-Flash-Next-NVFP4` as SHORT (99.0 GiB
>   against a 102.5 GiB `total_size`). That is a false positive: all 40 shards match the
>   Hub byte for byte on 2026-11-10; the publisher's index overstates the total.

Legend: **H** = complete on head, **W** = complete on worker.

## Ready — weights on every node the recipe needs (20 recipes)

| Model | Nodes | GiB | Recipes |
|---|---|---|---|
| `local/glm53-flash-ablit-topk2044` | H W | 184.3 | `glm-5.3-flash-abliterated-nvfp4kv-long-tp2` (the only two-node recipe ready) |
| `poolside/Laguna-S-2.1-NVFP4` | H | 92.9 | `laguna-s-2.1-nvfp4-tp1` |
| `AEON-7/Qwen3.6-27B-AEON-Ultimate-Uncensored-NVFP4` | H | 25.8 | `qwen36-27b-aeon-ultimate-nvfp4`, `qwen36-27b-aeon-colocate` |
| `orcarouter/Qwen3.8-27B-Uncensored-NVFP4` | H | 23.0 | `qwen3.8-27b-uncensored-nvfp4-tp1` (gateway `default` alias) |
| `orcarouter/Nex-N2.5-mini-Uncensored-NVFP4` | H | 22.3 | `nex-n2.5-mini-uncensored-nvfp4-tp1` (UNFIT 2026-10-16, garbage output) |
| `AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4` | H W | 21.8 | `qwen36-35b-a3b-heretic-nvfp4`, `qwen36-35b-a3b-heretic-nvfp4-batch` |
| `unsloth/Qwen3.8-27B-NVFP4` | H | 21.8 | `qwen3.8-27b-nvfp4-tp1`, `qwen38-27b-nvfp4-refusal-dial` |
| `AEON-7/Nemotron-3-Nano-Omni-AEON-Ultimate-Uncensored-NVFP4` | H | 20.4 | `nemotron3-nano-omni-aeon-nvfp4` |
| `AEON-7/Gemma-4-31B-it-DECKARD-HERETIC-Uncensored-NVFP4` | H | 19.0 | `gemma4-31b-deckard-heretic-nvfp4` |
| `cyankiwi/GLM-4.7-Flash-AWQ-4bit` | H | 18.8 | `glm-4.7-flash-awq-tp1` |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` | H | 18.0 | `nemotron-3-nano-30b-nvfp4-tp1` |
| `nvidia/diffusiongemma-26B-A4B-it-NVFP4` | H | 17.5 | `diffusiongemma-26b-a4b-nvfp4` |
| `AEON-7/Gemma-4-26B-A4B-it-Uncensored-NVFP4` | H | 15.3 | `gemma4-26b-aeon-vllm`, `gemma4-26b-stock-vllm` |
| `AEON-7/Gemma-4-12B-it-AEON-Abliterated-K4-NVFP4-FP8` | H | 8.7 | `gemma4-12b-k4-nvfp4-fp8` |
| `Qwen/Qwen3-Embedding-4B` | H W | 7.5 | `qwen3-embedding-4b-tp1` |
| `Qwen/Qwen3-Reranker-4B` | H | 7.5 | `qwen3-reranker-4b-tp1` |

Single-node recipes that list `gx10-solo` as a gateway candidate (Nemotron Nano 30B,
embedding, reranker) can only use the worker where the weights are marked **W**.

## Two-node recipes with weights on the head only (14 recipes)

| Model | Nodes | GiB | Recipes |
|---|---|---|---|
| `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45` | H | 184.3 | `glm-5.3-flash-abliterated-nvfp4-tp2` |
| `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit` | H | 163.6 | `glm-5.3-flash-exl3-abliterated-tp2` |
| `thinkingmachines/Inkling-Small-NVFP4` | H | 159.0 | `inkling-small-nvfp4-tp2-sglang` |
| `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` | H | 156.3 | `deepseek-v4-flash-vision-uncensored-tp2`, `-coder-tp2`, `-ep2` (ep2 UNFIT) |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | H | 155.4 | `deepseek-v4-flash-0731-tp2`, `deepseek-v4-flash-0731-refusal-dial-tp2` |
| `nvidia/MiniMax-M2.7-NVFP4` | H | 130.3 | `minimax-m2.7-nvfp4-vllm-tp2` |
| `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` | H | 125.9 | `qwen3.8-flash-next-abliterated-nvfp4-tp2` |
| `lukealonso/MiniMax-M2.7-NVFP4` | H | 125.3 | `minimax-m2.7-nvfp4-atlas-ep2` |
| `stepfun-ai/Step-3.7-Flash-NVFP4` | H | 120.4 | `step-3.7-flash-nvfp4-tp2-miaai` |
| `local-inference-lab/Qwen3.8-Flash-Next-NVFP4` | H | 99.0 | `qwen3.8-flash-next-nvfp4-tp2` |
| `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4` | H | 74.8 | `nemotron-3-super-120b-nvfp4-tp2` |

The worker has 2.5 TiB free, so all of these fit there again (about 1.5 TiB in total).
`local-inference-lab/Qwen3.8-Flash-Next-NVFP4` also documents a single-node profile
(`tp: 1` override in the lil catalog: one sequence, 64K context, PLE offload); no
recipe here uses it yet.

## Auxiliary artifacts (drafters, ablation tensors)

Not servable on their own; each is pulled in by a recipe's `--speculative-config`
or equivalent. They must be **pre-cached** — serve containers run `HF_HUB_OFFLINE=1`.

| Artifact | Nodes | GiB | Used by |
|---|---|---|---|
| `z-lab/Qwen3.6-27B-DFlash` | H | 3.2 | `qwen36-27b-aeon-ultimate-nvfp4` |
| `z-lab/gemma-4-31B-it-DFlash` | H | 2.9 | `gemma4-31b-deckard-heretic-nvfp4` |
| `incoai/GLM-5.3-Flash-DFlash2` | H | 2.2 | `glm-5.3-flash-abliterated-nvfp4-tp2` |
| `RadixArk/Inkling-Small-DSpark-Preview` | H | 1.7 | `inkling-small-nvfp4-tp2-sglang` |
| `z-lab/gemma-4-26B-A4B-it-DFlash` | H | 0.8 | `gemma4-26b-aeon-vllm` |
| `z-lab/Qwen3.6-35B-A3B-DFlash` | H W | 0.7 | `qwen36-35b-a3b-heretic-nvfp4` |
| `pocharlies/qwen38-27b-uncensored-abliterated-refusal-directions` | H | 0.003 | `qwen38-27b-nvfp4-refusal-dial` |

The refusal-direction tensor is complete at 2.8 MB by design — it is a rank-1
ablation, not a checkpoint.

## Downloaded but no recipe uses them

| Model | Nodes | GiB | Note |
|---|---|---|---|
| `openai/gpt-oss-20b` | H | 38.4 | The tp1 `gpt-oss-120b` attempts in `FLEET-2026-09-27.md` used a different checkpoint |
| `nvidia/Qwen3.6-35B-A3B-NVFP4` | H W | 21.8 | Has no `main` ref. The `qwen3.6-35b-a3b-nvfp4*` recipes point at `unsloth/Qwen3.6-35B-A3B-NVFP4` instead |
| `nvidia/Qwen3.8-27B-NVFP4` | H | 20.4 | Every Qwen3.8-27B recipe uses the `unsloth` or `orcarouter` repo |
| `sakamakismile/Huihui-Qwen3.6-27B-abliterated-NVFP4-MTP` | H | 19.1 | No recipe was ever written for it |
| `Qwen/Qwen3-VL-Embedding-8B` | H | 15.2 | — |
| `google/gemma-4-E4B-it` | H | 14.9 | Base BF16, not a serving target here |
| `Qwen/Qwen2.5-3B-Instruct` | H | 5.7 | — |
| `Qwen/Qwen3-Embedding-0.6B` | H | 1.1 | Gateway embedding model, not a recipe target |

## Recipes whose checkpoint is not cached on either node (16 recipes)

- **Deleted 2026-11-10** (only the FP8 was a complete checkpoint; the rest were stubs,
  which were removed from the NAS too): `qwen3.8-27b-fp8-mtp-tp1` (`Qwen/Qwen3.8-27B-FP8`, 28.7 GiB, backup at
  `/mnt/nas/ai-models/model-backup/huggingface-hub/models--Qwen--Qwen3.8-27B-FP8`),
  `deepseek-v4-flash-nvfp4-atlas-ep2`, `hy3-295b-nvfp4-tp2`,
  `ling-3.0-flash-int4-tp1-sglang`, `north-mini-code-1.0-nvfp4-tp1`,
  `qwen3.8-27b-nvfp4-tp1-alt`, `qwen3.8-27b-nvfp4-tp1-sglang`.
- **Never downloaded:** `leanstral-1.5-119b-a6b-tp2`, `gemma-4-26b-a4b-nvfp4-tp1`,
  `gemma-4-31b-it-nvfp4-tp1`, `muse-glimmer-30b-nvfp4-tp1`,
  `nemotron-3.5-lightning-30b-a3b-nvfp4-tp1-sglang`,
  `nemotron-labs-3-puzzle-75b-nvfp4-tp1`, `qwen3.6-27b-nvfp4-tp1`,
  `qwen3.6-35b-a3b-nvfp4-tp1`, `qwen3.6-35b-a3b-nvfp4-unofficial-tp1`.

The `qwen3.8-27b-fp8-mtp-tp1` binding was removed from the gateway when its weights
were deleted.

## Deleted on 2026-11-10 (head unless noted)

- `Qwen/Qwen3.8-27B-FP8` (28.7 GiB), verified against the NAS copy first.
- Partial downloads: `mistralai/Mistral-Small-4-119B-2603-NVFP4` (2 of 13 shards),
  `local-inference-lab/{Qwen3.8-27B-NVFP4-QAD, GLM-5.3-Flash-NVFP4, GLM-5.3-Flash-NVFP4-Spark, GLM-5.3-NVFP4}`,
  `deepseek-ai/{DeepSeek-V4-Flash, DeepSeek-V4-Flash-Vision-Exp}`, `Qwen/Qwen3-VL-Reranker-8B`,
  `OptimizeLLM/Qwen3-VL-30B-A3B-Thinking-NVFP4`.
- Stubs, also removed from the NAS backup: `0xSero/deepseek-v4-flash-0731-spark`,
  `dealignai/GLM-5.3-Flash-UNCENSORED-NVFP4`, `inclusionAI/Ling-3.0-flash-int4`,
  `kodelow/Hy3-NVFP4-W4A16`, `mistralai/Mistral-Small-4-119B-2603`,
  `nvidia/DeepSeek-V4-Flash-NVFP4`, `nvidia/Qwen3.8-Flash-Next-NVFP4`,
  `RadixArk/Qwen3.8-27B-NVFP4`, `Sebesky/MiniMax-M3-W4A16-GPTQ`,
  `XanuNetworks/North-Mini-Code-1.0-NVFP4`.
- The superseded revision `7c4f1bc` of `local-inference-lab/Qwen3.8-Flash-Next-NVFP4`
  (36 shards, 103 GB; NAS copy verified), plus its 650 files in the shared blob store.
- `~/.cache/huggingface/spark-forge-local/` on both nodes: its one checkpoint moved to
  `hub/models--local--glm53-flash-ablit-topk2044/snapshots/local` (NAS backup at
  `model-backup/huggingface-hub/spark-forge-local/glm53-flash-ablit-topk2044/`).

The head now holds no stubs and no partial downloads. Earlier deletions (2026-10-13/14)
are recorded in `HISTORY.md`.

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

Then map models to recipes with `grep -l '^model: <repo>' recipes/*.yaml`. One recipe
loads from a local path instead: `glm-5.3-flash-abliterated-nvfp4kv-long-tp2` sets
`model_path` to the `local/glm53-flash-ablit-topk2044` snapshot.
