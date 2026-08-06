#!/usr/bin/env bash
set -euo pipefail

image_reference="${1:?immutable image reference is required}"
bundle_root="${2:?bundle root is required}"
output_root="${3:?output root is required}"
model_root="${4:?model root is required}"
expected_commit="${5:?expected Git commit is required}"
expected_tree="${6:?expected Git tree is required}"
expected_digest="${7:?expected image digest is required}"

if [[ ! "${image_reference}" =~ ^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$ ]]; then
  echo "image reference is invalid" >&2
  exit 64
fi
actual_digest="$(docker image inspect --format '{{.Id}}' "${image_reference}")"
if [[ "${actual_digest}" != "${expected_digest}" ]]; then
  echo "loaded image digest mismatch" >&2
  exit 65
fi

exec docker run --rm --gpus all --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  -e MYIS_REMOTE_MODE=a1_2_preflight_only \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e PYTHONPATH=/opt/myis/bundle/src \
  -v "${bundle_root}:/opt/myis/bundle:ro" \
  -v "${model_root}:/opt/myis/models:ro" \
  -v "${output_root}:/opt/myis/output:rw" \
  "${image_reference}" \
  python -m myis_research.armindex.a1_2_vast remote-preflight \
    --bundle-root /opt/myis/bundle \
    --output-root /opt/myis/output \
    --model-root /opt/myis/models \
    --expected-git-commit "${expected_commit}" \
    --expected-git-tree "${expected_tree}" \
    --expected-image-digest "${expected_digest}"
