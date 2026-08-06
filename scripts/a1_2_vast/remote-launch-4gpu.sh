#!/usr/bin/env bash
set -euo pipefail

bundle_root="${1:-/opt/myis/bundle}"
output_root="${2:-/opt/myis/output/a1.2-v2}"
image_reference="${3:?immutable image reference is required}"
expected_digest="${4:?expected image digest is required}"
if [[ ! "${image_reference}" =~ ^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$ ]]; then
  echo "image reference is invalid" >&2
  exit 64
fi
actual_digest="$(docker image inspect --format '{{.Id}}' "${image_reference}")"
if [[ "${actual_digest}" != "${expected_digest}" ]]; then
  echo "loaded image digest mismatch" >&2
  exit 65
fi
lock_root="/var/lock/myis-a1.2-v2"
mkdir -p "${lock_root}"

arms=(ARM-02 ARM-03 ARM-04 ARM-05)
pids=()
for slot in 0 1 2 3; do
  arm="${arms[$slot]}"
  lock="${lock_root}/${arm}.lock"
  flock -n "${lock}" docker run --rm --gpus all --network none --read-only \
    --tmpfs /tmp:rw,nosuid,nodev,size=1g \
    -e CUDA_VISIBLE_DEVICES="${slot}" \
    -e MYIS_REMOTE_MODE=a1_2_preflight_only \
    -e HF_HUB_OFFLINE=1 \
    -e TRANSFORMERS_OFFLINE=1 \
    -e PYTHONPATH=/opt/myis/bundle/src \
    -v "${bundle_root}:/opt/myis/bundle:ro" \
    -v "${output_root}:/opt/myis/output:rw" \
    "${image_reference}" \
    python -m myis_research.armindex.a1_2_vast remote-worker \
      --job "/opt/myis/bundle/control/armindex/a1.2/jobs/v2/${arm}.json" \
      --output-root /opt/myis/output &
  pids+=("$!")
done

status=0
for pid in "${pids[@]}"; do
  if ! wait "${pid}"; then
    status=1
  fi
done
if [[ "${status}" -eq 0 ]]; then
  docker run --rm --network none --read-only \
    --tmpfs /tmp:rw,nosuid,nodev,size=256m \
    -e MYIS_REMOTE_MODE=a1_2_preflight_only \
    -e PYTHONPATH=/opt/myis/bundle/src \
    -v "${bundle_root}:/opt/myis/bundle:ro" \
    -v "${output_root}:/opt/myis/output:rw" \
    "${image_reference}" \
    python -m myis_research.armindex.a1_2_vast safe-export \
      --output-root /opt/myis/output \
      --allowlist /opt/myis/bundle/control/armindex/a1.2/safe-export-allowlist.v2.json \
      --archive /opt/myis/output/safe-export.tar.gz
fi
exit "${status}"
