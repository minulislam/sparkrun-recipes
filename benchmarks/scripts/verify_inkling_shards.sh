#!/bin/bash
set -euo pipefail

HEAD_DIR="$HOME/.cache/huggingface/hub/models--thinkingmachines--Inkling-Small-NVFP4"
EXPECTED_SHARDS=10
MIN_TOTAL_GIB=150

echo "=== Auditing Head Shards ==="
if [ ! -d "$HEAD_DIR" ]; then
  echo "ERROR: Head model directory $HEAD_DIR missing"
  exit 1
fi

HEAD_SHARDS=$(find "$HEAD_DIR" -name "*.safetensors" -exec test -e {} \; -print)
HEAD_COUNT=$(echo "$HEAD_SHARDS" | sed '/^$/d' | wc -l)
HEAD_BYTES=$(echo "$HEAD_SHARDS" | xargs -r stat -L -c "%s" 2>/dev/null | awk '{s+=$1} END {print s+0}')
HEAD_GIB=$(awk -v b="$HEAD_BYTES" 'BEGIN {printf "%.1f", b/(1024*1024*1024)}')

echo "Head valid shards found: $HEAD_COUNT / $EXPECTED_SHARDS ($HEAD_GIB GiB)"

# Determine worker reachable host (prefer CX7 data plane 10.99.10.11; fallback to mgmt 10.10.20.11)
WORKER_HOST="10.99.10.11"
if ! ssh -o ConnectTimeout=2 -o BatchMode=yes "devops@$WORKER_HOST" true 2>/dev/null; then
  echo "Notice: CX7 interface $WORKER_HOST unreachable, falling back to mgmt 10.10.20.11"
  WORKER_HOST="10.10.20.11"
fi

echo "=== Auditing Worker Shards ($WORKER_HOST) ==="
WORKER_SHARDS=$(ssh -o ConnectTimeout=5 "devops@$WORKER_HOST" "find '$HEAD_DIR' -name '*.safetensors' -exec test -e {} \\; -print 2>/dev/null" || true)
WORKER_COUNT=$(echo "$WORKER_SHARDS" | sed '/^$/d' | wc -l)
WORKER_BYTES=$(ssh -o ConnectTimeout=5 "devops@$WORKER_HOST" "echo '$WORKER_SHARDS' | xargs -r stat -L -c '%s' 2>/dev/null | awk '{s+=\$1} END {print s+0}'" || echo "0")
WORKER_GIB=$(awk -v b="$WORKER_BYTES" 'BEGIN {printf "%.1f", b/(1024*1024*1024)}')

echo "Worker valid shards found: $WORKER_COUNT / $EXPECTED_SHARDS ($WORKER_GIB GiB)"

if [ "$HEAD_COUNT" -ne "$EXPECTED_SHARDS" ] || (( $(echo "$HEAD_GIB < $MIN_TOTAL_GIB" | bc -l) )); then
  echo "FAILURE: Head node is missing shards or incomplete (found $HEAD_COUNT shards, $HEAD_GIB GiB; expected $EXPECTED_SHARDS shards, >= $MIN_TOTAL_GIB GiB)"
  exit 1
fi

if [ "$WORKER_COUNT" -ne "$EXPECTED_SHARDS" ] || (( $(echo "$WORKER_GIB < $MIN_TOTAL_GIB" | bc -l) )); then
  echo "STATUS: Worker requires synchronization ($WORKER_COUNT/$EXPECTED_SHARDS shards, $WORKER_GIB GiB). Run:"
  echo "rsync -avP $HEAD_DIR/ devops@$WORKER_HOST:$HEAD_DIR/"
  exit 2
fi

echo "SUCCESS: Shard parity confirmed across both nodes ($EXPECTED_SHARDS shards each, >= $MIN_TOTAL_GIB GiB)."
exit 0
