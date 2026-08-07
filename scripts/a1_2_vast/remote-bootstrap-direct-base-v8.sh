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

[[ -f "${supplement}/SHA256SUMS" ]] || { echo 'v8 supplement SHA256SUMS missing' >&2; exit 80; }
(cd "${supplement}" && sha256sum --check SHA256SUMS)
python "${bundle_root}/scripts/a1_2_vast/validate_preflight_supplement_v7.py" "${supplement}"
if find "${bundle_root}" -type d -name __pycache__ -print -quit | grep -q .; then
  echo 'fresh v8 frozen bundle contains Python bytecode cache' >&2
  exit 81
fi

[[ -f "${bundle_archive}" ]] || { echo 'frozen bundle archive missing' >&2; exit 68; }
[[ "$(sha256sum "${bundle_archive}" | awk '{print $1}')" == "${expected_bundle_sha256}" ]] || {
  echo 'frozen bundle archive SHA-256 mismatch' >&2
  exit 69
}

image_observation_mode="runtime_anchors_no_container_api"
if command -v docker >/dev/null 2>&1 && [[ -S /var/run/docker.sock ]]; then
  image_rows="$(docker image inspect --format '{{.Id}}|{{join .RepoDigests ","}}|{{.Os}}|{{.Architecture}}' "${image_reference}")"
  grep -F "${expected_manifest_digest}" <<<"${image_rows}" >/dev/null || {
    echo 'observable Docker identity does not include the expected manifest digest' >&2
    exit 70
  }
  [[ "${image_rows}" == *'|linux|amd64' ]] || { echo 'observable Docker platform mismatch' >&2; exit 71; }
  image_observation_mode="docker_repo_digest"
fi

for path in \
  "${bundle_root}/BUNDLE_MANIFEST.json" \
  "${bundle_root}/GIT_COMMIT" \
  "${bundle_root}/GIT_TREE" \
  "${bundle_root}/PYTORCH_IMAGE_DIGEST" \
  "${wheelhouse}/SHA256SUMS"; do
  [[ -f "${path}" ]] || { echo "required staged file missing: ${path##*/}" >&2; exit 72; }
done
[[ "$(tr -d '\r\n' < "${bundle_root}/GIT_COMMIT")" == "${expected_commit}" ]] || { echo 'bundle Git commit mismatch' >&2; exit 73; }
[[ "$(tr -d '\r\n' < "${bundle_root}/GIT_TREE")" == "${expected_tree}" ]] || { echo 'bundle Git tree mismatch' >&2; exit 74; }
[[ "$(tr -d '\r\n' < "${bundle_root}/PYTORCH_IMAGE_DIGEST")" == "${expected_manifest_digest}" ]] || { echo 'bundle image digest mismatch' >&2; exit 75; }

(cd "${wheelhouse}" && sha256sum --check SHA256SUMS)
for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  [[ -f "${model_root}/${arm}/SHA256SUMS" ]] || { echo "${arm} SHA256SUMS missing" >&2; exit 76; }
  [[ -f "${model_root}/${arm}/runtime-file-manifest.v4.json" ]] || { echo "${arm} runtime manifest missing" >&2; exit 77; }
  [[ -f "${jobs}/${arm}.json" ]] || { echo "${arm} job manifest missing" >&2; exit 78; }
  (cd "${model_root}/${arm}" && sha256sum --check SHA256SUMS)
done

python - "${remote_root}" "${expected_commit}" "${expected_tree}" "${expected_manifest_digest}" <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
expected_commit, expected_tree, expected_digest = sys.argv[2:]
bundle = root / "current"
wheelhouse = root / "wheelhouse"
models = root / "models"
jobs = root / "jobs"
incoming = root / "incoming"
forbidden_path = re.compile(
    r"qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|protected[_-]?evaluator",
    re.IGNORECASE,
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


supplement = root / "supplement-wheelhouse-v7"
for surface in (incoming, bundle, wheelhouse, supplement, models, jobs):
    if not surface.is_dir():
        raise SystemExit(f"required remote surface is missing: {surface.name}")
    for path in surface.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"remote symlink is forbidden: {path.relative_to(root).as_posix()}")
        if forbidden_path.search(path.relative_to(root).as_posix()):
            raise SystemExit(f"forbidden remote path detected: {path.relative_to(root).as_posix()}")


