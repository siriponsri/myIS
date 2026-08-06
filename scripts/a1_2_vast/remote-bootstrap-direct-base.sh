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
sha256sum --check "${wheelhouse}/SHA256SUMS"
for arm in ARM-02 ARM-03 ARM-04 ARM-05; do
  [[ -f "${model_root}/${arm}/SHA256SUMS" ]] || { echo "${arm} SHA256SUMS missing" >&2; exit 71; }
  (cd "${model_root}/${arm}" && sha256sum --check SHA256SUMS)
  [[ -f "${jobs}/${arm}.json" ]] || { echo "${arm} job manifest missing" >&2; exit 72; }
done
grep -R -E -i 'qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|protected_evaluator' "${remote_root}/incoming" "${remote_root}/current" "${model_root}" "${jobs}" >/dev/null && { echo 'forbidden remote path/content detected' >&2; exit 73; } || true
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
"${remote_root}/venv/bin/python" -m pip install --no-index --no-deps --find-links "${wheelhouse}" -r "${bundle_root}/containers/a1_2_vast_4x3090/runtime/requirements.v2.txt"
PYTHONPATH="${bundle_root}/src" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "${remote_root}/venv/bin/python" -m myis_research.armindex.a1_2_runtime_minimal_direct_base validate --repository-root "${bundle_root}"
