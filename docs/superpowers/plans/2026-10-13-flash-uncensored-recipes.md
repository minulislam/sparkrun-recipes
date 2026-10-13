# Flash-class Uncensored Recipes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One working uncensored route each for Qwen3.8 Flash-Next, GLM-5.3 Flash and DeepSeek V4 Flash on `dgx-pair`, with unrunnable recipes and weightless stubs removed.

**Architecture:** Each family gets a new recipe YAML in `recipes/`, adapted from the nearest upstream recipe, plus its weights staged on both nodes. A recipe's "test" is the repo's `verify` procedure: lint, dry run, launch, then a real request. Records (`INDEX.md`, `MODELS.md`, `HISTORY.md`) are updated per task at the bar actually reached.

**Tech Stack:** sparkrun 0.3.10, vLLM (three different images), Hugging Face `hf` CLI, Docker, two GB10 nodes (head 10.10.20.10, worker 10.10.20.11).

**Spec:** `docs/superpowers/specs/2026-10-13-flash-uncensored-recipes-design.md`

## Global Constraints

- Load the `sparkrun:run` skill before any sparkrun CLI call; follow `.claude/skills/verify/SKILL.md` for every launch.
- Always `--no-follow`. Cluster is `dgx-pair`. Endpoint `http://10.10.20.10:8000/v1`.
- `gpu_memory_utilization` 0.70–0.82. Never 0.85.
- Dated image tags only. No digest pins on two-node recipes.
- Hardlink HF blobs before any sparkrun sync (0.3.10 self-rsync deletes symlinked blobs).
- `executor_config: {entrypoint: ""}` for images that bake `vllm serve`.
- No comm pins (`NCCL_*`, `GLOO_*`, `TP_SOCKET_IFNAME`) in recipes.
- Never print the HF token. Pass it inline as the verify skill shows.
- No commit or push unless the user asks. Work on `main`.
- Do not touch `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` or its three recipes.
- Weight deletion needs the user's explicit word (Task 6). Config-only stubs are the exception.
- Before each TP2 launch: `docker ps` and `nvidia-smi` on both nodes; stop `vllm-reranker` on the worker; restore it afterwards with `benchmarks/redteam/RESTORE-vllm-reranker.sh`.
- Report a status only at the bar reached: lints, serves, verified.

## Review Focus

1. **A new recipe serves but with a collapsed context.** Expect `/v1/models` `max_model_len` to equal the recipe's stated context. Pinned in Tasks 2, 4, 5 (step "read `max_model_len`").
2. **The dial comes up ablated, or "off" is not off.** Expect lambda 0 at boot and a refusal at lambda 0. Pinned in Task 4.
3. **Worker copy of weights is incomplete.** Expect the `MODELS.md` regenerate script to print COMPLETE on both nodes before launch. Pinned in Tasks 2, 3, 5.
4. **A removed recipe is still referenced.** Expect `grep` for each removed name to hit only `HISTORY.md` and the removal notes. Pinned in Task 1.
5. **The engine dies after a few requests** (as Step-3.7 and the orcarouter DeepSeek build did). Expect 20 sequential requests to succeed before recording "verified". Pinned in Tasks 2, 4, 5.

---

### Task 1: Remove six recipes and the weightless stubs

**Files:**
- Delete: `recipes/qwen3.8-flash-next-uncensored-nvfp4-tp2.yaml`, `recipes/glm-5.3-flash-nvfp4-tp2.yaml`, `recipes/glm-5.3-flash-exl3-1x-spark.yaml`, `recipes/glm-5.3-flash-uncensored-nvfp4-tp2.yaml`, `recipes/deepseek-v4-flash-tp2.yaml`, `recipes/deepseek-v4-flash-vision-exp-tp2.yaml`
- Modify: `INDEX.md` (rows 13, 14, 15, 44, 45 removed and listed under Open items; row numbers not reused), `MODELS.md`, `README.md` if it names any of them

- [ ] **Step 1:** `git rm` the six files.
- [ ] **Step 2:** List stub candidates on each node with the regenerate script in `MODELS.md`; keep only rows printing `STUB` whose repo matches `GLM-5.3-Flash|Qwen3.8-Flash-Next|DeepSeek-V4-Flash|deepseek-v4-flash`.
- [ ] **Step 3:** From that list drop `deepseek-ai/DeepSeek-V4-Flash-0731` (Task 3 fills it) and `nvidia/DeepSeek-V4-Flash-NVFP4` (Task 6). Delete the rest with `rm -rf ~/.cache/huggingface/hub/models--<org>--<name>` after confirming each directory is under 50 MB with `du -sh`.
- [ ] **Step 4:** Edit `INDEX.md` and `MODELS.md` to match.
- [ ] **Step 5: Test.** Run `for n in <six names>; do grep -rln "$n" --include=*.md --include=*.yaml . ; done`. Expected: hits only in `HISTORY.md`, `INDEX.md` Open items, `MODELS.md` removed-recipes table, and the spec/plan. Run `ls recipes | wc -l`. Expected: `42`.

