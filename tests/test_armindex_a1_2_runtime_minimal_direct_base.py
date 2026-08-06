from __future__ import annotations

import json
import subprocess
from pathlib import Path

from myis_research.armindex.a1_2_runtime_minimal_direct_base import (
    IMAGE_REFERENCE,
    RECEIPT_PATH,
    RESOLVED_MANIFEST_DIGEST,
    REVISION_ID,
    validate_direct_base_revision,
)
from myis_research.kernel.canonical import file_sha256


ROOT = Path(__file__).resolve().parents[1]


def test_direct_base_revision_validates_and_preserves_zero_counters() -> None:
    result = validate_direct_base_revision(ROOT)
    assert result["revision_id"] == REVISION_ID
    assert result["image_reference"] == IMAGE_REFERENCE
    assert result["resolved_manifest_digest"] == RESOLVED_MANIFEST_DIGEST
    assert result["platform"] == "linux/amd64"
    assert result["launch_allowed"] is False
    assert result["adopted_for_execution"] is False
    assert result["measured_runs"] == 0
    assert result["charged_usd"] == 0


def test_manifest_digest_is_registry_identity_not_layer_identity() -> None:
    image = json.loads((ROOT / "control/armindex/a1.2/image-digest-contract.direct-base.v5.json").read_text(encoding="utf-8"))
    assert image["resolved_manifest_digest"] == RESOLVED_MANIFEST_DIGEST
    assert image["manifest_media_type"] == "application/vnd.docker.distribution.manifest.v2+json"
    assert image["verification"]["layer_digest_is_not_identity"] is True
    assert image["platform"] == "linux/amd64"


def test_active_direct_path_has_no_custom_image_or_nested_container_steps() -> None:
    contract = json.loads((ROOT / "control/armindex/a1.2/execution-contract.direct-base.v5.json").read_text(encoding="utf-8"))
    assert contract["active_path"] == {
        "direct_base_launch": True,
        "custom_image_build": False,
        "docker_save": False,
        "image_upload": False,
        "docker_load": False,
        "nested_container": False,
        "runtime_model_download": False,
        "network_fallback": False,
    }
    bootstrap = (ROOT / "scripts/a1_2_vast/remote-bootstrap-direct-base.sh").read_text(encoding="utf-8")
    assert "docker run" not in bootstrap
    assert "docker load" not in bootstrap
    assert "--no-index" in bootstrap
    assert "--system-site-packages" in bootstrap
    coordinator = (ROOT / "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinator.ps1").read_text(encoding="utf-8")
    assert "ImageArchivePath" not in coordinator
    assert "docker load" not in coordinator.lower()
    assert "WheelhousePath" in coordinator
    assert "ModelRoot" in coordinator
    assert "JobManifestRoot" in coordinator


def test_receipt_is_aggregate_safe_and_binds_contract_and_policy() -> None:
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    assert receipt["contract_sha256"] == file_sha256(ROOT / "control/armindex/a1.2/execution-contract.direct-base.v5.json")
    assert receipt["policy_sha256"] == file_sha256(ROOT / "control/armindex/a1.2/runtime-minimal-model-policy.v4.json")
    forbidden = ("qrels", "membership", "query_ids", "private_key", "openai_api_key")
    encoded = json.dumps(receipt, ensure_ascii=True).lower()
    assert all(value not in encoded for value in forbidden)


def test_direct_coordinator_supports_dry_run_without_secrets(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("placeholder\n", encoding="ascii")
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    models = tmp_path / "models"
    (models / "ARM-02").mkdir(parents=True)
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    collect = tmp_path / "collect"
    collect.mkdir()
    script = ROOT / "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinator.ps1"
    common = ["powershell", "-NoProfile", "-NonInteractive", "-File", str(script), "-Action", "status", "-HostName", "example.invalid", "-Port", "22", "-UserName", "root", "-KeyPath", str(key)]
    actions = {
        "upload": ["-BundlePath", str(bundle), "-WheelhousePath", str(wheelhouse), "-ModelRoot", str(models), "-JobManifestRoot", str(jobs)],
        "verify": ["-ExpectedGitCommit", "a" * 40, "-ExpectedGitTree", "b" * 40],
        "start": [],
        "status": [],
        "collect": ["-CollectPath", str(collect)],
        "teardown": [],
    }
    for action, extra in actions.items():
        args = list(common)
        args[args.index("status")] = action
        result = subprocess.run(args + extra + ["-DryRun"], capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["status"] == "dry_run_validated"
        assert str(key) not in result.stdout
