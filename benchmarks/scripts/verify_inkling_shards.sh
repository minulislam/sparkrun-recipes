#!/bin/bash
set -euo pipefail

HEAD_DIR="$HOME/.cache/huggingface/hub/models--thinkingmachines--Inkling-Small-NVFP4"
# CX7 data interface 10.99.10.11 is primary/fastest; fallback to mgmt 10.10.20.11 if needed
WORKER_HOST="10.99.10.11"
EXPECTED_SHARDS=10

echo "=== Auditing Head Shards ==="
if [ ! -d "$HEAD_DIR" ]; then
  echo "ERROR: Head model directory $HEAD_DIR missing"
  exit 1
fi

HEAD_COUNT=$(find "$HEAD_DIR" -name "*.safetensors" -exec test -e {} \; -print | wc -l)
echo "Head valid shards found: $HEAD_COUNT / $EXPECTED_SHARDS"

echo "=== Auditing Worker Shards ($WORKER_HOST) ==="
WORKER_COUNT=$(ssh "devops@$WORKER_HOST" "find $HEAD_DIR -name '*.safetensors' -exec test -e {} \; -print 2>/dev/null | wc -l" || echo "0")
echo "Worker valid shards found: $WORKER_COUNT / $EXPECTED_SHARDS"

if [ "$HEAD_COUNT" -ne "$EXPECTED_SHARDS" ]; then
  echo "FAILURE: Head node is missing shards (found $HEAD_COUNT, expected $EXPECTED_SHARDS)"
  exit 1
fi

if [ "$WORKER_COUNT" -ne "$EXPECTED_SHARDS" ]; then
  echo "STATUS: Worker requires synchronization. Run:"
  echo "rsync -avP $HEAD_DIR/ devops@$WORKER_HOST:$HEAD_DIR/"
  exit 2
fi

echo "SUCCESS: Shard parity confirmed across both nodes ($EXPECTED_SHARDS shards each)."
exit 0
