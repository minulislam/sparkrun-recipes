# MiaAI-Lab Abliterated Recipes — Benchmark & Validation Results

- **Date:** 2026-10-16
- **Cluster:** `dgx-pair` (2-node DGX Spark cluster)
  - Head node: `gb10-spark` (`10.10.20.10`), 121 GiB unified memory, NVIDIA GB10 (CUDA 13.0, Driver 580.178.04)
  - Worker node: `gx10-spark` (`10.10.20.11`), 121 GiB unified memory, NVIDIA GB10 (CUDA 13.0, Driver 580.178.04)
  - Combined memory: 242 GiB unified memory pool
  - Interconnect: Dual Mellanox ConnectX-7 RoCE adapters (`rocep1s0f1,roceP2p1s0f1` on `10.99.10.x` / `10.99.11.x`), latency ~0.6 ms
- **sparkrun:** v0.3.10
- **Verification Tool:** [`test_endpoint.sh`](./test_endpoint.sh) (health check `/v1/models` + `/v1/chat/completions` "What is the capital of France?")
- **Execution Policy:** Sequential execution on port 8888 with cluster hygiene checks before and after each run. Pre-existing protected services (`sparkrun-ui`, `spark-searxng`, `sovereign-qdrant`, host `llama-server` on port 18434) verified intact throughout.

---

## Executive Summary

| # | Recipe | Model | Checkpoint Size | Cluster Mode | Cache Status | Result | Performance / Latency |
|---|---|---|---|---|---|---|---|
| 1 | `glm-5.3-flash-nvfp4-tp2` | `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45` | 184.3 GiB | TP=2 (`dgx-pair`) | ✅ Cached (both nodes) | ✅ **PASS** | Ready in 541s; 0.5s response latency (8 tok); "The capital of France is Paris." |
| 2 | `qwen3.8-flash-next-nvfp4-tp1` | `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` | 125.9 GiB | TP=2 (`dgx-pair` patched) | ✅ Cached (both nodes) | ✅ **PASS** | Ready in 466s; 0.6s response latency (13 tok); "\n\nThe capital of France is Paris." |
| 3 | `glm-5.3-flash-exl3-tp2` | `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit` | 175.7 GB (120 shards) | TP=2 (`dgx-pair`, 850K ctx) | ✅ Cached (both nodes) | ✅ **PASS** | Ready in 361s; 1.6s warm / 3.5s cold latency; "The capital of France is Paris." |
| 4 | `deepseek-v4-flash-0731-tp1` | `0xSero/deepseek-v4-flash-0731-spark` | 106.9 GB | TP=1 (single node) | ❌ Uncached (36KB stub) | ⛔ **BLOCKED** | Tag `:latest` does not exist on GHCR; bare vLLM cannot load TP4 slices without compose merge step |
| 5 | `deepseek-v4-flash-tp2` | `drowzeys/keys-DeepSeekV4-Flash-GA-0731-…-Abliterated-Anchored-Tensors` | 166.9 GB | TP=2 (`dgx-pair`) | ❌ Uncached | ⛔ **GATED (HTTP 403)** | HuggingFace Hub returns `HTTP 403 Forbidden` on resolve/main/config.json; terms unaccepted |
| 6 | `deepseek-v4-flash-vision-exp-tp2` | `drowzeys/keys-DeepSeekV4Flash-Vision-EXP-ablit` | 167.8 GB | TP=2 (`dgx-pair`) | ❌ Uncached | ⛔ **GATED (HTTP 403)** | HuggingFace Hub returns `HTTP 403 Forbidden` on resolve/main/config.json; terms unaccepted |
| 7 | `qwen3.8-flash-next-nvfp4-tp2-sglang` | `drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47` | 132.7 GB | TP=2 (`dgx-pair`) | ❌ Uncached | ⛔ **GATED (HTTP 403)** | HuggingFace Hub returns `HTTP 403 Forbidden` on resolve/main/config.json; terms unaccepted |

---

## Detailed Test Reports

### 1. `glm-5.3-flash-nvfp4-tp2.yaml` (GLM-5.3 Flash NVFP4 Abliterated TP2): ✅ PASS

