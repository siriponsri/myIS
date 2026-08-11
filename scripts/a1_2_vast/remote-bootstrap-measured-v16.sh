#!/usr/bin/env bash
set -euo pipefail

stage_root="${1:?stage root is required}"
expected_bundle_sha256="${2:?bundle SHA-256 is required}"
expected_requirements_sha256="${3:?requirements SHA-256 is required}"
receipt_path="${4:?receipt path is required}"

[[ "${stage_root}" =~ ^/opt/myis/[A-Za-z0-9._/-]+$ ]] || {
  echo 'invalid stage root' >&2
  exit 64
}
[[ "${receipt_path}" =~ ^/opt/myis/[A-Za-z0-9._/-]+\.json$ ]] || {
  echo 'invalid receipt path' >&2
  exit 65
}
[[ "${expected_bundle_sha256}" =~ ^[a-f0-9]{64}$ ]] || exit 66
[[ "${expected_requirements_sha256}" =~ ^[a-f0-9]{64}$ ]] || exit 67
[[ "$(uname -m)" == "x86_64" ]] || {
  echo 'runtime is not linux/amd64' >&2
  exit 68
}

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PIP_NO_INDEX=1
export PYTHONDONTWRITEBYTECODE=1

bundle="${stage_root}/incoming/a1.2-engineering-execution-bundle-v16-frozen-69a056f7.tar.gz"
wheelhouse="${stage_root}/wheelhouse"
supplement="${stage_root}/supplement-wheelhouse-v7"
models="${stage_root}/models"
requirements="${wheelhouse}/requirements.v2.txt"
venv="${stage_root}/venv"

[[ -f "${bundle}" ]] || { echo 'frozen bundle missing' >&2; exit 69; }
[[ "$(sha256sum -- "${bundle}" | awk '{print $1}')" == "${expected_bundle_sha256}" ]] || {
  echo 'frozen bundle SHA-256 mismatch' >&2
  exit 70
}
[[ -f "${requirements}" ]] || { echo 'requirements missing' >&2; exit 71; }
[[ "$(sha256sum -- "${requirements}" | awk '{print $1}')" == "${expected_requirements_sha256}" ]] || {
  echo 'requirements SHA-256 mismatch' >&2
  exit 72
}

for checksum in "${wheelhouse}/SHA256SUMS" "${supplement}/SHA256SUMS"; do
  [[ -f "${checksum}" ]] || { echo "checksum manifest missing: ${checksum}" >&2; exit 73; }
done
(cd "${wheelhouse}" && sha256sum --check SHA256SUMS)
(cd "${supplement}" && sha256sum --check SHA256SUMS)

for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  [[ -f "${models}/${arm}/SHA256SUMS" ]] || { echo "${arm} SHA256SUMS missing" >&2; exit 74; }
  [[ -f "${models}/${arm}/runtime-file-manifest.v4.json" ]] || {
    echo "${arm} runtime manifest missing" >&2
    exit 75
  }
  (cd "${models}/${arm}" && sha256sum --check SHA256SUMS)
done

python - "${stage_root}" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
forbidden = re.compile(
    r"qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|private[_-]?key|protected[_-]?evaluator",
    re.I,
)
for name in ("incoming", "wheelhouse", "supplement-wheelhouse-v7", "models"):
    surface = root / name
    if not surface.is_dir() or surface.is_symlink():
        raise SystemExit(f"required stage surface missing: {name}")
    for path in surface.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or forbidden.search(relative):
            raise SystemExit(f"unsafe stage surface: {relative}")
PY

if [[ ! -x "${venv}/bin/python" ]]; then
  python -m venv --system-site-packages "${venv}"
fi
"${venv}/bin/python" -m pip install \
  --disable-pip-version-check --no-index --find-links "${wheelhouse}" \
  -r "${requirements}"
"${venv}/bin/python" -m pip install \
  --disable-pip-version-check --no-index --find-links "${supplement}" \
  -r "${supplement}/requirements.preflight-supplement.v7.txt"

mkdir -p "$(dirname "${receipt_path}")"
"${venv}/bin/python" - "${stage_root}" "${expected_bundle_sha256}" \
  "${expected_requirements_sha256}" "${receipt_path}" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

import torch

stage = Path(sys.argv[1]).resolve()
bundle_sha256 = sys.argv[2]
requirements_sha256 = sys.argv[3]
receipt_path = Path(sys.argv[4]).resolve()

locked = {
    "accelerate": "1.6.0",
    "jsonschema": "4.25.1",
    "pydantic": "2.13.4",
    "pyyaml": "6.0.2",
    "safetensors": "0.5.3",
    "sentence-transformers": "4.1.0",
    "structlog": "26.1.0",
    "transformers": "4.51.3",
}
observed = {package: version(package) for package in locked}
if observed != locked:
    raise SystemExit(f"dependency drift: {observed!r}")
if torch.__version__ != "2.6.0+cu118" or torch.version.cuda != "11.8":
    raise SystemExit("PyTorch/CUDA runtime drift")
if not torch.cuda.is_available() or torch.cuda.device_count() != 4:
    raise SystemExit("four CUDA devices are required")
gpu_names = [torch.cuda.get_device_name(index) for index in range(4)]
if gpu_names != ["NVIDIA GeForce RTX 3090"] * 4:
    raise SystemExit(f"GPU identity drift: {gpu_names!r}")
if any(os.environ.get(name) != "1" for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PIP_NO_INDEX")):
    raise SystemExit("offline environment drift")

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

body = {
    "schema_version": "myis.armindex-a1.2-runtime-stage-receipt.v16",
    "status": "PASS_RUNTIME_STAGE",
    "aggregate_safe": True,
    "bundle_sha256": bundle_sha256,
    "requirements_sha256": requirements_sha256,
    "wheelhouse_manifest_sha256": digest(stage / "wheelhouse" / "SHA256SUMS"),
    "supplement_manifest_sha256": digest(stage / "supplement-wheelhouse-v7" / "SHA256SUMS"),
    "model_manifest_sha256": {
        arm: digest(stage / "models" / arm / "SHA256SUMS")
        for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
    },
    "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "gpu_count": 4,
    "gpu_model": "NVIDIA GeForce RTX 3090",
    "offline_runtime": True,
    "dependencies": observed,
}
canonical = json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
body["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
payload = json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
if receipt_path.exists() and receipt_path.read_text(encoding="ascii") != payload:
    raise SystemExit("immutable runtime-stage receipt already exists with different bytes")
receipt_path.write_text(payload, encoding="ascii")
print(payload, end="")
PY
