#!/usr/bin/env bash
# run.sh — executed inside every rank's container before serve.
# Replaces the decode-time top-k kernel in ghcr.io/tonyd2wild/vllm-glm53-flash images, which
# hard-kills the engine on any decode past ~24K context on GB10 (SM121).
# Source: github.com/tonyd2wild/GLM-5.3-Flash-NVFP4-DFlash2-2x-DGX-Spark at commit d061f26,
#   docker/sparse_attn_indexer_kpool_sm121.py (README step 3; docs/SM121-CRASH-FORENSICS-2026-08-27.md).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/sparse_attn_indexer_kpool.py"
if [[ ! -f "$DST" ]]; then
    echo "[ERROR] $DST not found. Has the image changed?" >&2
    exit 1
fi
cp "$HERE/sparse_attn_indexer_kpool.py" "$DST"
python3 -m py_compile "$DST"
echo "[INFO] SM121 top-k fix installed at $DST"