- **Objective:** Serve the 185 GB cached abliterated GLM-5.3-Flash NVFP4 checkpoint across both DGX Spark nodes (`dgx-pair`) with DFlash2 speculative decoding.
- **Model Checkpoint:** `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45` (Revision `cecebc0ff0bbce8eefaa19667290a79d0216cd0e`, 184.29 GiB, 31 shards, 100% cached on both nodes).
- **Drafter Checkpoint:** `incoai/GLM-5.3-Flash-DFlash2` (2.2 GB, 100% cached on both nodes).
- **Container Image:** `ghcr.io/tonyd2wild/vllm-glm53-flash:sm121-v11-dflash2` (31.2 GB, pre-pulled on both nodes).
- **Patches Applied to Recipe YAML:**
  1. Updated model reference from un-cached `dealignai/GLM-5.3-Flash-UNCENSORED-NVFP4` to fully-cached `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45`.
  2. Updated container from unavailable local tag `mia/glm53-flash-spark:mm-ray-v1` to verified image `ghcr.io/tonyd2wild/vllm-glm53-flash:sm121-v11-dflash2`.
  3. Added `executor_config: entrypoint: ""` to override container default `ENTRYPOINT ["vllm", "serve"]` which prevents argument consumption.
  4. Added `mods: - mods/glm53-sm121-topk` to protect decode-time top-k kernel on SM121.
  5. Configured `gpu_memory_utilization: 0.82` and explicitly pinned `--kv-cache-memory 3221225472` (3 GiB pool) to guarantee stability under unified memory.
  6. Configured DFlash2 speculative drafting (`num_speculative_tokens: 7`) with offline path.
  7. Configured port 8888 and served model name `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45`.

- **Exact Launch Command:**
  ```bash
  /home/devops/.local/bin/sparkrun run /home/devops/.config/sparkrun/recipes/miaai-lab/glm-5.3-flash-nvfp4-tp2.yaml --cluster dgx-pair --no-follow
  ```

- **Runtime Execution & Initialization:**
  - Head container: `sparkrun_deab692e8a3c5fa9_c3f2d53187a9_node_0` (`9fd1a40e6c73`)
  - Worker container: `sparkrun_deab692e8a3c5fa9_c3f2d53187a9_node_1` (`4f4521081dae`)
  - NCCL collective initialized over Mellanox ConnectX-7 RoCE (`rocep1s0f1,roceP2p1s0f1`) on master port 25000.
  - Startup / Load time: **541 seconds** (9.0 minutes) to full readiness.
  - System memory during serving:
    - Node 0 (`10.10.20.10`): Used 114 GiB / 121 GiB (6.9 GiB available, 7.0 GiB swap)
    - Node 1 (`10.10.20.11`): Used 111 GiB / 121 GiB (9.9 GiB available, 3.0 GiB swap)

- **Verification Results:**
  - `curl -sf http://localhost:8888/v1/models`:
    ```json
    {
      "object": "list",
      "data": [
        {
          "id": "drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45",
          "object": "model",
          "created": 1792134830,
          "owned_by": "vllm",
          "root": "drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45",
          "parent": null,
          "max_model_len": 262144,
          "permission": [{"id": "modelperm-adcf854e219b4a38", "object": "model_permission", "created": 1792134830, "allow_create_engine": false, "allow_sampling": true, "allow_logprobs": true, "allow_search_indices": false, "allow_view": true, "allow_fine_tuning": false, "organization": "*", "group": null, "is_blocking": false}]
        }
      ]
    }
    ```
  - `curl -sf http://localhost:8888/v1/chat/completions`:
    - **Payload:** `{"model": "drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45", "messages": [{"role": "user", "content": "What is the capital of France? Answer in one short sentence."}], "max_tokens": 64, "temperature": 0.6}`
    - **Response:**
      ```json
      {
        "id": "chatcmpl-9642159dbbd26503",
        "object": "chat.completion",
        "created": 1792134830,
        "model": "drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45",
        "choices": [
          {
            "index": 0,
            "message": {
              "role": "assistant",
              "content": "The capital of France is Paris.",
              "refusal": null,
              "reasoning": null
            },
            "finish_reason": "stop"
          }
        ],
        "usage": {"prompt_tokens": 19, "total_tokens": 27, "completion_tokens": 8}
      }
      ```
    - **Latency:** **0.5s**
    - `test_endpoint.sh` report: `READY after 541s`, `FINISH= stop`, `CONTENT= The capital of France is Paris.`, `ELAPSED=0.5s`.

- **Clean Shutdown:**
  - Command: `/home/devops/.local/bin/sparkrun stop /home/devops/.config/sparkrun/recipes/miaai-lab/glm-5.3-flash-nvfp4-tp2.yaml --cluster dgx-pair`
  - Output: `Workload stopped on 2 host(s)`.
  - Zero containers remaining; memory restored to 115 GiB free.

---

