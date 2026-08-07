from __future__ import annotations

import json
import hashlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_live_preflight_repair_v7 import (
    BINDING_PATHS,
    CONTRACT_PATH,
    RECEIPT_PATH,
    validate_live_repair_v7,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256


ROOT = Path(__file__).resolve().parents[1]
_VALIDATOR_PATH = ROOT / "scripts/a1_2_vast/validate_preflight_supplement_v7.py"
_VALIDATOR_SPEC = importlib.util.spec_from_file_location("a1_2_v7_supplement_validator", _VALIDATOR_PATH)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)
SupplementValidationError = _VALIDATOR.SupplementValidationError
validate_supplement = _VALIDATOR.validate_supplement


def test_v7_same_instance_repair_is_valid_and_launch_locked() -> None:
    result = validate_live_repair_v7(ROOT)
    assert result == {
        "status": "same_instance_repair_prepared_preflight_pending",
        "revision_id": "a1.2-live-preflight-same-instance-repair-v7",
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
    }


def test_v7_receipt_binds_v6_policy_scripts_locks_and_code() -> None:
    contract = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    assert {item["uri"] for item in contract["bindings"]} == {
        path.as_posix() for path in BINDING_PATHS
    }
    assert receipt["contract_sha256"] == file_sha256(ROOT / CONTRACT_PATH)
    assert receipt["v6_receipt_sha256"] == json.loads(
        (ROOT / "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-correction.receipt.v6.json").read_text(encoding="utf-8")
    )["receipt_sha256"]
    body = dict(receipt)
    assert body.pop("receipt_sha256") == canonical_sha256(body)


def test_v7_preserves_both_failures_and_requires_fresh_bytecode_suppressed_root() -> None:
    contract = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
    failures = {item["failure_id"] for item in contract["preserved_live_failures"]}
    assert failures == {
        "v6-initial-wheelhouse-missing-pydantic",
        "v6-supplement-repair-mutated-pycache-tree",
    }
    active = contract["active_correction"]
    assert active["new_remote_root"] == "/opt/myis/a1.2-v7"
    assert active["source_remote_root"] == "/opt/myis/a1.2-v6"
    assert active["required_environment"] == {"PYTHONDONTWRITEBYTECODE": "1"}
    assert active["upload_only"] == ["new_frozen_code_bundle"]
    assert active["reuse_only_after_sha256_validation"] == [
        "models",
        "wheelhouse",
        "jobs",
        "supplement_wheelhouse_v7",
    ]


def test_v7_coordinator_and_bootstrap_keep_repair_bounded() -> None:
    coordinator = (ROOT / "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1").read_text(encoding="utf-8")
    bootstrap = (ROOT / "scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh").read_text(encoding="utf-8")
    assert "test ! -e ${RemoteRoot}" in coordinator
    assert "cp -a ${SourceRemoteRoot}/models/. ${RemoteRoot}/models/" in coordinator
    assert "PYTHONDONTWRITEBYTECODE=1" in coordinator
    assert "scp" in coordinator and "frozen-code-bundle.tar.gz" in coordinator
    assert "PYTHONDONTWRITEBYTECODE=1" in bootstrap
    assert "sha256sum --check SHA256SUMS" in bootstrap
    assert "validate_preflight_supplement_v7.py" in bootstrap
    assert "__pycache__" in bootstrap


def _write_valid_supplement(root: Path) -> None:
    root.mkdir()
    (root / "requirements.preflight-supplement.v7.txt").write_text(
        "jsonschema==4.25.1\npydantic==2.13.4\nstructlog==26.1.0\n",
        encoding="utf-8",
    )
    (root / "pydantic-2.13.4-py3-none-any.whl").write_bytes(b"fixture wheel")
    (root / "SUPPLEMENT_VALIDATION.json").write_text(
        json.dumps(
            {
                "schema_version": "myis.owner-a1.2-preflight-supplement-wheelhouse.v7",
                "status": "PASS",
                "platform": "linux/amd64",
                "machine": "x86_64",
                "dependencies": {
                    "jsonschema": "4.25.1",
                    "pydantic": "2.13.4",
                    "structlog": "26.1.0",
                },
                "wheel_count": 1,
                "torch_wheel_included": False,
                "offline_install": "PASS",
                "contains_models_or_protected_data": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    entries = sorted(path for path in root.iterdir() if path.is_file())
    (root / "SHA256SUMS").write_text(
        "".join(f"{'a' * 64}  {path.name}\n" for path in entries), encoding="ascii"
    )


def test_v7_supplement_validator_rejects_extra_tree_and_bad_receipt(tmp_path: Path) -> None:
    supplement = tmp_path / "supplement"
    _write_valid_supplement(supplement)
    assert validate_supplement(supplement)["status"] == "PASS"

    (supplement / "unexpected.txt").write_text("not allowed\n", encoding="ascii")
    with pytest.raises(SupplementValidationError, match="exact checksummed"):
        validate_supplement(supplement)
    (supplement / "unexpected.txt").unlink()

    receipt_path = supplement / "SUPPLEMENT_VALIDATION.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["status"] = "BLOCKED"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(SupplementValidationError, match="receipt value"):
        validate_supplement(supplement)


def test_v7_coordinator_dry_run_rejects_unpinned_image_digest(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("placeholder\n", encoding="ascii")
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    script = ROOT / "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1"
    common = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(script),
        "-Action",
        "stage-repair",
        "-HostName",
        "example.invalid",
        "-Port",
        "22",
        "-UserName",
        "root",
        "-KeyPath",
        str(key),
        "-BundlePath",
        str(bundle),
        "-ExpectedGitCommit",
        "a" * 40,
        "-ExpectedGitTree",
        "b" * 40,
        "-ExpectedBundleSha256",
        digest,
        "-DryRun",
    ]
    passed = subprocess.run(common, capture_output=True, text=True, check=False)
    assert passed.returncode == 0, passed.stderr
    assert json.loads(passed.stdout)["status"] == "dry_run_validated"

    rejected = subprocess.run(
        common[:-1] + ["-ExpectedManifestDigest", "sha256:" + "0" * 64, "-DryRun"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "ExpectedManifestDigest must equal the pinned" in rejected.stderr
