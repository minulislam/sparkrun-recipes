# Flash-class uncensored recipes: design

Date: 2026-10-13. Status: awaiting review.

## Goal

Give each of the three Flash-class families one working uncensored route on
`dgx-pair` at the largest context the pair can hold, remove recipes that cannot
run, and clear the stubs they leave behind. Uncensored comes first; a stock
NVFP4 build is the fallback where no uncensored one works.

Families: Qwen3.8 Flash-Next, GLM-5.3 Flash, DeepSeek V4 Flash.

## What the user decided

- One uncensored build per family. No DeepSeek V4.1 download, no stock GLM
  download.
- `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` and all three of its recipes
  (`-tp2`, `-ep2`, `-coder-tp2`) stay exactly as they are.

## Out of scope

- TP1 at full context. All three families exceed one node's memory except as
  low-bitrate EXL3 quants, and no uncensored single-Spark build was readable.
- DeepSeek V4.1 Flash. Every registry recipe needs three or four nodes; the
  two-node route is a 197 GiB EXL3 build that was not selected.
- Other model families, image mirroring, the pre-push gate.

## Survey result

Searched all eight registries (updated 2026-10-13) and Hugging Face.

| Family | Runtime abliteration | Chosen uncensored build | Size | On disk |
|---|---|---|---|---|
| DeepSeek V4 Flash 0731 | Yes: `pocharlies/deepseek-v4-flash-0731-uncensored-abliterated-refusal-directions` (757 KB) | stock `deepseek-ai/DeepSeek-V4-Flash-0731` plus the directions file | 155.4 GiB | stub on head |
| Qwen3.8 Flash-Next | None found | `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` | 125.9 GiB | complete on worker only |
| GLM-5.3 Flash | None found | `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45` | 184 GiB (197.8 GB) | absent |

No registry carries a recipe for any of the three chosen builds, so each needs
a new recipe adapted from the nearest upstream one.

## Work items

### 1. DeepSeek V4 Flash 0731 with the refusal dial

- **Weights:** download `deepseek-ai/DeepSeek-V4-Flash-0731` on the head,
  hardlink the blobs, then stage on the worker. Download the directions file
  to both nodes.
- **Image:** upstream publishes no image. Build `deploy/Dockerfile` from
  `github.com/pocharlies/deepseek-v4-flash-rank1-refusal-projection` on base
  `ghcr.io/anemll/dspark-vllm-gx10:0.1.1`, tagged with a date, and load it on
  both nodes. The Dockerfile runs the project's own tests at build time; a
  failed test means no image.
- **Recipes:**
  - `deepseek-v4-flash-0731-tp2`: stock, copied from
    `@official/deepseek-v4-flash-0731-b12x-dspark-vllm` with an attribution
    header, a dated image tag in place of `:latest`, and a readiness block.
  - `deepseek-v4-flash-0731-refusal-dial-tp2`: the built image,
    `VLLM_REFUSAL_DIRS` pointing at the cached file, upstream's serve settings
    (TP2, DSpark k=5, B12X, `nvfp4_ds_mla` KV, 393,216 context, 4 sequences).
    Lambda starts at 0, as upstream ships it; the header gives the `curl` call
    that turns it on.
- **Risk:** the anemll base image could not load the vision tower of the
  orcarouter build on this pair. The 0731 checkpoint is text-only, so this
  should not apply, but the first boot is the test.

### 2. Qwen3.8 Flash-Next abliterated

- **Weights:** copy from worker to head over the LAN. No download.
- **Recipe:** `qwen3.8-flash-next-abliterated-nvfp4-tp2`, taken from
  `qwen3.8-flash-next-nvfp4-tp2` (row 48, verified) with the model id changed.
  The card names SGLang as its serving path, so if the vLLM route fails to
  load, the fallback is the community SGLang recipe
  `qwen3.8-flash-next-nvfp4-nextn-sglang-thupalo`.
- **Risk:** this build is 125.9 GiB against 98.6 GiB for the verified base. If
  its per-layer-embedding table is bf16 like the orcarouter build, it will not
  fit. Checked 2026-10-13 on the worker: the largest single tensor is 3.1 GiB
  (an MTP expert block) and there is no 100 GB bf16 table like the orcarouter
  build's. That removes the known failure but does not prove the fit; the
  first boot does.

### 3. GLM-5.3 Flash abliterated

- **Access:** the repo is gated with automatic approval. The account behind
  sparkrun's HF token must accept the terms on the model page first.
- **Weights:** download on the head, hardlink, stage on the worker.
- **Recipe:** `glm-5.3-flash-abliterated-nvfp4-tp2`, following the card: the
  `ghcr.io/tonyd2wild/vllm-glm53-flash:sm121-v11-dflash2` image (already on the
  head), marlin MoE, DFlash2 k=7 with `incoai/GLM-5.3-Flash-DFlash2`
  pre-cached, fp8 KV, `--block-size 2304`, utilization at or below 0.82, no
  `--quantization` flag, and the repo's thinking-off chat template mounted.