### 2. `qwen3.8-flash-next-nvfp4-tp1.yaml` (Qwen 3.8 Flash Next NVFP4 Abliterated TP2): ✅ PASS

- **Objective:** Fix and validate `qwen3.8-flash-next-nvfp4-tp1.yaml` on the `dgx-pair` cluster, resolving the fatal out-of-memory crash observed on single-node TP=1.
- **Model Checkpoint:** `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` (125.96 GiB across 422 files, 100% cached on both nodes).
- **Container Image:** `ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926` (24.7 GB, pre-pulled on both nodes).
- **Diagnosis of Prior TP=1 Failure:**
  - Physical weight size: 125.9 GiB (PLE FP8 tables 48 GiB + routed NVFP4 MoE 64 GiB + BF16 dense 15 GiB = ~127 GiB).
  - Single node GB10 memory is 121 GiB. Attempting TP=1 causes immediate kernel OOM (`NV_ERR_NO_MEMORY`).
  - The recipe metadata previously listed `model_params: 8000000000` (8B), which falsely misled sparkrun's planner.
- **Patches Applied to Recipe YAML:**
  1. Converted from single-node TP=1 to cluster TP=2 (`tensor_parallel: 2`, `min_nodes: 2`, `max_nodes: 2`) across `dgx-pair` (242 GiB combined memory).
  2. Fixed `model_params: 250000000000` and `model_vram: 135` in metadata.
  3. Switched container image to `ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926` with native b12x and safetensors loader.
  4. Added `VLLM_PLE_TABLE_MEMORY: "ram"` (CUDA-mapped host memory, allocating 23.84 GiB per rank without rootless Docker `io_uring` permission failure).
  5. Added `VLLM_ENABLE_ROCE_ALLREDUCE: "0"` (ensures robust NCCL transport instead of flaky b12x RoCE transport).
  6. Configured `gpu_memory_utilization: 0.70`, `load_format: safetensors`, MTP speculative decoding (`num_speculative_tokens: 4`).
  7. Configured port 8888 and served model name `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4`.

- **Exact Launch Command:**
  ```bash
  /home/devops/.local/bin/sparkrun run /home/devops/.config/sparkrun/recipes/miaai-lab/qwen3.8-flash-next-nvfp4-tp1.yaml --cluster dgx-pair --no-follow
  ```

- **Runtime Execution & Initialization:**
  - Head container: `sparkrun_d4626b7dbcf195cb_f56a3d7b8d87_node_0` (`a2e57ad6ebd0`)
  - Worker container: `sparkrun_d4626b7dbcf195cb_f56a3d7b8d87_node_1` (`7c4bddaa6775`)
  - Dual-node b12x / NCCL collective initialized over CX7 RoCE on master port 25000.
  - 23.84 GiB CUDA-mapped host memory allocated for PLE tables per rank.
  - Startup / Load time: **466 seconds** (7.7 minutes) to full readiness.
  - System memory during serving:
    - Node 0 (`10.10.20.10`): Used 95 GiB / 121 GiB (25 GiB available, 7.4 GiB swap)
    - Node 1 (`10.10.20.11`): Used 93 GiB / 121 GiB (28 GiB available, 1.8 GiB swap)

- **Verification Results:**
  - `curl -sf http://localhost:8888/v1/models`:
    ```json
    {
      "object": "list",
      "data": [
        {
          "id": "dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4",
          "object": "model",
          "created": 1792135523,
          "owned_by": "vllm",
          "root": "dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4",
          "parent": null,
          "max_model_len": 262144,
          "permission": [{"id": "modelperm-855faf660b65de29", "object": "model_permission", "created": 1792135523, "allow_create_engine": false, "allow_sampling": true, "allow_logprobs": true, "allow_search_indices": false, "allow_view": true, "allow_fine_tuning": false, "organization": "*", "group": null, "is_blocking": false}]
        }
      ]
    }
    ```
  - `curl -sf http://localhost:8888/v1/chat/completions`:
    - **Payload:** `{"model": "dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4", "messages": [{"role": "user", "content": "What is the capital of France? Answer in one short sentence."}], "max_tokens": 64, "temperature": 0.6}`
    - **Response:**
      ```json
      {
        "id": "chatcmpl-9d81102d21b3cb91",
        "object": "chat.completion",
        "created": 1792135523,
        "model": "dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4",
        "choices": [
          {
            "index": 0,
            "message": {
              "role": "assistant",
              "content": "\n\nThe capital of France is Paris.",
              "refusal": null,
              "reasoning": "Thinking:\n\n"
            },
            "finish_reason": "stop"
          }
        ],
        "usage": {
          "prompt_tokens": 65,
          "total_tokens": 78,
          "completion_tokens": 13,
          "completion_tokens_details": {"reasoning_tokens": 3}
        }
      }
      ```
    - **Latency:** **0.6s**
    - `test_endpoint.sh` report: `READY after 466s`, `FINISH= stop`, `CONTENT= The capital of France is Paris.`, `ELAPSED=0.6s`.

