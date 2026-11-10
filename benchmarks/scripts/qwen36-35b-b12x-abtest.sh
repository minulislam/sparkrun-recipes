#!/usr/bin/env bash
# A/B/C speed test for Qwen3.6-35B-A3B on gx10-spark (idle worker), port 8899.
# Run from gb10-spark. Each config: start container -> wait ready -> task-mix bench -> stop.
set -uo pipefail
W=10.99.10.11
PORT=8899
NAME=qwen35-abtest
OUT=${OUT:-$HOME/workspace/sparkrun-recipes/benchmarks/results/qwen36-35b-b12x-abtest-$(date +%Y%m%d)}
BENCH=$HOME/workspace/sparkrun-recipes/benchmarks/scripts/task_mix_bench.py
mkdir -p "$OUT"

AEON=ghcr.io/aeon-7/aeon-vllm-ultimate:maxsafe-20260708
B12X=ghcr.io/spark-arena/dgx-vllm-eugr-nightly-b12x:20260926
# Local snapshot paths (offline): heretic refs/main points at a partial snapshot
# (config.json only) and the nvidia repo has no refs/main, so repo IDs fail offline.
HUB=/root/.cache/huggingface/hub
HERETIC=$HUB/models--AEON-7--Qwen3.6-35B-A3B-heretic-NVFP4/snapshots/a483749169933e3fc5a4f48a5979effeba093192
STOCK=$HUB/models--nvidia--Qwen3.6-35B-A3B-NVFP4/snapshots/491c2f1ea524c639598bf8fa787a93fed5a6fbce
DFLASH='{"method":"dflash","model":"'$HUB'/models--z-lab--Qwen3.6-35B-A3B-DFlash/snapshots/f181eece646affea2c38b2765f1aaa01a9734ccd","num_speculative_tokens":11}'
MTP='{"method":"mtp","num_speculative_tokens":2,"moe_backend":"triton"}'

COMMON="--served-model-name m --host 0.0.0.0 --port $PORT --tensor-parallel-size 1 --trust-remote-code \
 --gpu-memory-utilization 0.75 --max-model-len 262144 --max-num-batched-tokens 32768 --enable-chunked-prefill \
 --reasoning-parser qwen3 --tool-call-parser qwen3_coder --enable-auto-tool-choice"

launch() { # label image extra-env serve-args...
  local label=$1 image=$2 env=$3; shift 3
  echo "=== [$label] launching $(date +%T)"
  ssh $W "docker rm -f $NAME >/dev/null 2>&1; docker run -d --name $NAME --gpus all --network host --ipc host \
    --shm-size=32g --ulimit memlock=-1:-1 --entrypoint vllm $env \
    -e HF_HOME=/root/.cache/huggingface -e HF_HUB_OFFLINE=1 -v \$HOME/.cache/huggingface:/root/.cache/huggingface \
    $image serve $*" >/dev/null || { echo "[$label] docker run failed"; return 1; }
  for i in $(seq 1 120); do
    sleep 10
    if curl -sf -m 5 http://$W:$PORT/v1/models >/dev/null; then echo "[$label] ready after $((i*10))s"; return 0; fi
    if ! ssh $W "docker ps -q -f name=^$NAME\$" | grep -q .; then echo "[$label] container died"; ssh $W "docker logs --tail 60 $NAME" > "$OUT/$label.fail.log" 2>&1; return 1; fi
  done
  echo "[$label] timeout"; return 1
}
finish() { ssh $W "docker logs $NAME > /tmp/$1.log 2>&1; docker rm -f $NAME" >/dev/null; scp -q $W:/tmp/$1.log "$OUT/$1.server.log"; }
bench() { python3 $BENCH --url http://$W:$PORT --model m --runs 3 --concurrency 8 --max-tokens 512 --label "$1" --out "$OUT/$1.json"; }

run_cfg() { local label=$1; shift; if launch "$label" "$@"; then bench "$label"; fi; finish "$label"; }

# A: current production binding (AEON image, DFlash-11, BF16 KV)
run_cfg A_heretic_aeon_dflash "$AEON" "" "$HERETIC $COMMON --max-num-seqs 64 --dtype auto --quantization compressed-tensors --enable-prefix-caching --speculative-config '$DFLASH'"

# B: same Heretic weights + DFlash, on the b12x image with b12x kernels + async scheduling (BF16 KV, DFlash needs it)
run_cfg B_heretic_b12x_dflash "$B12X" "-e CUTE_DSL_ARCH=sm_121a" "$HERETIC $COMMON --max-num-seqs 64 --moe-backend auto --linear-backend flashinfer_b12x --attention-backend flashinfer --async-scheduling --enable-prefix-caching --speculative-config '$DFLASH'"

# C: handbook reproduction — stock NVIDIA NVFP4 (has MTP heads) + MiaAI flags (b12x, MTP-2, FP8 KV)
run_cfg C_stock_b12x_mtp "$B12X" "-e CUTE_DSL_ARCH=sm_121a" "$STOCK $COMMON --max-num-seqs 24 --moe-backend auto --linear-backend flashinfer_b12x --attention-backend flashinfer --async-scheduling --kv-cache-dtype fp8 --speculative-config '$MTP'"

echo "=== ALL DONE $(date +%T) -> $OUT"