- **Risk:** 92 GiB of weights per node leaves about 6 GiB for KV and graphs at
  0.82. Full 262k context may not be reachable. The recipe states whatever
  context the first boot measures. If it is below 131k, the fallback is
  `Mia-AiLab/GLM-5.3-Flash-EXL3-4bpw-TensorFold-Ablit` (about 164 GiB, gated).

- **Long-context profile (added 2026-10-13 from a link the user supplied):**
  `github.com/drowzeys/keys-vLLm.0.27.1-GLM-5.3-Flash-NVFP4-NVFP4KV-1M-Context-Abliterated`
  serves this checkpoint family at 1,048,576 context on 2× GB10 with an
  `nvfp4_ds_mla` KV cache (368 bytes per token per layer against 656 for
  fp8), a published image and bind-mounted vLLM overlays. Upstream reports
  about 22 tok/s, `--enforce-eager`, and 1.24 GB free at the 1M peak with
  utilization 0.85. A second recipe,
  `glm-5.3-flash-abliterated-nvfp4kv-long-tp2`, follows it at this repo's
  0.82 ceiling, starting at 524k and going higher only if memory allows. It
  is attempted after the 262k recipe verifies. The repo predates the
  checkpoint's September re-publish, so its `index_topk=2044` workaround has
  to be re-checked against the current files.

### 4. Recipes to remove

| Recipe | Reason |
|---|---|
| `qwen3.8-flash-next-uncensored-nvfp4-tp2` | Unfit on this pair after three attempts; replaced by item 2 |
| `glm-5.3-flash-nvfp4-tp2` | Its image was never published and its checkpoint is a stub |
| `glm-5.3-flash-exl3-1x-spark` | Wrong checkpoint, provisional container, runtime and entrypoint disagree |
| `glm-5.3-flash-uncensored-nvfp4-tp2` | 205 GB, marginal, stub; replaced by item 3 |
| `deepseek-v4-flash-tp2` | No container, pre-0731 checkpoint; replaced by item 1 |
| `deepseek-v4-flash-vision-exp-tp2` | Stub; the verified uncensored vision build covers it |

`deepseek-v4-flash-nvfp4-atlas-ep2` is the user's decision (see below).

### 5. Weights and stubs

Delete without backup (config-only stubs, no weights): the head stubs for
these three families that no kept recipe uses, and the two worker stubs.
`deepseek-ai/DeepSeek-V4-Flash-0731` is filled by item 1 instead of deleted.

Needs the user's word before anything is deleted, each backed up to
`/mnt/nas/dgx-spark/model-backup/` first if kept as an option:

1. `orcarouter/Qwen3.8-Flash-Next-Uncensored-NVFP4`: 170.9 GiB on each node,
   unfit here.
2. `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw`: 81.6 GiB partial on the head.
   Checked 2026-10-13: none of its 59 large blobs match a sha256 in the
   successor repo `Mia-AiLab/GLM-5.3-Flash-EXL3-4bpw-TensorFold` (89 files,
   163.6 GiB, re-sharded), so it cannot be resumed from there. It is unusable
   as it stands.
3. `nvidia/DeepSeek-V4-Flash-NVFP4` stub and the `-atlas-ep2` recipe that
   points at it.

### 6. Verification and records

Each new recipe goes through the repo's `verify` skill: validate, dry run,
launch with `--no-follow`, then a real request. A recipe is recorded at the bar
it reached and no higher. For the dial recipe, verification includes one
refusing prompt at lambda 0 and the same prompt at lambda 1.5.

Then update `INDEX.md` (new rows, removed rows listed without renumbering),
`MODELS.md` and `HISTORY.md`.

## Order

1. Gate acceptance for the GLM repo (item 3). The other two pre-checks are
   done and recorded under items 2 and 5.
2. Remove the six recipes and the weightless stubs.
3. Item 2, since it needs no download.
4. Item 1 download and image build, then item 3 download.
5. Verify each as its weights land. Update records after each.

The pair must be idle for every TP2 launch: stop `vllm-reranker` on the worker
for the duration and restore it afterwards with
`benchmarks/redteam/RESTORE-vllm-reranker.sh`.

## Disk

| Node | Free now | Added | Free after |
|---|---|---|---|
| head | 1.1 TiB | 155 + 126 + 184 = 465 GiB | about 0.65 TiB |
| worker | 1.5 TiB | 155 + 184 = 339 GiB | about 1.2 TiB |

## Constraints carried from the repo

- Dated image tags only; no digest pins on two-node recipes.
- Hardlink HF blobs before any sparkrun sync.
- `gpu_memory_utilization` between 0.70 and 0.82.
- `executor_config: {entrypoint: ""}` for images that bake `vllm serve`.
- Comm pins stay in the cluster definition, not in recipes.
- Commit and push only when asked.