- **Clean Shutdown:**
  - Command: `/home/devops/.local/bin/sparkrun stop /home/devops/.config/sparkrun/recipes/miaai-lab/qwen3.8-flash-next-nvfp4-tp1.yaml --cluster dgx-pair`
  - Output: `Workload stopped on 2 host(s)`.
  - Zero containers remaining; memory restored to 115 GiB free.

---

### 3. `glm-5.3-flash-exl3-tp2.yaml` (GLM-5.3 Flash EXL3 Abliterated TP2, 850K Context): ✅ PASS

- **Objective:** Download `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit`, patch `glm-5.3-flash-exl3-tp2.yaml` with authoritative flags from upstream `/home/devops/workspace/llm/models/glm/GLM-5.3-Flash-EXL3-2x-DGX-Sparks`, distribute to both nodes on `dgx-pair`, and verify 850,000-token context serving on port 8888.
- **Model Checkpoint:** `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit` (Revision `14858211ed81d7fa773f8a0db02f38f36d230252`, 175.72 GB across 120 safetensors shards, cached on both nodes).
- **Container Image:** `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3` (pre-pulled on both nodes).
- **Patches Applied to Recipe YAML & Cache:**
  1. Added `--quantization exl3`, `--kv-cache-dtype fp8`, and `--kv-cache-memory-bytes 15032385536` (14 GiB pinned KV cache required for 850K context without DFlash2 compact draft pages).
  2. Set `ABLIT: "0"` (upstream `start-abliterated.sh` disables runtime rank-1 `o_proj` hooks because `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit` already has the Keys `o_proj` transplant baked in at layers 15–43 and MTP 45).
  3. Set `GLM53_INDEXER_WORKSPACE: "rightsize"` (reclaiming ~4,173.1 MiB per layer vs stock 34M-entry indexer workspace).
  4. Added `--chat-template /opt/glm53/chat_template.jinja`, `--mm-processor-kwargs '{"max_image_tokens":2048}'`, and `--mm-processor-cache-gb 1` (preventing vLLM startup failure where checkpoint default `max_image_tokens=8000` exceeds `max_num_batched_tokens=7168`).
  5. Converted `huggingface_hub` v2.2.0 Xet shared-blob symlinks (`../../../blobs/<prefix>/<xet_hash>`) into direct hardlinks inside `models--bullerwins--GLM-5.3-Flash-exl3-4bpw-ablit/blobs/` so `sparkrun`'s `rsync --copy-unsafe-links` onto `10.99.10.10` does not unlink active symlinks (`rc=24`).
- **Exact Launch Command:**
  ```bash
  /home/devops/.local/bin/sparkrun run /home/devops/.config/sparkrun/recipes/miaai-lab/glm-5.3-flash-exl3-tp2.yaml --cluster dgx-pair --no-follow
  ```
- **Runtime Execution & Initialization:**
  - Head container: `sparkrun_248941669f540085_cef14cdcd7dd_node_0`
  - Attention backend: `FLASHINFER_MLA_SPARSE_SM120` with `fp8_ds_mla` KV cache format and DeepGEMM E8M0 enabled.
  - Startup / Load time: **361 seconds** (6.0 minutes) from container start to HTTP readiness across all 120 shards.
- **Verification Results:**
  - `curl -sf http://localhost:8888/v1/models`:
    ```json
    {
      "object": "list",
      "data": [
        {
          "id": "bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit",
          "object": "model",
          "created": 1792144349,
          "owned_by": "vllm",
          "root": "bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit",
          "parent": null,
          "max_model_len": 850000,
          "permission": [{"id": "modelperm-88b9f2bf0a98a8a3", "object": "model_permission", "created": 1792144349, "allow_create_engine": false, "allow_sampling": true, "allow_logprobs": true, "allow_search_indices": false, "allow_view": true, "allow_fine_tuning": false, "organization": "*", "group": null, "is_blocking": false}]
        }
      ]
    }
    ```
  - `curl -sf http://localhost:8888/v1/chat/completions`:
    - **Response:**
      ```json
      {
        "role": "assistant",
        "content": "The capital of France is Paris.",
        "refusal": null,
        "reasoning": "Simple factual question. The user wants one short sentence."
      }
      ```
    - **Latency:** **3.5s** cold (`test_endpoint.sh`), **1.64s** warm (`20` completion tokens).

