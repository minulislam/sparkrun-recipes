#!/usr/bin/env bash
# run.sh — executed inside every rank's container before serve.
# Installs the vLLM overlays that give GLM-5.3-Flash an NVFP4 (nvfp4_ds_mla) KV cache on GB10:
# zero-RoPE shim, SM120 width/gate fixes, PDL gate, indexer top-k init, and the B12X_MLA_SPARSE
# backend port. Upstream bind-mounts these files; sparkrun mods copy them instead.
# Source: github.com/drowzeys/keys-vLLm.0.27.1-GLM-5.3-Flash-NVFP4-NVFP4KV-1M-Context-Abliterated
#   at commit b4e7547 (Apache-2.0), overlays/official and overlays/nvfp4-b12x, mapping taken from
#   launcher/launch.sh (ENGINE=official). For image ghcr.io/drowzeys/keys-vllm-glm53-flash-nvfp4-ablit:b12x-cu130.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V=/usr/local/lib/python3.12/dist-packages/vllm
put() { # put <src relative to this mod> <dst relative to vllm>
    [[ -f "$V/$2" ]] || { echo "[ERROR] $V/$2 not found. Has the image changed?" >&2; exit 1; }
    cp "$HERE/$1" "$V/$2"; python3 -m py_compile "$V/$2"
}
put official/attention.py                    models/glm5next/nvidia/attention.py
put official/flashinfer_mla_sparse_sm120.py  v1/attention/backends/mla/flashinfer_mla_sparse_sm120.py
put official/flashinfer_mla_sparse.py        v1/attention/backends/mla/flashinfer_mla_sparse.py
put official/cuda.py                         platforms/cuda.py
put official/sparse_attn_indexer_kpool.py    model_executor/layers/sparse_attn_indexer_kpool.py
put official/kpool_compress.py               models/glm5next/nvidia/ops/kpool_compress.py
put nvfp4-b12x/config/cache.py               config/cache.py
put nvfp4-b12x/config/vllm.py                config/vllm.py
put nvfp4-b12x/envs.py                       envs.py
put nvfp4-b12x/model_executor/layers/attention/mla_attention.py  model_executor/layers/attention/mla_attention.py
put nvfp4-b12x/utils/torch_utils.py          utils/torch_utils.py
put nvfp4-b12x/v1/attention/backends/registry.py                 v1/attention/backends/registry.py
put nvfp4-b12x/v1/kv_cache_interface.py      v1/kv_cache_interface.py
# These two are new files in the overlay (no stock file to replace).
cp "$HERE/nvfp4-b12x/model_executor/layers/mla_cache_format.py" "$V/model_executor/layers/mla_cache_format.py"
cp "$HERE/nvfp4-b12x/v1/attention/backends/mla/b12x_mla_sparse.py" "$V/v1/attention/backends/mla/b12x_mla_sparse.py"
python3 -m py_compile "$V/model_executor/layers/mla_cache_format.py" "$V/v1/attention/backends/mla/b12x_mla_sparse.py"
echo "[INFO] GLM-5.3 NVFP4-KV overlays installed (15 files)"