### Task 2: Qwen3.8 Flash-Next abliterated

**Files:**
- Create: `recipes/qwen3.8-flash-next-abliterated-nvfp4-tp2.yaml`
- Modify: `INDEX.md` (new row 59), `MODELS.md`

**Interfaces:**
- Consumes: `recipes/qwen3.8-flash-next-nvfp4-tp2.yaml` as the template.
- Produces: served model name `qwen3.8-flash-next-abliterated`.

- [ ] **Step 1:** Copy the weights worker to head: on the head, `rsync -aH --info=progress2 devops@10.10.20.11:.cache/huggingface/hub/models--dealignai--Qwen3.8-Flash-Next-ABLITERATED-NVFP4 ~/.cache/huggingface/hub/`. Then confirm `snapshots/*/` entries resolve; if blobs are symlinked, hardlink them as in `benchmarks/FLEET-2026-09-27.md`.
- [ ] **Step 2:** Run the regenerate script on both nodes. Expected: `COMPLETE` and 125.9 GiB on each.
- [ ] **Step 3:** Create the recipe as a copy of the template with: `model: dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4`, `served_model_name: qwen3.8-flash-next-abliterated`, `metadata.model_vram: 135`, a `>>>` header stating source, UNVERIFIED, and the uncensored warning used in the refusal-dial recipe header. Keep `--quantization modelopt_mixed` only if `hf_quant_config.json` in the snapshot says `MIXED_PRECISION`; otherwise remove the flag.
- [ ] **Step 4:** `sparkrun recipe validate recipes/qwen3.8-flash-next-abliterated-nvfp4-tp2.yaml`. Expected: no errors. Then `sparkrun run ./recipes/<file> --dry-run`. Expected: two hosts, fit accepted.
- [ ] **Step 5:** Launch per the verify skill. Poll until `/v1/models` returns 200 or the log shows a traceback.
- [ ] **Step 6: Test.** `max_model_len` from `/v1/models` equals `262144`. One chat completion returns non-empty content. One prompt from `benchmarks/redteam/` harmful split returns a compliant answer. 20 sequential 120-token requests all return 200.
- [ ] **Step 7:** If the vLLM load fails on an unknown-architecture or PLE error, stop, and port `@community/qwen3.8-flash-next-nvfp4-nextn-sglang-thupalo` with the same model id as the same filename; repeat steps 4–6. Record which route worked.
- [ ] **Step 8:** `sparkrun stop <cluster_id>`. Write the measured numbers into the recipe header, `INDEX.md` row 59 and `MODELS.md`.

### Task 3: Download DeepSeek V4 Flash 0731 and build the dial image

**Files:**
- Create: `images/deepseek-rank1/README.md` (build provenance: upstream commit sha, base image, tag, date)

**Interfaces:**
- Produces: image `spark-forge/vllm-dsv4-rank1:20261013` on both nodes, with the directions baked at `/opt/refusal/refusal_dirs.safetensors`; weights `deepseek-ai/DeepSeek-V4-Flash-0731` COMPLETE on both nodes.

- [ ] **Step 1:** Start the download in the background on the head: `hf download deepseek-ai/DeepSeek-V4-Flash-0731` with the token passed inline. 155.4 GiB.
- [ ] **Step 2:** `git clone https://github.com/pocharlies/deepseek-v4-flash-rank1-refusal-projection` into the session scratch directory; record `git rev-parse HEAD`.
- [ ] **Step 3:** `docker pull ghcr.io/anemll/dspark-vllm-gx10:0.1.1`. Assemble the build context the Dockerfile expects (`patches/0001-rank1-projection.patch`, `hf/refusal_dirs.safetensors` or the HF download of it, `test_refusal_per_request.py`) and `docker build -f deploy/Dockerfile -t spark-forge/vllm-dsv4-rank1:20261013 .`. Expected: build succeeds; its in-build tests pass. A failed build stops the task.
- [ ] **Step 4:** `docker save spark-forge/vllm-dsv4-rank1:20261013 | ssh devops@10.10.20.11 docker load`. Expected: same image ID on both nodes.
- [ ] **Step 5:** When the download ends, hardlink blobs, `rsync -aH` the repo directory to the worker, and run the regenerate script on both nodes. Expected: `COMPLETE`, 155.4 GiB each.
- [ ] **Step 6:** Write `images/deepseek-rank1/README.md` with the four provenance facts.

### Task 4: DeepSeek V4 Flash 0731 recipes (stock and refusal dial)