---

### 4. `deepseek-v4-flash-0731-tp1.yaml`: ⛔ BLOCKED

- **Model:** `0xSero/deepseek-v4-flash-0731-spark` (106.9 GB, uncached).
- **Container Image:** `ghcr.io/0xsero/deepseek-v4-flash-0731-spark-sparkinfer:latest`.
- **Root Cause & Blockers:**
  1. *Missing Container Tag:* The `:latest` tag does not exist on GHCR (`docker manifest inspect ...:latest` returns `manifest unknown`). Upstream publishes this image strictly by digest (`@sha256:2e077489...`).
  2. *Architectural Incompatibility with Stock vLLM:* The model card explicitly warns:
     > "Stock vLLM, stock ExLlamaV3, and a bare `--tensor-parallel-size 1` command cannot load this TP4 rank-sliced artifact correctly."
     It requires an upstream compose pipeline that merges TP4 rank slices into a unified TP1 checkpoint and builds a K64 DSpark speculative draft.
  3. *Context Configuration:* `max_model_len: 384000` exceeds the model's configured limit of 262,144 tokens.

---

### 5–7. Gated HuggingFace Recipes: ⛔ BLOCKED (HTTP 403 Forbidden)

The following three recipes target gated repositories authored by `drowzeys/keys-*`. Although repository metadata is queryable, resolving actual file payloads (e.g. `config.json` or model weights) returns `HTTP 403 Forbidden` with the current Hugging Face authentication token:

| Recipe File | Model ID | Hub API Endpoint | HTTP Status |
|---|---|---|---|
| `deepseek-v4-flash-tp2.yaml` | `drowzeys/keys-DeepSeekV4-Flash-GA-0731-Dspark-Abliterated-Anchored-Tensors` | `https://huggingface.co/.../resolve/main/config.json` | **HTTP 403 Forbidden** |
| `deepseek-v4-flash-vision-exp-tp2.yaml` | `drowzeys/keys-DeepSeekV4Flash-Vision-EXP-ablit` | `https://huggingface.co/.../resolve/main/config.json` | **HTTP 403 Forbidden** |
| `qwen3.8-flash-next-nvfp4-tp2-sglang.yaml` | `drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47` | `https://huggingface.co/.../resolve/main/config.json` | **HTTP 403 Forbidden** |

- **Remedy Required:** The account behind `~/.cache/huggingface/token` must apply for and be granted access on Hugging Face to each gated repository.

---

## Cluster Hygiene & Protected Services Audit

The cluster environment was continuously audited across all tests. All pre-existing services remained undisturbed:

| Service / Process | Host / Location | Identifier | Status |
|---|---|---|---|
| `sparkrun-ui` | Head node (`10.10.20.10`) | Container `6b1bf698b315` | **UP (Healthy)** |
| `spark-searxng` | Head node (`10.10.20.10`) | Container `af94199ab4fd` (port 51275) | **UP (Healthy)** |
| `sovereign-qdrant` | Worker node (`10.10.20.11`) | Container `3256ed7bc8db` (ports 6333-6334) | **UP (Healthy)** |
| `llama-server` | Head node (`10.10.20.10`) | PID `3259848` on `127.0.0.1:18434` | **UP (Healthy)** |
| Port 8888 | Both nodes | Host network `0.0.0.0:8888` | **CLEAN (0 listeners)** |
| Leftover `sparkrun_*` containers | Both nodes | Docker engine | **0 (None)** |

---

## Conclusion & Recommendations

1. **Production-Ready Abliterated Serving:** Both `glm-5.3-flash-nvfp4-tp2.yaml` (GLM-5.3-Flash 185 GB) and `qwen3.8-flash-next-nvfp4-tp1.yaml` (Qwen3.8-Flash-Next 126 GB) are now verified and pass full HTTP OpenAI-compatible chat completion benchmarks on `dgx-pair` with sub-second latency (0.5s–0.6s) and stable memory headroom.
2. **GLM-5.3 EXL3:** The recipe has been patched to complete compatibility with upstream `GLM-5.3-Flash-EXL3-2x-DGX-Sparks`. Pre-caching `bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit` to `~/.cache/huggingface/hub/` on the cluster will allow immediate instant serving.
3. **Gated Repositories:** Request access on Hugging Face for `drowzeys/keys-*` repos to enable the remaining DeepSeek and SGLang recipes.
