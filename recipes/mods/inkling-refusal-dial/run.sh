#!/usr/bin/env bash
# run.sh — executed inside every rank's container before serve.
# Sets up /opt/refusal with directions and verification tools, and wires
# refusal projection into vLLM.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /opt/refusal

# Install directions and verification script
cp "$HERE/refusal_dirs_inkling.safetensors" /opt/refusal/refusal_dirs_inkling.safetensors
cp "$HERE/verify_inkling_rank1.py" /opt/refusal/verify_inkling_rank1.py
chmod +x /opt/refusal/verify_inkling_rank1.py

# Link modules to python site-packages so vLLM can import them
VLLM_PKG_DIR="/usr/local/lib/python3.12/dist-packages/vllm"
if [[ -d "$VLLM_PKG_DIR" ]]; then
    cp "$HERE/refusal_projection.py" "$VLLM_PKG_DIR/refusal_projection.py"
    cp "$HERE/admin_routes.py" "$VLLM_PKG_DIR/admin_routes.py"
fi

echo "[INFO] Inkling refusal dial overlay mod installed successfully."
