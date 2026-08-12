from __future__ import annotations

import copy
import io
import json
import os
import tarfile
from pathlib import Path

import pytest

from myis_research.armindex import a2_deployment_package as deployment
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-deployment-test01"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="ascii")


def _write_model(root: Path, arm_id: str) -> None:
    rows = []
    sums = []
    for index in range(12):
        relative = f"file-{index:02d}.bin"
        payload = f"{arm_id}-{index}\n".encode("ascii")
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        sha256 = file_sha256(path)
        rows.append({"path": relative, "sha256": sha256, "size_bytes": len(payload)})
        sums.append(f"{sha256}  {relative}\n")
    body = {"arm_id": arm_id, "file_count": 12, "files": rows}
    _write_json(root / "runtime-file-manifest.v4.json", {**body, "manifest_sha256": canonical_sha256(body)})
    (root / "SHA256SUMS").write_text("".join(sums), encoding="ascii")


def _write_wheelhouse(root: Path) -> None:
    sums = []
    for index in range(14):
        relative = "requirements.v2.txt" if index == 13 else f"package-{index:02d}.whl"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"wheel-{index}\n".encode("ascii"))
        sums.append(f"{file_sha256(path)}  {relative}\n")
    sums_path = root / "SHA256SUMS"
    sums_path.write_text("".join(sums), encoding="ascii")
    _write_json(
        root / "WHEELHOUSE_VALIDATION.json",
        {
            "status": "PASS",
            "offline_install": "PASS",
            "contains_models_or_protected_data": False,
            "platform": "linux/amd64",
            "python": "3.11",
            "wheel_count": 13,
            "sha256sums_sha256": file_sha256(sums_path),
        },
    )


def _write_handoff(root: Path, role: str, count: int) -> None:
    rows = []
    for index in range(count):
        relative = (
            "safe-return/safe-return.tar.gz"
            if role == "a1_baseline" and index == 0
            else f"aggregate/file-{index:02d}.json"
        )
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"{role}-{index}\n".encode("ascii"))
        row = {"sha256": file_sha256(path), "size_bytes": path.stat().st_size}
        row["relative_path" if role == "a1_baseline" else "file_name"] = relative
        rows.append(row)
    if role == "a1_baseline":
        body = {
            "schema_version": "myis.armindex-a1.2-a2-baseline-handoff.v16",
            "handoff_id": "a12-v16-20260811-r15-a2-baseline-handoff-v16",
            "status": "PASS",
            "attempt_id": "a12-v16-20260811-r15",
            "copied_file_count": count,
            "copied_files": rows,
            "safe_return_archive_sha256": rows[0]["sha256"],
            "a2_execution_authorized": False,
        }
        name = "handoff-manifest.v16.json"
    else:
        body = {
            "schema_version": (
                "myis.armindex-a1.2-remote-closeout-mirror.v16"
                if role == "a1_closeout"
                else "myis.armindex-a1.2-journal-eda-handoff.v16"
            ),
            "status": "PASS",
            "attempt_id": "a12-v16-20260811-r15",
            "aggregate_safe": True,
            "file_count": count,
            "files": rows,
        }
        name = "mirror-manifest.v16.json" if role == "a1_closeout" else "handoff-manifest.v16.json"
    _write_json(root / name, {**body, "manifest_sha256": canonical_sha256(body)})


