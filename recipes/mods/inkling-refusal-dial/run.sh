#!/usr/bin/env bash
# run.sh — executed inside every rank's container before serve.
# Installs refusal directions, verification tools, rank-1 projection hook,
# and mounts the /admin/refusal_lambda API router.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /opt/refusal
mkdir -p /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/serve/refusal

# Install directions and verification script
cp "$HERE/refusal_dirs_inkling.safetensors" /opt/refusal/refusal_dirs_inkling.safetensors
cp "$HERE/verify_inkling_rank1.py" /opt/refusal/verify_inkling_rank1.py
# The mod runs as root but vLLM serves as the container user; cp keeps the
# source mode (0600 in some checkouts), so make the directions world-readable.
chmod 0644 /opt/refusal/refusal_dirs_inkling.safetensors
chmod 0755 /opt/refusal/verify_inkling_rank1.py

# Install refusal projection core and API router into vLLM package
cp "$HERE/refusal_projection.py" /usr/local/lib/python3.12/dist-packages/vllm/refusal_projection.py
cp "$HERE/api_router.py" /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/serve/refusal/api_router.py
touch /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/serve/refusal/__init__.py

# Apply surgical patches to Inkling model and entrypoints
python3 "$HERE/patch_vllm.py"

# Pre-compile modified python files
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/vllm/refusal_projection.py
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/serve/refusal/api_router.py
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/vllm/models/inkling/nvidia/model.py
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/serve/__init__.py

# Verify refusal directions and rank-1 projection math
python3 /opt/refusal/verify_inkling_rank1.py

echo "[INFO] Inkling refusal dial overlay mod fully installed and verified."
