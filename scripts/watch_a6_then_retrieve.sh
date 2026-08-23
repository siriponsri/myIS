#!/usr/bin/env bash
set -euo pipefail

ROOT=/opt/myis/a6-goal001-20260823T052423Z-full09
APP="$ROOT/app"
OWNER="$ROOT/owner"
ATTEMPT="$OWNER/armindex/a6/a6-goal001-20260823T052423Z-full09"
QUERY="$ATTEMPT/query-input/opaque-queries-20260823.jsonl"
OUT="$ATTEMPT/deep-rankings"
MODEL="$OWNER/armindex/a4/a4-goal001-20260819T160000Z-a4x10/bundle/runtime-package/assets/models/ARM-03"
SHARD0="$ATTEMPT/owner-local/shard-0"
SHARD1="$ATTEMPT/owner-local/shard-1"

while pgrep -f 'python -u run_a6_full_dapfam.py' >/dev/null 2>&1; do
  sleep 60
done

test -f "$ATTEMPT/A6_SAFE_RETURN_MANIFEST.json"
mkdir -p "$OUT"
export PYTHONPATH="$APP"
python "$APP/run_a6_remote_retrieval.py" \
  --model "$MODEL" \
  --queries "$QUERY" \
  --shard 0 "$SHARD0" \
  --shard 1 "$SHARD1" \
  --output-dir "$OUT" \
  --depths 200 500 1000 2000 \
  > "$OUT/retrieval.log" 2>&1

python "$APP/merge_a6_deep_rankings.py" \
  --input "$OUT/rankings-gpu0.jsonl" \
  --input "$OUT/rankings-gpu1.jsonl" \
  --output "$OUT/deep-rankings.jsonl" \
  --pool-200 "$OUT/pool-200.jsonl" \
  --depth 2000 \
  > "$OUT/merge.log" 2>&1

sha256sum "$OUT"/*.jsonl > "$OUT/SHA256SUMS"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/RETRIEVAL_COMPLETE_UTC"
