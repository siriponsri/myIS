#!/usr/bin/env bash
set -euo pipefail

remote_root="${1:?remote root is required}"
expected_manifest_digest="${2:?expected manifest digest is required}"
attempt_id="${3:?attempt id is required}"
expected_digest="sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
[[ "${expected_manifest_digest}" == "${expected_digest}" ]] || { echo 'unexpected direct-base digest' >&2; exit 64; }
[[ "${attempt_id}" =~ ^[a-z0-9][a-z0-9._-]{2,79}$ ]] || { echo 'invalid attempt id' >&2; exit 65; }

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PIP_NO_INDEX=1
export PYTHONDONTWRITEBYTECODE=1
export MYIS_REMOTE_MODE=a1_2_preflight_only
export PYTHONPATH="${remote_root}/current/src"

output_root="${remote_root}/output"
attempt_dir="${output_root}/attempts/${attempt_id}"
marker="${output_root}/preflight/verification-pass.v9.json"
python_bin="${remote_root}/venv/bin/python"
runtime_module="myis_research.armindex.a1_2_live_preflight_runtime_v9"
children=()
roles=()
heartbeat_pids=()

runtime() {
  "${python_bin}" -m "${runtime_module}" "$@"
}

attempt_runtime() {
  runtime "$@" --output-root "${output_root}" --attempt-id "${attempt_id}" --marker "${marker}"
}

stop_heartbeat() {
  local heartbeat_pid="$1"
  kill "${heartbeat_pid}" 2>/dev/null || true
  wait "${heartbeat_pid}" 2>/dev/null || true
}

cleanup() {
  local index pid heartbeat_pid rc
  set +e
  for heartbeat_pid in "${heartbeat_pids[@]}"; do stop_heartbeat "${heartbeat_pid}"; done
  for pid in "${children[@]}"; do kill -TERM "${pid}" 2>/dev/null || true; done
  for index in "${!children[@]}"; do
    pid="${children[$index]}"
    if wait "${pid}"; then rc=0; else rc=$?; fi
    attempt_runtime record-process-exit --pid "${pid}" --exit-code "${rc}" >/dev/null 2>&1 || true
  done
  attempt_runtime teardown --children-reaped >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

spawn_child() {
  local role="$1"
  local slot="$2"
  local stdout_path="$3"
  local stderr_path="$4"
  shift 4
  CUDA_VISIBLE_DEVICES="${slot}" "$@" >"${stdout_path}" 2>"${stderr_path}" &
  local pid="$!"
  children+=("${pid}")
  roles+=("${role}")
  attempt_runtime record-pid --pid "${pid}" --role "${role}" >/dev/null
  attempt_runtime heartbeat --pid "${pid}" >/dev/null
  (
    while kill -0 "${pid}" 2>/dev/null; do
      attempt_runtime heartbeat --pid "${pid}" >/dev/null || exit 1
      sleep 15
    done
  ) &
  heartbeat_pids+=("$!")
}

wait_group() {
  local active_pid index pid rc state failed=0 progress remaining="${#children[@]}"
  local active=()
  declare -A completed=()
  while [[ "${remaining}" -gt 0 ]]; do
    progress=0
    for index in "${!children[@]}"; do
      pid="${children[$index]}"
      [[ -n "${completed[$pid]:-}" ]] && continue
      state="$(ps -o stat= -p "${pid}" 2>/dev/null | tr -d '[:space:]')"
      if [[ -n "${state}" && "${state}" != Z* ]]; then
        continue
      fi
      if wait "${pid}"; then rc=0; else rc=$?; fi
      completed["${pid}"]=1
      remaining=$((remaining - 1))
      progress=1
      stop_heartbeat "${heartbeat_pids[$index]}"
      attempt_runtime record-process-exit --pid "${pid}" --exit-code "${rc}" >/dev/null
      if [[ "${rc}" -ne 0 && "${failed}" -eq 0 ]]; then
        failed=1
        for active_pid in "${children[@]}"; do
          [[ -n "${completed[$active_pid]:-}" ]] || kill -TERM "${active_pid}" 2>/dev/null || true
        done
      fi
    done
    [[ "${remaining}" -eq 0 || "${progress}" -eq 1 ]] || sleep 1
  done
  children=()
  roles=()
  heartbeat_pids=()
  return "${failed}"
}

runtime init --output-root "${output_root}" --attempt-id "${attempt_id}" --marker "${marker}" >/dev/null
mkdir -p "${attempt_dir}/logs" "${attempt_dir}/preflight/adapters"

for slot in 0 1 2 3; do
  arm="ARM-0$((slot + 2))"
  spawn_child "adapter-${arm,,}" "${slot}" \
    "${attempt_dir}/logs/${arm}.adapter.stdout" "${attempt_dir}/logs/${arm}.adapter.stderr" \
    "${python_bin}" -m "${runtime_module}" adapter-check \
    --output-root "${output_root}" --attempt-id "${attempt_id}" --marker "${marker}" \
    --arm "${arm}" --model-root "${remote_root}/models"
done
wait_group || exit 66

spawn_child "checkpoint-arm-02-injected" 0 \
  "${attempt_dir}/logs/ARM-02.injected.stdout" "${attempt_dir}/logs/ARM-02.injected.stderr" \
  "${python_bin}" -m "${runtime_module}" checkpoint-worker \
  --output-root "${output_root}" --attempt-id "${attempt_id}" --marker "${marker}" \
  --arm ARM-02 --fail-before-step 1
if wait_group; then
  echo 'injected checkpoint failure unexpectedly passed' >&2
  exit 67
fi

for slot in 0 1 2 3; do
  arm="ARM-0$((slot + 2))"
  spawn_child "worker-${arm,,}" "${slot}" \
    "${attempt_dir}/logs/${arm}.worker.stdout" "${attempt_dir}/logs/${arm}.worker.stderr" \
    "${python_bin}" -m "${runtime_module}" checkpoint-worker \
    --output-root "${output_root}" --attempt-id "${attempt_id}" --marker "${marker}" --arm "${arm}"
done
wait_group || exit 68

attempt_runtime summarize >"${attempt_dir}/logs/summary.stdout" 2>"${attempt_dir}/logs/summary.stderr"
attempt_runtime complete --summary "${attempt_dir}/summary.json" >/dev/null
attempt_runtime status --require-pass
attempt_runtime teardown --children-reaped >/dev/null

trap - EXIT INT TERM