def checksum_paths(directory: Path) -> set[str]:
    paths: set[str] = set()
    for number, line in enumerate((directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"[a-f0-9]{64}  ([^\r\n]+)", line)
        if match is None or match.group(1) in paths:
            raise SystemExit(f"malformed SHA256SUMS entry: {directory.name}:{number}")
        paths.add(match.group(1))
    return paths


def regular_files(directory: Path) -> set[str]:
    return {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}


manifest = json.loads((bundle / "BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
body = dict(manifest)
recorded = body.pop("manifest_sha256", None)
if recorded != canonical_sha(body):
    raise SystemExit("bundle manifest self-hash mismatch")
if (
    manifest.get("git_commit") != expected_commit
    or manifest.get("git_tree") != expected_tree
    or manifest.get("official_pytorch_image_digest") != expected_digest
):
    raise SystemExit("bundle manifest identity binding mismatch")
entries = manifest.get("files", [])
listed = {item.get("path") for item in entries}
metadata = {"BUNDLE_MANIFEST.json", "GIT_COMMIT", "GIT_TREE", "PYTORCH_IMAGE_DIGEST"}
if regular_files(bundle) != listed | metadata:
    raise SystemExit("remote bundle tree is not the exact frozen bundle")
for item in entries:
    path = bundle / item["path"]
    if path.stat().st_size != item["size_bytes"] or digest(path) != item["sha256"]:
        raise SystemExit(f"bundle file hash mismatch: {item['path']}")

for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
    directory = models / arm
    checksummed = checksum_paths(directory)
    expected = checksummed | {"SHA256SUMS", "runtime-file-manifest.v4.json"}
    if regular_files(directory) != expected:
        raise SystemExit(f"{arm} remote model tree is not the exact frozen runtime tree")

wheelhouse_files = checksum_paths(wheelhouse)
if regular_files(wheelhouse) != wheelhouse_files | {"SHA256SUMS", "WHEELHOUSE_VALIDATION.json"}:
    raise SystemExit("remote wheelhouse tree is not the exact Actions artifact")
wheelhouse_receipt = json.loads((wheelhouse / "WHEELHOUSE_VALIDATION.json").read_text(encoding="utf-8"))
if (
    wheelhouse_receipt.get("status") != "PASS"
    or wheelhouse_receipt.get("offline_install") != "PASS"
    or wheelhouse_receipt.get("torch_wheel_included") is not False
):
    raise SystemExit("remote wheelhouse validation receipt is invalid")

expected_jobs = {f"ARM-0{number}.json" for number in range(2, 6)}
if regular_files(jobs) != expected_jobs:
    raise SystemExit("remote job tree is not the four frozen manifests")
for number in range(2, 6):
    arm = f"ARM-0{number}"
    payload = json.loads((jobs / f"{arm}.json").read_text(encoding="utf-8"))
    body = dict(payload)
    job_sha = body.pop("job_sha256", None)
    if (
        job_sha != canonical_sha(body)
        or payload.get("arm_id") != arm
        or payload.get("cuda_visible_devices") != str(number - 2)
        or payload.get("mode") != "synthetic_preflight_only"
        or payload.get("measured_retrieval_allowed") is not False
        or payload.get("network_model_download_allowed") is not False
    ):
        raise SystemExit(f"unsafe remote job manifest: {arm}")
PY

python -m venv --system-site-packages "${remote_root}/venv"
"${remote_root}/venv/bin/python" -m pip install \
  --disable-pip-version-check --no-index --find-links "${wheelhouse}" \
  -r "${bundle_root}/containers/a1_2_vast_4x3090/runtime/requirements.v2.txt"
"${remote_root}/venv/bin/python" -m pip install \
  --disable-pip-version-check --no-index --find-links "${supplement}" \
  -r "${supplement}/requirements.preflight-supplement.v7.txt"

for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m \
    myis_research.armindex.a1_2_runtime_minimal validate-manifest \
    --repository-root "${bundle_root}" --arm "${arm}" --model-directory "${model_root}/${arm}"
done

PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m \
  myis_research.armindex.a1_2_live_preflight_packaging_v8 \
  --repository-root "${bundle_root}" validate-remote-lineage \
  --expected-commit "${expected_commit}" --expected-tree "${expected_tree}"

"${remote_root}/venv/bin/python" - <<'PY'
from importlib.metadata import version
import os
import torch

expected = {
    "accelerate": "1.6.0",
    "jsonschema": "4.25.1",
    "pydantic": "2.13.4",
    "pyyaml": "6.0.2",
    "safetensors": "0.5.3",
    "sentence-transformers": "4.1.0",
    "structlog": "26.1.0",
    "transformers": "4.51.3",
}
assert os.environ["HF_HUB_OFFLINE"] == "1"
assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
assert torch.__version__ == "2.6.0+cu118"
assert torch.version.cuda == "11.8"
assert torch.cuda.is_available()
for package, locked in expected.items():
    assert version(package) == locked, (package, version(package), locked)
print({"status": "offline_dependencies_pass", "torch": torch.__version__, "cuda": torch.version.cuda})
PY

if find "${bundle_root}" -type d -name __pycache__ -print -quit | grep -q .; then
  echo 'v8 verification wrote Python bytecode into the frozen bundle' >&2
  exit 82
fi

mkdir -p "${output_root}/preflight"
PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m \
  myis_research.armindex.a1_2_live_preflight runtime-identity \
  --remote-root "${remote_root}" \
  --output "${output_root}/preflight/runtime-identity.json" \
  --expected-manifest-digest "${expected_manifest_digest}" \
  --image-observation-mode "${image_observation_mode}" \
  --bundle-sha256 "${expected_bundle_sha256}"

PYTHONPATH="${bundle_root}/src" "${remote_root}/venv/bin/python" -m \
  myis_research.armindex.a1_2_live_preflight_packaging_v8 \
  --repository-root "${bundle_root}" write-verification-marker \
  --marker "${output_root}/preflight/verification-pass.v8.json" \
  --expected-commit "${expected_commit}" --expected-tree "${expected_tree}" \
  --expected-manifest-digest "${expected_manifest_digest}" \
  --expected-bundle-sha256 "${expected_bundle_sha256}"
