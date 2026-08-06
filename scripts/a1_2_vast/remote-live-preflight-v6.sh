#!/usr/bin/env bash
set -euo pipefail

remote_root="${1:?remote root is required}"
expected_manifest_digest="${2:?expected manifest digest is required}"
expected_digest="sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
[[ "${expected_manifest_digest}" == "${expected_digest}" ]] || { echo 'unexpected direct-base digest' >&2; exit 64; }

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PIP_NO_INDEX=1
export MYIS_REMOTE_MODE=a1_2_preflight_only
export PYTHONPATH="${remote_root}/current/src"
output_root="${remote_root}/output"
mkdir -p "${output_root}/preflight/adapters" "${output_root}/logs"

pids=()
for slot in 0 1 2 3; do
  arm="ARM-0$((slot + 2))"
  CUDA_VISIBLE_DEVICES="${slot}" "${remote_root}/venv/bin/python" -m \
    myis_research.armindex.a1_2_live_preflight adapter-check \
    --arm "${arm}" --model-root "${remote_root}/models" \
    --output "${output_root}/preflight/adapters/${arm}.json" \
    >"${output_root}/logs/${arm}.adapter.stdout" \
    2>"${output_root}/logs/${arm}.adapter.stderr" &
  pids+=("$!")
done
for pid in "${pids[@]}"; do
  wait "${pid}"
done

set +e
CUDA_VISIBLE_DEVICES=0 "${remote_root}/venv/bin/python" -m \
  myis_research.armindex.a1_2_vast remote-worker \
  --job "${remote_root}/jobs/ARM-02.json" --output-root "${output_root}" --fail-after-step 1 \
  >"${output_root}/logs/ARM-02.injected-failure.stdout" \
  2>"${output_root}/logs/ARM-02.injected-failure.stderr"
injected_status=$?
set -e
[[ "${injected_status}" -ne 0 ]] || { echo 'injected resume probe unexpectedly succeeded' >&2; exit 65; }

pids=()
for slot in 0 1 2 3; do
  arm="ARM-0$((slot + 2))"
  CUDA_VISIBLE_DEVICES="${slot}" "${remote_root}/venv/bin/python" -m \
    myis_research.armindex.a1_2_vast remote-worker \
    --job "${remote_root}/jobs/${arm}.json" --output-root "${output_root}" \
    >"${output_root}/logs/${arm}.worker.stdout" \
    2>"${output_root}/logs/${arm}.worker.stderr" &
  pids+=("$!")
done
for pid in "${pids[@]}"; do
  wait "${pid}"
done

"${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_live_preflight summarize \
  --output-root "${output_root}" --output "${output_root}/preflight/preflight-summary.json"

