#!/usr/bin/env bash
set -euo pipefail

image_reference="${1:?image reference is required}"
remote_root="${2:?remote root is required}"
expected_commit="${3:?expected Git commit is required}"
expected_tree="${4:?expected Git tree is required}"
expected_manifest_digest="${5:?expected manifest digest is required}"
expected_bundle_sha256="${6:?expected bundle SHA-256 is required}"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PIP_NO_INDEX=1
export PYTHONDONTWRITEBYTECODE=1
export MYIS_REMOTE_MODE=a1_2_preflight_only

supplement="${remote_root}/supplement-wheelhouse-v7"
[[ -f "${supplement}/SHA256SUMS" ]] || { echo 'v7 supplement SHA256SUMS missing' >&2; exit 80; }
(cd "${supplement}" && sha256sum --check SHA256SUMS)
python "${remote_root}/current/scripts/a1_2_vast/validate_preflight_supplement_v7.py" "${supplement}"

if find "${remote_root}/current" -type d -name __pycache__ -print -quit | grep -q .; then
  echo 'fresh v7 frozen bundle already contains Python bytecode cache' >&2
  exit 81
fi

python -m venv --system-site-packages "${remote_root}/venv"
"${remote_root}/venv/bin/python" -m pip install \
  --disable-pip-version-check --no-index --find-links "${supplement}" \
  -r "${supplement}/requirements.preflight-supplement.v7.txt"

bash "${remote_root}/current/scripts/a1_2_vast/remote-bootstrap-direct-base-v6.sh" \
  "${image_reference}" "${remote_root}" "${expected_commit}" "${expected_tree}" \
  "${expected_manifest_digest}" "${expected_bundle_sha256}"

PYTHONPATH="${remote_root}/current/src" "${remote_root}/venv/bin/python" - <<'PY'
from importlib.metadata import version

assert version("jsonschema") == "4.25.1"
assert version("pydantic") == "2.13.4"
assert version("structlog") == "26.1.0"
print({"status": "v7_supplement_runtime_pass"})
PY

if find "${remote_root}/current" -type d -name __pycache__ -print -quit | grep -q .; then
  echo 'v7 verification wrote Python bytecode into the frozen bundle' >&2
  exit 82
fi