def _assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> deployment.A2DeploymentAssets:
    model_roots = {}
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        model_root = tmp_path / "models" / arm_id
        _write_model(model_root, arm_id)
        model_roots[arm_id] = model_root
    wheelhouse = tmp_path / "wheelhouse"
    _write_wheelhouse(wheelhouse)
    baseline = tmp_path / "baseline"
    journal = tmp_path / "journal"
    closeout = tmp_path / "closeout"
    _write_handoff(baseline, "a1_baseline", 28)
    _write_handoff(journal, "a1_journal", 7)
    _write_handoff(closeout, "a1_closeout", 11)
    runtime_identity = tmp_path / "runtime-identity.json"
    runtime_body = {
        "schema_version": "myis.armindex-a1.2-live-ssh-runtime-receipt.v16",
        "receipt_kind": "ssh_runtime",
        "receipt_id": "a12-v16-20260811-r15-ssh-runtime-v16",
        "revision_id": "a1.2-live-admission-v16",
        "attempt_id": "a12-v16-20260811-r15",
        "status": "PASS_SSH_RUNTIME",
        "claim_boundary": (
            "Aggregate-safe SSH and runtime identity observation only; no endpoint, "
            "host name, credential, protected input, launch, retrieval, or provider "
            "action is retained or performed."
        ),
        "runtime": {
            "observed_at_utc": "2026-08-11T04:27:37Z",
            "instance_identity_sha256": "1" * 64,
            "host_identity_sha256": "2" * 64,
            "ssh_host_key_sha256": "3" * 64,
            "gpu_uuid_set_sha256": "4" * 64,
            "platform": "linux/amd64",
            "python": "3.11",
            "torch": "2.6.0+cu118",
            "cuda": "11.8",
            "gpu_count": 4,
            "gpu_model": "NVIDIA GeForce RTX 3090",
            "vram_mib_each": 24576,
            "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
            "image_manifest_digest": (
                "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
            ),
            "runtime_evidence_sha256": "5" * 64,
        },
        "provider_identity_receipt_sha256": "6" * 64,
        "ssh_runtime_input_sha256": "7" * 64,
    }
    _write_json(
        runtime_identity,
        {**runtime_body, "receipt_sha256": canonical_sha256(runtime_body)},
    )
    frozen_bundle = tmp_path / "a1-bundle.tar.gz"
    frozen_bundle.write_bytes(b"frozen-a1-bundle\n")
    a1_body = {
        "status": "ENGINEERING_BUNDLE_BUILT_NOT_ADOPTED",
        "clean_worktree": True,
        "pushed_to_origin_main": True,
        "frozen_bundle_sha256": file_sha256(frozen_bundle),
    }
    a1_receipt = tmp_path / "a1-bundle-receipt.json"
    _write_json(a1_receipt, {**a1_body, "receipt_sha256": canonical_sha256(a1_body)})
    a2_bundle = tmp_path / "a2-bundle.tar.gz"
    a2_bundle.write_bytes(b"a2-bundle\n")
    a2_receipt = tmp_path / "a2-bundle-receipt.json"
    a2_value = {
        "receipt_sha256": "2" * 64,
        "bundle_sha256": file_sha256(a2_bundle),
        "bundle_manifest_sha256": "3" * 64,
        "git_commit": "4" * 40,
        "git_tree": "5" * 40,
    }
    _write_json(a2_receipt, a2_value)
    monkeypatch.setattr(
        deployment,
        "validate_execution_bundle",
        lambda *_args, **_kwargs: {**a2_value, "validation_status": "PASS"},
    )
    return deployment.A2DeploymentAssets(
        model_roots=model_roots,
        wheelhouse_root=wheelhouse,
        a1_baseline_root=baseline,
        a1_journal_root=journal,
        a1_closeout_root=closeout,
        runtime_identity_path=runtime_identity,
        frozen_a1_bundle_path=frozen_bundle,
        frozen_a1_bundle_receipt_path=a1_receipt,
        a2_bundle_path=a2_bundle,
        a2_bundle_receipt_path=a2_receipt,
    )


def test_build_and_revalidate_hash_only_deployment_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    package = tmp_path / "a2-deployment.tar.gz"
    result = deployment.build_deployment_package(
        ROOT, attempt_id=ATTEMPT, output_path=package, assets=assets
    )

    with tarfile.open(package, "r:gz") as archive:
        assert [member.name for member in archive.getmembers()] == [
            "A2_DEPLOYMENT_MANIFEST.json"
        ]
    assert result["receipt"]["model_file_counts"] == {
        "ARM-02": 12,
        "ARM-03": 12,
        "ARM-04": 12,
        "ARM-05": 12,
    }
    assert result["receipt"]["wheelhouse_declared_file_count"] == 14
    assert result["receipt"]["protected_payload_included"] is False
    assert result["receipt"]["model_or_wheel_bytes_included"] is False
    assert result["receipt"]["scientific_authority"] is False
    assert result["receipt"]["measured_execution_authorized"] is False
    assert (
        deployment.validate_deployment_package(
            ROOT, package_path=package, receipt=result["receipt"], assets=assets
        )["validation_status"]
        == "PASS"
    )


