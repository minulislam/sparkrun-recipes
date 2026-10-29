#!/usr/bin/env bash
# run.sh — executed inside every rank's container before serve.
# Disables decode-path persistent_topk in ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3,
# which kills the engine on long-history decode on GB10 (SM121): "persistent_topk would
# oversubscribe and the FilteredTopK fallback requires >=128KB smem". Same edit as upstream
# MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks overlay/patch_glm_video_placeholders.py
# (_disable_gb10_persistent_topk), which the prebuilt image does not carry.
set -euo pipefail
DST="$(python3 -c 'import vllm,os;print(os.path.dirname(vllm.__file__))')/model_executor/layers/sparse_attn_indexer_kpool.py"
OLD="if current_platform.is_cuda() and select_k in (512, 1024, 2048):"
NEW="if False and current_platform.is_cuda() and select_k in (512, 1024, 2048):  # GB10 persistent_topk smem"
if grep -qF "$NEW" "$DST"; then
    echo "[INFO] persistent_topk already disabled"
elif grep -qF "$OLD" "$DST"; then
    python3 - "$DST" "$OLD" "$NEW" <<'PY'
import sys; p, old, new = sys.argv[1:]
t = open(p).read(); open(p, "w").write(t.replace(old, new, 1))
PY
    rm -f "$(dirname "$DST")"/__pycache__/sparse_attn_indexer_kpool*.pyc
    python3 -m py_compile "$DST"
    echo "[INFO] disabled GB10 persistent_topk (top_k_per_row_decode)"
else
    echo "[ERROR] persistent_topk pattern not found in $DST" >&2
    exit 1
fi