**Files:**
- Create: `recipes/deepseek-v4-flash-0731-tp2.yaml`, `recipes/deepseek-v4-flash-0731-refusal-dial-tp2.yaml`
- Modify: `INDEX.md` (rows 60, 61), `MODELS.md`

**Interfaces:**
- Consumes: Task 3's image and weights.
- Produces: served model names `deepseek-v4-flash-0731` and `deepseek-v4-flash-0731-dial`; admin route `POST /admin/refusal_lambda {"lambda": <float>}` on the dial recipe.

- [ ] **Step 1:** Create the stock recipe from `sparkrun recipe export @official/deepseek-v4-flash-0731-b12x-dspark-vllm`. Changes: attribution header; `container: ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926`; `max_nodes: 2`; `load_format: safetensors` in place of `instanttensor` and no `mods:`; `gpu_memory_utilization: 0.82`; `kv_cache_dtype: nvfp4_ds_mla` if the image accepts it, else `fp8`; `max_model_len: 262144`; a `readiness:` block copied from row 48's recipe; `served_model_name: deepseek-v4-flash-0731`.
- [ ] **Step 2:** Validate, dry-run, launch, and test as in Task 2 steps 4–6, with expected `max_model_len` `262144`. Stop. Record numbers.
- [ ] **Step 3:** Create the dial recipe: `container: spark-forge/vllm-dsv4-rank1:20261013`, `executor_config: {entrypoint: ""}`, `env: {VLLM_REFUSAL_DIRS: /opt/refusal/refusal_dirs.safetensors}`, upstream serve settings (`--tensor-parallel-size 2`, DSpark `num_speculative_tokens 5` probabilistic, B12X backends, `--kv-cache-dtype nvfp4_ds_mla`, `--max-model-len 393216`, `--max-num-seqs 4`, `--max-num-batched-tokens 8192`, `--long-prefill-token-threshold 1024`, `--enable-prefix-caching`), `gpu_memory_utilization: 0.82`, `served_model_name: deepseek-v4-flash-0731-dial`. No `post_exec` that sets lambda. Header carries the two `curl` calls and the prompt-injection warning from the Qwen dial recipe.
- [ ] **Step 4:** Validate, dry-run, launch.
- [ ] **Step 5: Test.** `max_model_len` equals `393216` (if the engine refuses that size, lower to `262144`, relaunch, and state the measured value in the recipe). At boot, one harmful-split prompt is refused. After `curl -XPOST http://10.10.20.10:8000/admin/refusal_lambda -d '{"lambda": 1.5}'` the same prompt is answered. After setting `0` it is refused again. 20 sequential requests return 200.
- [ ] **Step 6:** Stop. Write measured numbers into both recipe headers, `INDEX.md` and `MODELS.md`.

### Task 5: GLM-5.3 Flash abliterated

**Blocked until** the account behind sparkrun's HF token has accepted the terms at `https://huggingface.co/drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45`. Check with `hf download <repo> config.json`; a 403 means not yet.

**Files:**
- Create: `recipes/glm-5.3-flash-abliterated-nvfp4-tp2.yaml`
- Modify: `INDEX.md` (row 62), `MODELS.md`

- [ ] **Step 1:** Download the repo (197.8 GB) and `incoai/GLM-5.3-Flash-DFlash2` on the head; hardlink; rsync both to the worker; regenerate script prints `COMPLETE` on both nodes.
- [ ] **Step 2:** `docker save ghcr.io/tonyd2wild/vllm-glm53-flash:sm121-v11-dflash2 | ssh devops@10.10.20.11 docker load` if the worker lacks it.
- [ ] **Step 3:** Clone `https://github.com/tonyd2wild/GLM-5.3-Flash-NVFP4-DFlash2-2x-DGX-Spark`, record the commit, and read its DFlash2 TP2 launcher. Apply its "SM121 top-k fix" on both nodes exactly as its README step 3 describes; if that step needs root, hand it to the user and wait.
- [ ] **Step 4:** Create the recipe with the launcher's flags carried over verbatim, except: `gpu_memory_utilization: 0.82` (repo ceiling; upstream uses 0.85), no `--quantization` flag, no `--kv-cache-memory` pin, `--block-size 2304`, `--kv-cache-dtype fp8`, `--max-model-len 262144`, `--chat-template` pointing at the snapshot's `chat_template.thinking-off.jinja`, `executor_config: {entrypoint: ""}`, `served_model_name: glm-5.3-flash-abliterated`. Speculative config uses the cached DFlash2 snapshot path with `num_speculative_tokens: 7`.
- [ ] **Step 5:** Validate, dry-run, launch.
- [ ] **Step 6: Test.** Read `max_model_len`. If the engine fails with a KV-memory error at 262144, relaunch at 131072 and record that. Below 131072 counts as unfit: stop, record UNFIT with the log line, and report the Mia-AiLab EXL3 fallback to the user instead of downloading it. Otherwise: one completion with non-empty content and no `<think>` text in `content`; one harmful-split prompt answered; 20 sequential requests return 200.
- [ ] **Step 7:** Stop. Record numbers in the recipe header, `INDEX.md`, `MODELS.md`.

