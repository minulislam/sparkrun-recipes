# Inkling-Small NVFP4 Runtime Refusal Dial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement, verify, and benchmark a runtime refusal dial for `thinkingmachines/Inkling-Small-NVFP4` using vLLM on 2× DGX Spark nodes (`gb10-spark` + `gx10-spark`, TP=2), serving bit-exact stock weights at $\lambda=0.0$ and achieving $\ge 95\%$ compliance on harmful and benign benchmarks at $\lambda \ge 1.0$.

**Architecture:** Rank-1 orthogonal projection ($y \leftarrow y - \lambda \cdot \hat{r}(\hat{r}^T y)$) injected into vLLM's `InklingDecoderLayer` attention output projection via a mod overlay, powered by contrastively extracted directions (`refusal_dirs_inkling.safetensors`, ~350 KB across 42 layers). Controlled live over HTTP via `/admin/refusal_lambda` mutating an in-place device tensor without freezing under CUDA graphs.

**Tech Stack:** Python 3.12, PyTorch, vLLM (`ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926`), Safetensors, Sparkrun 0.4.2, JailbreakBench.

**Spec:** [`docs/superpowers/specs/2026-11-10-inkling-small-refusal-dial-design.md`](file:///home/devops/workspace/sparkrun-recipes/docs/superpowers/specs/2026-11-10-inkling-small-refusal-dial-design.md)

---

## Global Constraints

- **Stock weights read-only**: Under no circumstances may `thinkingmachines/Inkling-Small-NVFP4` checkpoint files be modified or re-quantized.
- **Bit-exact baseline**: At $\lambda=0.0$, output logits must match the unpatched stock model within float32 numerical precision.
- **Fail-closed pre-exec**: The server must verify that all 42 transformer layer directions exist, have valid norms ($1.0 \pm 10^{-4}$), and contain no NaNs/Infs before launching inference.
- **Recipe schema consistency**: The recipe must match the canonical refusal-dial interface of [`recipes/qwen38-27b-nvfp4-refusal-dial.yaml`](file:///home/devops/workspace/sparkrun-recipes/recipes/qwen38-27b-nvfp4-refusal-dial.yaml) (`pre_exec` verification, `post_exec` curl initialization to $\lambda=1$, `/admin/refusal_lambda` route, and `post_commands`).
- **Cluster topology**: Runs at TP=2 across head `gb10-spark` (10.10.20.10) and worker `gx10-spark` (10.10.20.11).

---

## Review Focus

1. **CUDA Graph Tensor Mutability**: If $\lambda$ is captured as a Python float or reassigned as a new tensor reference, CUDA graph replays will freeze the initial $\lambda$ value forever without error.
   - *Test pinned in Task 2*: Verify `.fill_(val)` in-place mutation leaves tensor memory address (`data_ptr()`) identical across updates.
2. **Layer Alignment and Shape Match**: If a layer direction tensor has shape mismatch (e.g. not matching hidden size 4096) or layer indices are misnamed (e.g. 0..41), projection will broadcast incorrectly or skip layers silently.
   - *Test pinned in Task 1*: Verify all 42 keys (`layers.0.r` .. `layers.41.r`) have exact shape `torch.Size([4096])` and unit norm.
3. **Prefix Cache Invalidation**: If the global dial switches $\lambda=1 \rightarrow 0$ without invalidating cached KV blocks, subsequent prompts hitting common prefixes will inherit ablated representations.
   - *Test pinned in Task 2*: Verify `/admin/refusal_lambda` triggers cache clearance.
4. **Token Slice Position**: If directions are extracted by mean-pooling the entire prompt rather than isolating the final prefix token, the direction will encode semantic topical shift rather than refusal intent.
   - *Test pinned in Task 1*: Verify extraction indexing targets index `-1` of sequence length boundaries.
5. **Multi-Node Weight Parity**: If shard files are missing or incomplete on the worker `gx10-spark`, vLLM will fail during TP=2 weight loading.
   - *Test pinned in Task 4*: Pre-flight integrity audit verifying all 10 shards exist and match size on both nodes.

---

## Tasks

### Task 1: Contrastive Refusal Direction Extractor & Verification Tool

**Files:**
- Create: `benchmarks/redteam/extract_contrastive_directions.py`
- Create: `recipes/mods/inkling-refusal-dial/verify_inkling_rank1.py`
- Test: `tests/test_refusal_extractor.py`

**Interfaces:**
- Produces: `refusal_dirs_inkling.safetensors` containing 42 tensors named `layers.{l}.r`, shape `[4096]`, dtype `float32`.
- Produces: `verify_inkling_rank1.py` CLI exit code 0 on valid safetensors, exit 1 with descriptive error on missing/corrupt layers.

- [ ] **Step 1: Write failing tests for direction calculation, normalization, and verification**

Create `tests/test_refusal_extractor.py`:
```python
import torch
import pytest
from safetensors.torch import save_file, load_file

def test_direction_computation_and_unit_norm():
    from benchmarks.redteam.extract_contrastive_directions import compute_layer_direction
    # Synthetic activations: harmful and benign clusters with known offset
    harmful = torch.randn(10, 4096) + 2.0
    benign = torch.randn(10, 4096) - 1.0
    direction = compute_layer_direction(harmful, benign)
    assert direction.shape == (4096,)
    assert torch.isclose(torch.norm(direction), torch.tensor(1.0), atol=1e-4)

def test_verify_inkling_rank1_passes_valid(tmp_path):
    from recipes.mods.inkling_refusal_dial.verify_inkling_rank1 import verify_directions
    safetensors_path = tmp_path / "valid_dirs.safetensors"
    data = {f"layers.{l}.r": torch.randn(4096) for l in range(42)}
    for k in data:
        data[k] = data[k] / torch.norm(data[k])
    save_file(data, str(safetensors_path))
    assert verify_directions(str(safetensors_path), expected_layers=42, hidden_size=4096) is True

def test_verify_inkling_rank1_fails_missing_layer(tmp_path):
    from recipes.mods.inkling_refusal_dial.verify_inkling_rank1 import verify_directions
    safetensors_path = tmp_path / "incomplete_dirs.safetensors"
    data = {f"layers.{l}.r": torch.randn(4096) for l in range(41)} # only 41 layers
    save_file(data, str(safetensors_path))
    assert verify_directions(str(safetensors_path), expected_layers=42, hidden_size=4096) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_refusal_extractor.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement extraction and verification scripts**

Implement `compute_layer_direction` and batch contrastive prompt runner in `benchmarks/redteam/extract_contrastive_directions.py`:
- Extracts hidden states at sequence index `-1`.
- Computes $\Delta \mu_l = \mu_{l, \text{harmful}} - \mu_{l, \text{benign}}$.
- Normalizes $\hat{r}_l = \Delta \mu_l / \|\Delta \mu_l\|_2$.
- Saves dictionary `{"layers.0.r": ..., "layers.41.r": ...}` using `safetensors.torch.save_file`.

Implement `recipes/mods/inkling-refusal-dial/verify_inkling_rank1.py`:
- Validates all 42 layer keys exist (`layers.0.r` through `layers.41.r`).
- Checks shape `(4096,)`, finite values (`torch.isfinite`), and unit norm (`norm == 1.0 +/- 1e-4`).
- CLI exits 0 on success, prints errors and exits 1 on failure.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_refusal_extractor.py -v`
Expected: PASS with 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_refusal_extractor.py benchmarks/redteam/extract_contrastive_directions.py recipes/mods/inkling-refusal-dial/verify_inkling_rank1.py
git commit -m "feat: add contrastive direction extraction and rank-1 verification tools for Inkling"
```

---

### Task 2: vLLM Rank-1 Refusal Projection Overlay Mod

**Files:**
- Create: `recipes/mods/inkling-refusal-dial/refusal_projection.py`
- Create: `recipes/mods/inkling-refusal-dial/admin_routes.py`
- Test: `tests/test_vllm_refusal_projection.py`

**Interfaces:**
- Consumes: `refusal_dirs_inkling.safetensors` via `VLLM_REFUSAL_DIRS`.
- Consumes: `VLLM_REFUSAL_LAMBDA_INIT` env var (defaults to `1.0`).
- Produces: `InklingRefusalProjection` class providing forward hook `project(hs, layer_id) -> torch.Tensor`.
- Produces: FastAPI router registering `GET /admin/refusal_lambda` and `POST /admin/refusal_lambda`.

- [ ] **Step 1: Write failing tests for rank-1 projection math and in-place tensor mutability**

Create `tests/test_vllm_refusal_projection.py`:
```python
import torch
import pytest

def test_rank1_projection_mathematics():
    from recipes.mods.inkling_refusal_dial.refusal_projection import InklingRefusalProjection
    proj = InklingRefusalProjection(hidden_size=4096, num_layers=42)
    # Unit direction along axis 0
    r = torch.zeros(4096)
    r[0] = 1.0
    proj.directions[0] = r
    proj.set_lambda(1.0)
    
    # Input vector with components along axis 0 and axis 1
    x = torch.tensor([[5.0, 3.0] + [0.0]*4094])
    y = proj.project(x, layer_id=0)
    
    # Component along axis 0 must be zeroed at lambda=1.0
    assert torch.isclose(y[0, 0], torch.tensor(0.0), atol=1e-5)
    # Orthogonal component along axis 1 must remain untouched
    assert torch.isclose(y[0, 1], torch.tensor(3.0), atol=1e-5)

def test_lambda_in_place_device_tensor_preserves_data_ptr():
    from recipes.mods.inkling_refusal_dial.refusal_projection import InklingRefusalProjection
    proj = InklingRefusalProjection(hidden_size=4096, num_layers=42)
    ptr_before = proj.lambda_tensor.data_ptr()
    proj.set_lambda(0.5)
    ptr_after = proj.lambda_tensor.data_ptr()
    assert ptr_before == ptr_after
    assert torch.isclose(proj.lambda_tensor, torch.tensor([0.5]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vllm_refusal_projection.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `InklingRefusalProjection` and admin API router**

Implement `recipes/mods/inkling-refusal-dial/refusal_projection.py`:
- Initializes `self.lambda_tensor = torch.zeros(1, dtype=torch.float32)` (moved to GPU when available).
- `set_lambda(val)` uses `self.lambda_tensor.fill_(float(val))`.
- Loads safetensors from `os.getenv("VLLM_REFUSAL_DIRS")`.
- `project(hs, layer_id)` performs:
  ```python
  if self.lambda_tensor.item() == 0.0 or layer_id not in self.directions:
      return hs
  r = self.directions[layer_id]
  dot = torch.matmul(hs, r)
  return hs - self.lambda_tensor * torch.outer(dot, r)
  ```

Implement `recipes/mods/inkling-refusal-dial/admin_routes.py`:
- Registers `/admin/refusal_lambda` on FastAPI app.
- Returns current lambda on `GET`.
- Parses `{"lambda": float}` on `POST`, updates `lambda_tensor`, and calls vLLM cache reset.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_vllm_refusal_projection.py -v`
Expected: PASS with 2 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_vllm_refusal_projection.py recipes/mods/inkling-refusal-dial/refusal_projection.py recipes/mods/inkling-refusal-dial/admin_routes.py
git commit -m "feat: implement vLLM rank-1 refusal projection hook and admin endpoint"
```

---

### Task 3: Author and Validate Sparkrun Recipe

**Files:**
- Create: `recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml`
- Test: `tests/test_recipe_schema.py`

**Interfaces:**
- Produces: Valid sparkrun recipe for `thinkingmachines/Inkling-Small-NVFP4` with refusal dial.

- [ ] **Step 1: Write recipe schema and field assertion test**

Create `tests/test_recipe_schema.py`:
```python
import yaml
import pytest

def test_inkling_refusal_dial_recipe_structure():
    with open("recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml") as f:
        recipe = yaml.safe_load(f)
    assert recipe["recipe_version"] == "2"
    assert recipe["model"] == "thinkingmachines/Inkling-Small-NVFP4"
    assert recipe["runtime"] == "vllm"
    assert recipe["min_nodes"] == 2
    assert recipe["max_nodes"] == 2
    assert recipe["defaults"]["tensor_parallel"] == 2
    assert "VLLM_REFUSAL_DIRS" in recipe["env"]
    assert "VLLM_REFUSAL_LAMBDA_INIT" in recipe["env"]
    assert any("verify_inkling_rank1.py" in cmd for cmd in recipe["pre_exec"])
    assert any("admin/refusal_lambda" in cmd for cmd in recipe["post_exec"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_recipe_schema.py -v`
Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Create `recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml`**

Write the complete recipe including:
- Header documenting verified hardware (`dgx-pair`, GB10 128 GB unified, RoCEv2 ConnectX-7).
- `container: ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926`.
- `executor_config: {entrypoint: ""}`.
- Complete `env`, `defaults`, `pre_exec`, `post_exec`, `post_commands`, and `command` blocks conforming to the design spec.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_recipe_schema.py -v`
Expected: PASS with 1 passed.

- [ ] **Step 5: Validate recipe with sparkrun validator**

Run: `sparkrun validate recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml`
Expected: Exit code 0, "Recipe is valid".

- [ ] **Step 6: Commit**

```bash
git add tests/test_recipe_schema.py recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml
git commit -m "feat: add verified sparkrun recipe for Inkling-Small refusal dial"
```

---

### Task 4: Shard Parity Audit & Cluster Weight Sync Verification

**Files:**
- Create: `benchmarks/scripts/verify_inkling_shards.sh`
- Test: Execute script against `gb10-spark` and `gx10-spark`

**Interfaces:**
- Produces: Shard audit log verifying all 10 shards (`model-00001-of-00010.safetensors` through `model-00010-of-00010.safetensors`) exist on both nodes and byte counts match `metadata.total_size` (159.0 GiB).

- [ ] **Step 1: Write shard parity audit script**

Create `benchmarks/scripts/verify_inkling_shards.sh`:
```bash
#!/bin/bash
set -euo pipefail
HEAD_DIR="$HOME/.cache/huggingface/hub/models--thinkingmachines--Inkling-Small-NVFP4"
WORKER_HOST="10.10.20.11"

echo "=== Auditing Head Shards ==="
test -d "$HEAD_DIR" || { echo "Head model dir missing"; exit 1; }
HEAD_COUNT=$(find "$HEAD_DIR" -name "*.safetensors" | wc -l)
echo "Head shards found: $HEAD_COUNT"

echo "=== Auditing Worker Shards ($WORKER_HOST) ==="
WORKER_COUNT=$(ssh "devops@$WORKER_HOST" "find $HEAD_DIR -name '*.safetensors' 2>/dev/null | wc -l" || echo "0")
echo "Worker shards found: $WORKER_COUNT"

if [ "$HEAD_COUNT" -ne 10 ] || [ "$WORKER_COUNT" -ne 10 ]; then
  echo "Shard parity check FAILED: expected 10 shards on both nodes."
  exit 1
fi
echo "Shard parity check PASSED."
```
Make executable: `chmod +x benchmarks/scripts/verify_inkling_shards.sh`

- [ ] **Step 2: Run verification script**

Run: `./benchmarks/scripts/verify_inkling_shards.sh`
Expected: Report current shard status and determine if rsync sync is required.

- [ ] **Step 3: Commit**

```bash
git add benchmarks/scripts/verify_inkling_shards.sh
git commit -m "chore: add multi-node shard parity audit script for Inkling-Small"
```

---

### Task 5: End-to-End Extraction, Launch & Dual-Split Evaluation

**Files:**
- Output: `refusal_dirs_inkling.safetensors`
- Output: `benchmarks/redteam/results/inkling-small-refusal-dial.jsonl`
- Output: `benchmarks/redteam/results/RESULTS-inkling-small-refusal-dial.md`

- [ ] **Step 1: Execute contrastive extraction**

Run:
```bash
python3 benchmarks/redteam/extract_contrastive_directions.py \
  --model thinkingmachines/Inkling-Small-NVFP4 \
  --output /opt/refusal/refusal_dirs_inkling.safetensors \
  --n-prompts 32
```
Expected: Produces `/opt/refusal/refusal_dirs_inkling.safetensors` (~350 KB).

- [ ] **Step 2: Run pre-exec verification on the generated tensor**

Run:
```bash
python3 recipes/mods/inkling-refusal-dial/verify_inkling_rank1.py \
  --dirs /opt/refusal/refusal_dirs_inkling.safetensors
```
Expected: "All 42 layers verified successfully. Directions norm=1.000. Ready for inference." (Exit code 0).

- [ ] **Step 3: Launch the recipe via sparkrun**

Run:
```bash
sparkrun run recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml
```
Expected: Engine starts, pre-exec passes, models report ready, post-exec initializes $\lambda=1.0$.

- [ ] **Step 4: Verify live dial modulation via HTTP**

Run:
```bash
# Verify lambda query:
curl -s http://127.0.0.1:8000/admin/refusal_lambda
# Verify switch to stock (lambda 0):
curl -s -XPOST http://127.0.0.1:8000/admin/refusal_lambda -H 'Content-Type: application/json' -d '{"lambda": 0.0}'
# Verify switch back to ablated (lambda 1):
curl -s -XPOST http://127.0.0.1:8000/admin/refusal_lambda -H 'Content-Type: application/json' -d '{"lambda": 1.0}'
```
Expected: Returns `{"status": "ok", "lambda": 0.0}` and `{"status": "ok", "lambda": 1.0}` respectively.

- [ ] **Step 5: Run dual-split refusal evaluation**

Run:
```bash
python3 benchmarks/redteam/run_refusal_eval.py \
  --base http://127.0.0.1:8000/v1 \
  --model inkling-small \
  --split both \
  --out benchmarks/redteam/results/inkling-small-refusal-dial.jsonl
```
Expected: $\ge 95/100$ harmful compliance AND $\ge 95/100$ benign compliance at $\lambda=1.0$.

- [ ] **Step 6: Record results scorecard and commit**

Create `benchmarks/redteam/results/RESULTS-inkling-small-refusal-dial.md` with the benchmark scores and commit:
```bash
git add benchmarks/redteam/results/RESULTS-inkling-small-refusal-dial.md
git commit -m "docs: record Inkling-Small refusal dial dual-split evaluation results"
```
