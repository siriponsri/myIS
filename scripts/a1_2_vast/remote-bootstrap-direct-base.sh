#!/usr/bin/env bash
set -euo pipefail

image_reference="${1:?image reference is required}"
remote_root="${2:?remote root is required}"
expected_commit="${3:?expected Git commit is required}"
expected_tree="${4:?expected Git tree is required}"
expected_manifest_digest="${5:?expected manifest digest is required}"

[[ "${image_reference}" == "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime" ]] || { echo 'unexpected image reference' >&2; exit 64; }
[[ "${expected_manifest_digest}" == "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20" ]] || { echo 'unexpected image manifest digest' >&2; exit 65; }
image_rows="$(docker image inspect --format '{{.Id}}|{{join .RepoDigests ","}}|{{.Os}}|{{.Architecture}}' "${image_reference}" 2>/dev/null)" || { echo 'base image is not present locally; network pull is forbidden' >&2; exit 66; }
grep -F "${expected_manifest_digest}" <<<"${image_rows}" >/dev/null || { echo 'best observable image identity does not include the expected manifest digest' >&2; exit 67; }
[[ "${image_rows}" == *'|linux|amd64' ]] || { echo 'base image platform is not linux/amd64' >&2; exit 68; }

bundle_root="${remote_root}/current"
wheelhouse="${remote_root}/wheelhouse"
model_root="${remote_root}/models"
jobs="${remote_root}/jobs"
[[ -f "${bundle_root}/BUNDLE_MANIFEST.json" ]] || { echo 'frozen code bundle manifest missing' >&2; exit 69; }
[[ -f "${wheelhouse}/SHA256SUMS" ]] || { echo 'Linux wheelhouse SHA256SUMS missing' >&2; exit 70; }
(cd "${wheelhouse}" && sha256sum --check SHA256SUMS)
for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  [[ -f "${model_root}/${arm}/SHA256SUMS" ]] || { echo "${arm} SHA256SUMS missing" >&2; exit 71; }
  (cd "${model_root}/${arm}" && sha256sum --check SHA256SUMS)
  [[ -f "${jobs}/${arm}.json" ]] || { echo "${arm} job manifest missing" >&2; exit 72; }
done
python - "${remote_root}" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
bundle = root / "current"
wheelhouse = root / "wheelhouse"
models = root / "models"
jobs = root / "jobs"
incoming = root / "incoming"
forbidden_path = re.compile(
    r"qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|protected[_-]?evaluator",
    re.IGNORECASE,
)

for surface in (incoming, bundle, wheelhouse, models, jobs):
    if not surface.is_dir():
        raise SystemExit(f"required remote surface is missing: {surface.name}")
    for path in surface.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"remote symlink is forbidden: {path.relative_to(root).as_posix()}")
        relative = path.relative_to(root).as_posix()
        if forbidden_path.search(relative):
            raise SystemExit(f"forbidden remote path detected: {relative}")


def checksum_paths(directory: Path) -> set[str]:
    paths: set[str] = set()
    for number, line in enumerate((directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"[a-f0-9]{64}  ([^\r\n]+)", line)
        if match is None or match.group(1) in paths:
            raise SystemExit(f"malformed SHA256SUMS entry: {directory.name}:{number}")
        paths.add(match.group(1))
    return paths


def regular_files(directory: Path) -> set[str]:
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    }


for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
    directory = models / arm
    checksummed = checksum_paths(directory)
    expected = checksummed | {"SHA256SUMS", "runtime-file-manifest.v4.json"}
    if regular_files(directory) != expected:
        raise SystemExit(f"{arm} remote model tree is not the exact frozen runtime tree")
    manifest = json.loads((directory / "runtime-file-manifest.v4.json").read_text(encoding="utf-8"))
    if manifest.get("arm_id") != arm or {item.get("path") for item in manifest.get("files", [])} != checksummed:
        raise SystemExit(f"{arm} runtime manifest does not bind the checksummed files")

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

bundle_manifest = json.loads((bundle / "BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
bundle_files = {item.get("path") for item in bundle_manifest.get("files", [])}
bundle_metadata = {"BUNDLE_MANIFEST.json", "GIT_COMMIT", "GIT_TREE", "PYTORCH_IMAGE_DIGEST"}
if regular_files(bundle) != bundle_files | bundle_metadata:
    raise SystemExit("remote bundle tree is not the exact frozen bundle")

expected_jobs = {f"ARM-0{number}.json" for number in range(2, 6)}
if regular_files(jobs) != expected_jobs:
    raise SystemExit("remote job tree is not the four frozen manifests")
for number in range(2, 6):
    arm = f"ARM-0{number}"
    payload = json.loads((jobs / f"{arm}.json").read_text(encoding="utf-8"))
    if (
        payload.get("arm_id") != arm
        or payload.get("cuda_visible_devices") != str(number - 2)
        or payload.get("mode") != "synthetic_preflight_only"
        or payload.get("measured_retrieval_allowed") is not False
        or payload.get("network_model_download_allowed") is not False
    ):
        raise SystemExit(f"unsafe remote job manifest: {arm}")
PY
[[ "${MYIS_REMOTE_MODE:-}" == "a1_2_preflight_only" ]] || { echo 'remote mode is not preflight-only' >&2; exit 74; }
python --version
python - <<'PY'
import os
import torch
assert os.environ.get('HF_HUB_OFFLINE') == '1'
assert os.environ.get('TRANSFORMERS_OFFLINE') == '1'
assert torch.__version__.split('+')[0].startswith('2.6.')
assert torch.version.cuda == '11.8'
print({'status': 'base_runtime_visible', 'torch': torch.__version__, 'cuda': torch.version.cuda, 'network_model_download': False})
PY
python -m venv --system-site-packages "${remote_root}/venv"
"${remote_root}/venv/bin/python" -m pip install --no-index --find-links "${wheelhouse}" -r "${bundle_root}/containers/a1_2_vast_4x3090/runtime/requirements.v2.txt"
PYTHONPATH="${bundle_root}/src" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_runtime_minimal_direct_base validate --repository-root "${bundle_root}"