### Task 5b: GLM-5.3 Flash abliterated, long-context profile (NVFP4 KV)

Run only after Task 5 has a verified recipe. Source:
`github.com/drowzeys/keys-vLLm.0.27.1-GLM-5.3-Flash-NVFP4-NVFP4KV-1M-Context-Abliterated`
(Apache-2.0, last pushed 2026-08-31), which reports 1,048,576 context on
2× GB10 for this checkpoint family using an `nvfp4_ds_mla` KV cache.

**Files:**
- Create: `recipes/glm-5.3-flash-abliterated-nvfp4kv-long-tp2.yaml`
- Create: `mods/glm53-nvfp4kv-overlays/` (the repo's `overlays/official` and `overlays/nvfp4-b12x` trees at a recorded commit, with its LICENSE and CREDITS)
- Modify: `INDEX.md` (row 63), `MODELS.md`

- [ ] **Step 1:** Clone the repo, record the commit, read `launcher/launch.sh`, `oneshot.sh` and `docs/WALLS.md`. The repo predates the checkpoint's 2026-09-27 re-publish (RedHat body, 10 shards, `index_topk` 2048 in `config.json`); confirm from `oneshot.sh` how the `index_topk=2044` sibling config is produced and whether it still applies to the 10-shard layout. If it does not, stop and report; do not edit the cached checkpoint in place.
- [ ] **Step 2:** `docker pull ghcr.io/drowzeys/keys-vllm-glm53-flash-nvfp4-ablit:b12x-cu130`, retag it `…:b12x-cu130-20261013`, and load it on the worker.
- [ ] **Step 3:** Create the recipe from the launcher's emitted serve args: `--tensor-parallel-size 2`, `--moe-backend marlin`, `--enforce-eager`, `--attention-backend B12X_MLA_SPARSE`, `--kv-cache-dtype nvfp4_ds_mla`, env `KV_FP8_ROPE=1`, `--block-size 7168`, `--max-num-batched-tokens 4096`, `--max-num-seqs 2`, prefix caching off, MTP k=2, parsers `glm45`/`glm47`, overlays mounted through `mods:`. Local changes: `gpu_memory_utilization: 0.82` (upstream's 0.85 is over this repo's ceiling), no `--kv-cache-memory` pin, `--max-model-len 524288` for the first boot, `served_model_name: glm-5.3-flash-abliterated-long`.
- [ ] **Step 4:** Validate, dry-run, launch.
- [ ] **Step 5: Test.** Read `max_model_len`; expect `524288`. Run a needle-in-haystack prompt at about 250k tokens with `free -m` sampled on both nodes every 10 s; abort the request if either node drops below 2,000 MB available. Needle returned correctly and 20 sequential short requests return 200. Only if that passes with at least 4 GB spare on both nodes, relaunch at `1048576` and repeat with a 500k-token needle. Record the largest context that passed; never claim 1M unless a prompt near 1M was answered.
- [ ] **Step 6:** Stop. Record numbers in the header, `INDEX.md`, `MODELS.md`.

### Task 6: Gated weight deletions

**Blocked until the user says yes to each item by name.**

- [ ] `orcarouter/Qwen3.8-Flash-Next-Uncensored-NVFP4`, 170.9 GiB on each node.
- [ ] `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw`, 81.6 GiB partial, head.
- [ ] `nvidia/DeepSeek-V4-Flash-NVFP4` stub plus `recipes/deepseek-v4-flash-nvfp4-atlas-ep2.yaml` and its `INDEX.md` row 58.

For each approved item: back up to `/mnt/nas/dgx-spark/model-backup/` only if the user asks for a backup, delete, run `df -h` before and after, and update `MODELS.md`.

### Task 7: Records

**Files:** `HISTORY.md`, `INDEX.md`, `MODELS.md`, `CLAUDE.md`

- [ ] **Step 1:** Append a 2026-10-13 entry to `HISTORY.md`: what was surveyed, what was added and removed, each recipe's bar, measured numbers, anything left unfit, and the open deletions.
- [ ] **Step 2:** Re-run the regenerate script on both nodes and reconcile `MODELS.md` family table and stub lists with its output.
- [ ] **Step 3: Test.** `for f in recipes/*.yaml; do sparkrun recipe validate "$f" >/dev/null || echo "FAIL $f"; done`. Expected: no `FAIL` lines. Every `model:` in `recipes/` either prints `COMPLETE` on the nodes it needs or is listed in `MODELS.md` as not downloaded.
- [ ] **Step 4:** Report to the user what is uncommitted and ask whether to commit and run `sparkrun registry update spark-forge`.
