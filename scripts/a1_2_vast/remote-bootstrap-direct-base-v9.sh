#!/usr/bin/env bash
set -euo pipefail

image_reference="${1:?image reference is required}"
remote_root="${2:?remote root is required}"
expected_commit="${3:?expected Git commit is required}"
expected_tree="${4:?expected Git tree is required}"
expected_manifest_digest="${5:?expected manifest digest is required}"
expected_bundle_sha256="${6:?expected bundle SHA-256 is required}"

expected_image="pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
expected_digest="sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
[[ "${image_reference}" == "${expected_image}" ]] || { echo 'unexpected image reference' >&2; exit 64; }
[[ "${expected_manifest_digest}" == "${expected_digest}" ]] || { echo 'unexpected image manifest digest' >&2; exit 65; }
[[ "${expected_bundle_sha256}" =~ ^[a-f0-9]{64}$ ]] || { echo 'invalid expected bundle SHA-256' >&2; exit 66; }
[[ "$(uname -m)" == "x86_64" ]] || { echo 'base image platform is not linux/amd64' >&2; exit 67; }

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PIP_NO_INDEX=1
export PYTHONDONTWRITEBYTECODE=1
export MYIS_REMOTE_MODE=a1_2_preflight_only

bundle_archive="${remote_root}/incoming/frozen-code-bundle.tar.gz"
bundle_root="${remote_root}/current"
wheelhouse="${remote_root}/wheelhouse"
supplement="${remote_root}/supplement-wheelhouse-v7"
model_root="${remote_root}/models"
jobs="${remote_root}/jobs"
output_root="${remote_root}/output"
marker="${output_root}/preflight/verification-pass.v9.json"

# This intentionally uses only base-image shell utilities before any bundled Python.
[[ -f "${bundle_archive}" ]] || { echo 'frozen bundle archive missing' >&2; exit 68; }
[[ "$(sha256sum -- "${bundle_archive}" | awk '{print $1}')" == "${expected_bundle_sha256}" ]] || {
  echo 'frozen bundle archive SHA-256 mismatch' >&2
  exit 69
}
python - "${bundle_archive}" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

with tarfile.open(sys.argv[1], "r:gz") as archive:
    names = set()
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if (
            not member.isreg()
            or path.is_absolute()
            or ".." in path.parts
            or not member.name
            or member.name in names
        ):
            raise SystemExit("unsafe frozen-bundle member")
        names.add(member.name)
PY

[[ -f "${bundle_root}/BUNDLE_MANIFEST.json" ]] || { echo 'extracted v9 bundle manifest missing' >&2; exit 70; }
for path in "${wheelhouse}/SHA256SUMS" "${supplement}/SHA256SUMS"; do
  [[ -f "${path}" ]] || { echo "required staged checksum missing: ${path}" >&2; exit 71; }
done
(cd "${wheelhouse}" && sha256sum --check SHA256SUMS)
(cd "${supplement}" && sha256sum --check SHA256SUMS)

python - "${remote_root}" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
forbidden = re.compile(r"qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|protected[_-]?evaluator", re.I)
for surface in (root / "current", root / "wheelhouse", root / "supplement-wheelhouse-v7", root / "models", root / "jobs"):
    if not surface.is_dir():
        raise SystemExit(f"required remote surface missing: {surface.name}")
    for path in surface.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or forbidden.search(relative):
            raise SystemExit(f"unsafe remote surface: {relative}")
PY

for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  [[ -f "${model_root}/${arm}/SHA256SUMS" ]] || { echo "${arm} SHA256SUMS missing" >&2; exit 72; }
  [[ -f "${model_root}/${arm}/runtime-file-manifest.v4.json" ]] || { echo "${arm} runtime manifest missing" >&2; exit 73; }
  [[ -f "${jobs}/${arm}.json" ]] || { echo "${arm} job manifest missing" >&2; exit 74; }
  (cd "${model_root}/${arm}" && sha256sum --check SHA256SUMS)
done

python -m venv --system-site-packages "${remote_root}/venv"
"${remote_root}/venv/bin/python" -m pip install --disable-pip-version-check --no-index --find-links "${wheelhouse}" -r "${bundle_root}/containers/a1_2_vast_4x3090/runtime/requirements.v2.txt"
"${remote_root}/venv/bin/python" -m pip install --disable-pip-version-check --no-index --find-links "${supplement}" -r "${supplement}/requirements.preflight-supplement.v7.txt"

for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_runtime_minimal validate-manifest --repository-root "${bundle_root}" --arm "${arm}" --model-directory "${model_root}/${arm}"
done
PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_live_preflight_packaging_v8 --repository-root "${bundle_root}" validate-remote-lineage --expected-commit "${expected_commit}" --expected-tree "${expected_tree}"

"${remote_root}/venv/bin/python" - <<'PY'
from importlib.metadata import version
import os
import torch

assert os.environ["HF_HUB_OFFLINE"] == "1"
assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
assert torch.__version__ == "2.6.0+cu118"
assert torch.version.cuda == "11.8"
assert torch.cuda.is_available()
for package, locked in {"accelerate": "1.6.0", "jsonschema": "4.25.1", "pydantic": "2.13.4", "pyyaml": "6.0.2", "safetensors": "0.5.3", "sentence-transformers": "4.1.0", "structlog": "26.1.0", "transformers": "4.51.3"}.items():
    assert version(package) == locked, (package, version(package), locked)
PY

mkdir -p "${output_root}/preflight"
PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_live_preflight runtime-identity --remote-root "${remote_root}" --output "${output_root}/preflight/runtime-identity.json" --expected-manifest-digest "${expected_manifest_digest}" --image-observation-mode runtime_anchors_no_container_api --bundle-sha256 "${expected_bundle_sha256}"

# The marker is created only after every offline runtime check above succeeds.
PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_live_preflight_runtime_v9 validate-verification-marker --write-marker "${marker}" --runtime-identity "${output_root}/preflight/runtime-identity.json" --expected-commit "${expected_commit}" --expected-tree "${expected_tree}" --expected-manifest-digest "${expected_manifest_digest}" --expected-bundle-sha256 "${expected_bundle_sha256}"
PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_live_preflight_runtime_v9 validate-verification-marker --marker "${marker}" --expected-commit "${expected_commit}" --expected-tree "${expected_tree}" --expected-manifest-digest "${expected_manifest_digest}" --expected-bundle-sha256 "${expected_bundle_sha256}"

if find "${bundle_root}" -type d -name __pycache__ -print -quit | grep -q .; then
  echo 'v9 verification wrote Python bytecode into the frozen bundle' >&2
  exit 75
fi