def test_deployment_rejects_model_manifest_member_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    (assets.model_roots["ARM-03"] / "file-04.bin").write_bytes(b"mutated\n")
    with pytest.raises(deployment.A2DeploymentPackageError, match="member hash drift"):
        deployment.build_deployment_package(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "package.tar.gz", assets=assets
        )


def test_deployment_rejects_wheelhouse_manifest_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    sums = assets.wheelhouse_root / "SHA256SUMS"
    sums.write_text(sums.read_text(encoding="ascii").replace("a", "b", 1), encoding="ascii")
    with pytest.raises(deployment.A2DeploymentPackageError):
        deployment.build_deployment_package(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "package.tar.gz", assets=assets
        )


def test_deployment_rejects_forbidden_manifest_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    manifest_path = assets.a1_journal_root / "handoff-manifest.v16.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    source = assets.a1_journal_root / manifest["files"][0]["file_name"]
    target = assets.a1_journal_root / "qrels.json"
    target.write_bytes(source.read_bytes())
    manifest["files"][0]["file_name"] = "qrels.json"
    manifest["manifest_sha256"] = canonical_sha256(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    _write_json(manifest_path, manifest)
    with pytest.raises(deployment.A2DeploymentPackageError, match="protected boundary"):
        deployment.build_deployment_package(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "package.tar.gz", assets=assets
        )


def test_deployment_rejects_symlinked_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    source = assets.model_roots["ARM-02"] / "file-00.bin"
    source.unlink()
    try:
        os.symlink(assets.model_roots["ARM-03"] / "file-00.bin", source)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(deployment.A2DeploymentPackageError, match="missing or unsafe"):
        deployment.build_deployment_package(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "package.tar.gz", assets=assets
        )


def test_deployment_rejects_destroyed_instance_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    runtime = json.loads(assets.runtime_identity_path.read_text(encoding="ascii"))
    runtime["provider_instance_id"] = "47411176"
    _write_json(assets.runtime_identity_path, runtime)
    with pytest.raises(deployment.A2DeploymentPackageError, match="schema drift"):
        deployment.build_deployment_package(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "package.tar.gz", assets=assets
        )


def test_deployment_rejects_runtime_receipt_self_hash_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    runtime = json.loads(assets.runtime_identity_path.read_text(encoding="ascii"))
    runtime["runtime"]["host_identity_sha256"] = "8" * 64
    _write_json(assets.runtime_identity_path, runtime)
    with pytest.raises(deployment.A2DeploymentPackageError, match="self-hash drift"):
        deployment.build_deployment_package(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "package.tar.gz", assets=assets
        )


def test_deployment_validator_rejects_extra_archive_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    package = tmp_path / "package.tar.gz"
    result = deployment.build_deployment_package(
        ROOT, attempt_id=ATTEMPT, output_path=package, assets=assets
    )
    with tarfile.open(package, "r:gz") as archive:
        manifest = archive.extractfile("A2_DEPLOYMENT_MANIFEST.json").read()
    replacement = tmp_path / "replacement.tar.gz"
    with tarfile.open(replacement, "w:gz") as archive:
        info = tarfile.TarInfo("A2_DEPLOYMENT_MANIFEST.json")
        info.size = len(manifest)
        archive.addfile(info, io.BytesIO(manifest))
        extra = b"model bytes\n"
        info = tarfile.TarInfo("model.bin")
        info.size = len(extra)
        archive.addfile(info, io.BytesIO(extra))
    bad_receipt = copy.deepcopy(result["receipt"])
    bad_receipt["package_sha256"] = file_sha256(replacement)
    bad_receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in bad_receipt.items() if key != "receipt_sha256"}
    )
    with pytest.raises(deployment.A2DeploymentPackageError, match="closure is not hash-only"):
        deployment.validate_deployment_package(
            ROOT, package_path=replacement, receipt=bad_receipt
        )


def test_deployment_reprobe_rejects_source_drift_after_package_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets = _assets(tmp_path, monkeypatch)
    package = tmp_path / "package.tar.gz"
    result = deployment.build_deployment_package(
        ROOT, attempt_id=ATTEMPT, output_path=package, assets=assets
    )
    (assets.model_roots["ARM-05"] / "file-09.bin").write_bytes(b"drift\n")
    with pytest.raises(deployment.A2DeploymentPackageError, match="member hash drift"):
        deployment.validate_deployment_package(
            ROOT, package_path=package, receipt=result["receipt"], assets=assets
        )
