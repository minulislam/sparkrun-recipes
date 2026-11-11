# Design Doc: Runtime Refusal Dial for Thinking Machines Inkling-Small NVFP4 via vLLM

- **Date**: 2026-11-10
- **Author**: Antigravity & Operator
- **Status**: Proposed (Revised for vLLM Runtime)
- **Target Model**: `thinkingmachines/Inkling-Small-NVFP4` (276B MoE / 12B active, 42 layers, 1M context)
- **Runtime**: vLLM (`ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926` / `spark-forge/vllm-inkling-rank1`)
- **Cluster**: 2× DGX Spark (`gb10-spark` 10.10.20.10, `gx10-spark` 10.10.20.11), TP=2

---

## 1. Intent & The Why

In `sparkrun-recipes`, the runtime refusal dial pattern—proven in [`qwen38-27b-nvfp4-refusal-dial.yaml`](file:///home/devops/workspace/sparkrun-recipes/recipes/qwen38-27b-nvfp4-refusal-dial.yaml) and [`deepseek-v4-flash-0731-refusal-dial-tp2.yaml`](file:///home/devops/workspace/sparkrun-recipes/recipes/deepseek-v4-flash-0731-refusal-dial-tp2.yaml)—is standardized on **vLLM**:
1. **Proven hook architecture**: vLLM's `RowParallelLinear` hook in `refusal_projection.py` provides exact rank-1 orthogonal projection ($y \leftarrow y - \lambda \cdot \hat{r}(\hat{r}^T y)$) without touching quantized model weights.
2. **Native Inkling support**: The verified nightly image `ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926` on our cluster already includes native support for `InklingForConditionalGeneration` and `InklingForCausalLM` (`vllm.models.inkling.nvidia.model`).
3. **Identical recipe contract**: Using vLLM allows the upcoming Inkling recipe to match the exact setup of our existing Qwen and DeepSeek refusal-dial recipes (`pre_exec` verification, `post_exec` curl initialization, `/admin/refusal_lambda`, and `post_commands`).
4. **Bit-exact stock baseline**: At $\lambda=0.0$, the serving endpoint is byte-for-byte and mathematically identical to the official stock model.

---

## 2. Goals, Non-Goals & Anti-Goals

### Goals
- **Direction extraction**: Extract layer-wise rank-1 refusal directions ($\hat{r}_l$) across Inkling-Small's 42 transformer layers via `benchmarks/redteam/extract_contrastive_directions.py` using contrastive prompt pairs (harmful vs. matched benign).
- **vLLM Refusal Hook**: Leverage the existing, verified `refusal_projection.py` hook on `RowParallelLinear` / attention output in vLLM.
- **Mutable device lambda ($\lambda$)**: Maintain $\lambda$ as an in-place device tensor buffer so CUDA graph capture does not freeze the dial value.
- **Admin HTTP endpoint**: Standard vLLM `/admin/refusal_lambda` route for hot $\lambda$ adjustment without restart.
- **Sparkrun recipe**: Deliver `recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml` matching the exact schema and lifecycle of `qwen38-27b-nvfp4-refusal-dial.yaml`.
- **Dual-split validation**: Measure and record compliance using [`benchmarks/redteam/run_refusal_eval.py`](file:///home/devops/workspace/sparkrun-recipes/benchmarks/redteam/run_refusal_eval.py) on both 100 harmful prompts and 100 matched benign controls.

### Non-Goals
- **Weight modification**: No offline baking or re-quantization of model weights.
- **Alternative runtimes**: SGLang is replaced entirely by vLLM to maintain a uniform refusal-dial architecture across the fleet.

---

## 3. System Architecture & Component Details

```mermaid
flowchart TD
    subgraph Offline Extraction
        JBB["Harmful Prompts (JBB)<br/>Benign Controls"] --> Extractor["extract_contrastive_directions.py"]
        Extractor --> Dirs["refusal_dirs_inkling.safetensors<br/>(42 layers x 4096 floats ~350 KB)"]
    end

    subgraph vLLM Runtime (TP=2)
        Dirs --> Mount["VLLM_REFUSAL_DIRS env"]
        Mount --> Hook["vLLM RowParallelLinear Hook<br/>y <- y - lambda * r (r^T y)"]
        Admin["POST /admin/refusal_lambda"] --> DeviceTensor["Device Buffer: lambda_tensor"]
        DeviceTensor --> Hook
    end

    subgraph Verification
        Hook --> Serve["HTTP :8000/v1/chat/completions"]
        Serve --> Eval["run_refusal_eval.py<br/>(100 Harmful + 100 Benign)"]
    end
```

### 3.1 Direction Extraction
- **Harness**: `benchmarks/redteam/extract_contrastive_directions.py`.
- **Prompt set**: 32 representative harmful prompts selected from JailbreakBench (covering cyber, deception, harassment, CBRN, illegal acts) and 32 length-matched benign prompts.
- **Sampling position**: Captured at the **final token of the prompt prefix** (index `-1`) where the refusal decision crystallizes.
- **Serialization**: Saved as `refusal_dirs_inkling.safetensors` containing tensors `layers.{l}.r` of shape `[4096]`, dtype `float32`.

### 3.2 Recipe Specification: `recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml`
Adheres strictly to the canonical refusal-dial setup from [`recipes/qwen38-27b-nvfp4-refusal-dial.yaml`](file:///home/devops/workspace/sparkrun-recipes/recipes/qwen38-27b-nvfp4-refusal-dial.yaml):

```yaml
recipe_version: "2"
model: thinkingmachines/Inkling-Small-NVFP4
runtime: vllm
container: spark-forge/vllm-inkling-rank1:20261110  # or ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x with refusal mod
min_nodes: 2
max_nodes: 2

executor_config:
  entrypoint: ""

env:
  VLLM_REFUSAL_DIRS: /opt/refusal/refusal_dirs_inkling.safetensors
  VLLM_REFUSAL_LAMBDA_INIT: "1.0"
  VLLM_ALLOW_LONG_MAX_MODEL_LEN: "1"
  PYTORCH_CUDA_ALLOC_CONF: "expandable_segments:True"

defaults:
  port: 8000
  host: 0.0.0.0
  tensor_parallel: 2
  gpu_memory_utilization: 0.85
  max_model_len: 262144
  served_model_name: inkling-small

pre_exec:
  - python3 /opt/refusal/verify_inkling_rank1.py

post_exec:
  - curl -s localhost:{port}/v1/models
  - 'curl -s -XPOST localhost:{port}/admin/refusal_lambda -H ''Content-Type: application/json'' -d ''{{"lambda": 1}}'''
  - curl -s localhost:{port}/admin/refusal_lambda

post_commands:
  - 'echo "ablation on:  curl -XPOST {head_host}:{port}/admin/refusal_lambda -d ''{{\"lambda\": 1}}''"'
  - 'echo "ablation off: curl -XPOST {head_host}:{port}/admin/refusal_lambda -d ''{{\"lambda\": 0}}''"'

command: |
  vllm serve {model} \
    --served-model-name {served_model_name} \
    --host {host} \
    --port {port} \
    -tp {tensor_parallel} \
    --gpu-memory-utilization {gpu_memory_utilization} \
    --max-model-len {max_model_len} \
    --trust-remote-code \
    --enable-prefix-caching
```

---

## 4. Operational & Verification Plan

1. **Pre-flight & Weight Sync**:
   - Confirm idle cluster state (`rtk sparkrun status`).
   - Sync 159 GiB shards from `gb10-spark` to `gx10-spark`:
     `rsync -avP ~/.cache/huggingface/hub/models--thinkingmachines--Inkling-Small-NVFP4/ devops@10.10.20.11:~/.cache/huggingface/hub/models--thinkingmachines--Inkling-Small-NVFP4/`.
2. **Extraction**:
   - Run contrastive extraction with vLLM prefill runner to produce `refusal_dirs_inkling.safetensors`.
   - Verify tensor sanity (`python3 /opt/refusal/verify_inkling_rank1.py`).
3. **Launch & Admin Verification**:
   - `sparkrun run recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml`.
   - Confirm readiness and verify toggle:
     `curl -XPOST localhost:8000/admin/refusal_lambda -d '{"lambda": 0}'` (off)
     `curl -XPOST localhost:8000/admin/refusal_lambda -d '{"lambda": 1}'` (on)
4. **Evaluation**:
   - Run `benchmarks/redteam/run_refusal_eval.py --base http://127.0.0.1:8000/v1 --model inkling-small --split both --out benchmarks/redteam/results/inkling-small-refusal-dial.jsonl`.
   - Verify compliance $\ge 95\%$ on both harmful and benign splits at $\lambda=1.0$, and expected refusal at $\lambda=0.0$.
