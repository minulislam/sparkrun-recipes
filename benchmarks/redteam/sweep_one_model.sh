#!/bin/bash
# Run the full eval suite against ONE recipe end to end, then stop it.
# usage: sweep_one_model.sh <recipe> <sparkrun-target-args...>
set -uo pipefail
RECIPE="$1"; shift
RD=/home/devops/workspace/sparkrun-recipes
BR="$RD/benchmarks/redteam"; R="$BR/results"; V="$CLAUDE_JOB_DIR/tmp/evalvenv/bin/python"
E="$CLAUDE_JOB_DIR/tmp/evalsets"; TSV="$R/SWEEP.tsv"
LBL=$(basename "$RECIPE" .yaml)
# serve port is per-recipe (the refusal-dial recipe uses 8101, not 8000)
PORT=$(grep -oP '^\s+port:\s*\K\d+' "$RECIPE" | head -1); PORT=${PORT:-8000}
BASE="http://10.10.20.10:${PORT}/v1"
mkdir -p "$R"; cd "$RD"
say(){ echo "[$(date +%H:%M:%S)] $*"; }

say "=== $LBL ==="
# make sure nothing else holds the GPUs
for j in $(sparkrun cluster status 2>/dev/null | grep -oE '\[[0-9a-f]+_[0-9a-f]+\]' | tr -d '[]'); do
  say "stopping stale job $j"; timeout 180 sparkrun stop "$j" >/dev/null 2>&1
done
# Settle before relaunching: a launch 54 s after a stop died with the container
# auto-removed (sparkrun --no-rm does not survive a crash on this version), so
# the startup logs were lost. Give the unified pool time to release.
sleep 90

say "launching"
if ! timeout 2400 sparkrun run "./$RECIPE" "$@" --no-follow --no-rm >"$R/${LBL}.launch.log" 2>&1; then
  say "LAUNCH FAILED"; tail -5 "$R/${LBL}.launch.log"
  printf "%s\tLAUNCH_FAIL\t-\t-\t-\t-\t-\t-\n" "$LBL" >> "$TSV"; exit 1
fi
JOB=$(grep -oE 'sparkrun_[0-9a-f]+_[0-9a-f]+' "$R/${LBL}.launch.log" | head -1 | sed 's/^sparkrun_//')
say "job=$JOB, port=$PORT, waiting for serve"
MODEL=""; for i in $(seq 1 60); do
  MODEL=$(curl -s -m 5 ${BASE}/models 2>/dev/null \
          | python3 -c "import json,sys;print(json.load(sys.stdin)['data'][0]['id'])" 2>/dev/null) && [ -n "$MODEL" ] && break
  docker ps --format '{{.Names}}' | grep -q "$JOB" || { say "CONTAINER GONE"; break; }
  sleep 30
done
if [ -z "$MODEL" ]; then
  say "NEVER SERVED"; printf "%s\tNEVER_SERVED\t-\t-\t-\t-\t-\t-\n" "$LBL" >> "$TSV"
  timeout 180 sparkrun stop "$JOB" >/dev/null 2>&1; exit 1
fi
say "serving as $MODEL"

# Budget generously for EVERY model. A probe with a trivial prompt is useless:
# Gemma-4-31B answered "say ping" directly in 400 tokens, then truncated 200/200
# real JBB prompts at the same budget. Reasoning is prompt-dependent, so size for
# the worst case. 1400 costs ~3x wall on the refusal eval and is worth it.
RTOK=1400
say "refusal eval"
timeout 2400 $V "$BR/run_refusal_eval.py" --base "$BASE" --model "$MODEL" \
  --data "$E/jbb/data" --split both --no-think --concurrency 12 --max-tokens "$RTOK" \
  --timeout 900 --out "$R/${LBL}.refusal.jsonl" >"$R/${LBL}.refusal.log" 2>&1
say "gsm8k"
timeout 2700 $V "$BR/run_correctness_eval.py" --base "$BASE" --model "$MODEL" \
  --gsm8k "$E/gsm8k/main/test-00000-of-00001.parquet" -n 150 --max-tokens 1536 \
  --concurrency 10 --timeout 1200 --out "$R/${LBL}.gsm8k.jsonl" >"$R/${LBL}.gsm8k.log" 2>&1
say "mmlu"
timeout 1800 $V "$BR/run_correctness_eval.py" --base "$BASE" --model "$MODEL" \
  --mmlu "$E/mmlu/all/test-00000-of-00001.parquet" -n 150 --max-tokens 768 --no-think \
  --concurrency 10 --timeout 900 --out "$R/${LBL}.mmlu.jsonl" >"$R/${LBL}.mmlu.log" 2>&1

if [ -n "${NEEDLE:-}" ]; then
  say "needle (full context): depths $NEEDLE"
  timeout 5400 $V "$BR/needle_context_test.py" --base "$BASE" --model "$MODEL" \
    --depths "$NEEDLE" --positions 0.1,0.5,0.9 --max-tokens 512 --timeout 2400 \
    --out "$R/${LBL}.needle.jsonl" >"$R/${LBL}.needle.log" 2>&1
  say "needle: $(grep -c 'YES' "$R/${LBL}.needle.log" 2>/dev/null) hits"
fi
say "stopping"; timeout 240 sparkrun stop "$JOB" >/dev/null 2>&1

$V - "$LBL" "$R" "$MODEL" <<'PY' >> "$TSV"
import json,sys,os
lbl,R,model=sys.argv[1],sys.argv[2],sys.argv[3]
def load(p):
    try: return [json.loads(l) for l in open(p)]
    except Exception: return []
def rate(rows,split):
    s=[r for r in rows if r.get("split")==split]
    if not s: return "-"
    return f"{100*sum(1 for r in s if r['label']=='compliance')/len(s):.0f}"
def acc(rows):
    if not rows: return "-"
    return f"{100*sum(1 for r in rows if r.get('correct'))/len(rows):.1f}"
ref=load(f"{R}/{lbl}.refusal.jsonl"); g=load(f"{R}/{lbl}.gsm8k.jsonl"); m=load(f"{R}/{lbl}.mmlu.jsonl")
unp=sum(1 for r in m if r.get("got") is None)+sum(1 for r in g if r.get("got") is None)
print("\t".join([lbl,"OK",model,rate(ref,"harmful"),rate(ref,"benign"),acc(g),acc(m),str(unp)]))
PY
say "done: $(tail -1 "$TSV")"
