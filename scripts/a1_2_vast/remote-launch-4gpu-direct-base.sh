#!/usr/bin/env bash
set -euo pipefail
remote_root="${1:?remote root is required}"
expected_manifest_digest="${2:?expected manifest digest is required}"
[[ "${expected_manifest_digest}" == "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20" ]] || { echo 'unexpected direct-base digest' >&2; exit 64; }
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MYIS_REMOTE_MODE=a1_2_preflight_only
export PYTHONPATH="${remote_root}/current/src"
for slot in 0 1 2 3; do
  arm="ARM-0$((slot + 2))"
  CUDA_VISIBLE_DEVICES="${slot}" "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_vast remote-worker --job "${remote_root}/jobs/${arm}.json" --output-root "${remote_root}/output" >"${remote_root}/output/${arm}.stdout" 2>"${remote_root}/output/${arm}.stderr" &
done
wait
