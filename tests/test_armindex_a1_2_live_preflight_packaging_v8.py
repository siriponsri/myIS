from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

import myis_research.armindex.a1_2_live_preflight_packaging_v8 as v8
from myis_research.armindex.a1_2_live_preflight_packaging_v8 import (
    CONTRACT_PATH,
    COORDINATOR_PATH,
    FORBIDDEN_PATH,
    IMAGE_DIGEST,
    RECEIPT_PATH,
    REQUIRED_VALIDATOR_FILES,
    REVISION_ID,
    SCHEMA_PATH,
    V2_RECEIPT_PATH,
    V3_RECEIPT_PATH,
    V5_RECEIPT_PATH,
    PackagingRepairError,
    build_validation_complete_bundle,
    select_bundle_paths,
    validate_remote_lineage,
    validate_revision,
    validate_verification_marker,
    validation_lineage_paths,
    write_verification_marker,
)
from myis_research.armindex.a1_2_vast import V1_BINDINGS
from myis_research.kernel.canonical import canonical_sha256, file_sha256


ROOT = Path(__file__).resolve().parents[1]


def _tracked_paths() -> list[str]:
    # Bundling itself requires a clean tracked tree.  Unit tests also run before
    # the new v8 files are staged, so model the candidate set explicitly here.
    return subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()


def _stage_repair_command(tmp_path: Path) -> list[str]:
    key = tmp_path / "key"
    bundle = tmp_path / "bundle.tar.gz"
    key.write_text("placeholder\n", encoding="ascii")
    bundle.write_bytes(b"v8 fixture bundle")
    return [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(ROOT / COORDINATOR_PATH),
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
        hashlib.sha256(bundle.read_bytes()).hexdigest(),
    ]


def _start_command(tmp_path: Path) -> list[str]:
    key = tmp_path / "key"
    key.write_text("placeholder\n", encoding="ascii")
    return [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(ROOT / COORDINATOR_PATH),
        "-Action",
        "start",
        "-HostName",
        "example.invalid",
        "-Port",
        "22",
        "-UserName",
        "root",
        "-KeyPath",
        str(key),
        "-DryRun",
    ]


def test_v8_lineage_covers_every_historical_validator_binding() -> None:
    lineage = validation_lineage_paths(ROOT)
    expected = {Path(path) for path in V1_BINDINGS}
    expected.update(REQUIRED_VALIDATOR_FILES)
    expected.update({V2_RECEIPT_PATH, V3_RECEIPT_PATH, V5_RECEIPT_PATH})

    assert expected <= lineage
    assert all((ROOT / path).is_file() for path in lineage)
    assert not any(FORBIDDEN_PATH.search(path.as_posix()) for path in lineage)


def test_v8_bundle_selection_is_deterministic_and_validation_complete() -> None:
    tracked = _tracked_paths()
    selected = select_bundle_paths(ROOT, tracked)

    assert selected == select_bundle_paths(ROOT, list(reversed(tracked)))
    assert selected == sorted(selected)
    assert {path.as_posix() for path in validation_lineage_paths(ROOT)} <= set(selected)
    assert {
        CONTRACT_PATH.as_posix(),
        RECEIPT_PATH.as_posix(),
        SCHEMA_PATH.as_posix(),
        COORDINATOR_PATH.as_posix(),
    } <= set(selected)
    assert not any(FORBIDDEN_PATH.search(path) for path in selected)


@pytest.mark.parametrize(
    "unsafe_path",
    ["src/myis_research/qrels.py", "src/myis_research/credentials.py"],
)
def test_v8_bundle_rejects_protected_or_credential_paths(unsafe_path: str) -> None:
    with pytest.raises(PackagingRepairError, match="forbidden remote path"):
        select_bundle_paths(ROOT, _tracked_paths() + [unsafe_path])


def test_v8_contract_receipt_and_schema_are_exact_and_launch_locked() -> None:
    result = validate_revision(ROOT)
    contract = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))

    assert result["revision_id"] == REVISION_ID
    assert contract["contract_id"] == REVISION_ID
    assert receipt["receipt_id"] == REVISION_ID
    assert receipt["schema_version"] == schema["properties"]["schema_version"]["const"]
    assert receipt["contract_sha256"] == file_sha256(ROOT / CONTRACT_PATH)
    assert contract["launch_allowed"] is False
    assert contract["adopted_for_execution"] is False
    assert result["measured_runs"] == 0
    assert result["charged_usd"] == 0
    body = dict(receipt)
    assert body.pop("receipt_sha256") == canonical_sha256(body)


def test_v8_bundle_extracts_without_git_and_validates_remote_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD^{commit}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    def _git_fixture(_root: Path, *arguments: str) -> str:
        if arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
            return ""
        if arguments == ("ls-files",):
            return "\n".join(_tracked_paths())
        if arguments == ("rev-parse", "HEAD^{commit}"):
            return commit
        if arguments == ("rev-parse", "HEAD^{tree}"):
            return tree
        raise AssertionError(arguments)

    monkeypatch.setattr(v8, "_git", _git_fixture)
    bundle = tmp_path / "v8-frozen-bundle.tar.gz"
    built = build_validation_complete_bundle(ROOT, bundle)
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with tarfile.open(bundle, "r:gz") as archive:
        archive.extractall(extracted)

    assert not (extracted / ".git").exists()
    manifest = json.loads((extracted / "BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["git_commit"] == built["git_commit"] == commit
    assert manifest["git_tree"] == built["git_tree"] == tree
    assert validate_remote_lineage(extracted, commit, tree)["status"] == "PASS"


def test_v8_verification_marker_rejects_self_hash_and_identity_tampering(
    tmp_path: Path,
) -> None:
    marker_path = tmp_path / "verification-pass.v8.json"
    commit, tree, bundle_sha256 = "a" * 40, "b" * 40, "c" * 64
    written = write_verification_marker(
        marker_path, commit, tree, IMAGE_DIGEST, bundle_sha256
    )
    assert validate_verification_marker(
        marker_path, commit, tree, IMAGE_DIGEST, bundle_sha256
    )["marker_sha256"] == written["marker_sha256"]

    tampered = json.loads(marker_path.read_text(encoding="utf-8"))
    tampered["git_commit"] = "d" * 40
    marker_path.write_text(json.dumps(tampered, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(PackagingRepairError, match="self-hash mismatch"):
        validate_verification_marker(marker_path, commit, tree, IMAGE_DIGEST, bundle_sha256)

    tampered["marker_sha256"] = canonical_sha256(
        {key: value for key, value in tampered.items() if key != "marker_sha256"}
    )
    marker_path.write_text(json.dumps(tampered, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(PackagingRepairError, match="identity mismatch"):
        validate_verification_marker(marker_path, commit, tree, IMAGE_DIGEST, bundle_sha256)


def test_v8_direct_start_rejects_missing_frozen_identity_without_ssh(tmp_path: Path) -> None:
    if shutil.which("powershell") is None:
        pytest.skip("PowerShell is not available")
    command = _start_command(tmp_path)
    cases = [
        ([], "ExpectedGitCommit is required and invalid."),
        (["-ExpectedGitCommit", "a" * 40], "ExpectedGitTree is required and invalid."),
        (
            ["-ExpectedGitCommit", "a" * 40, "-ExpectedGitTree", "b" * 40],
            "ExpectedBundleSha256 is required and invalid.",
        ),
    ]
    for arguments, expected_error in cases:
        rejected = subprocess.run(
            command + arguments,
            capture_output=True,
            text=True,
            check=False,
        )
        assert rejected.returncode != 0
        assert expected_error in rejected.stderr


def test_v8_active_path_uses_v8_bootstrap_and_forbids_nested_docker_steps() -> None:
    coordinator = (ROOT / COORDINATOR_PATH).read_text(encoding="utf-8")
    bootstrap = (ROOT / "scripts/a1_2_vast/remote-bootstrap-direct-base-v8.sh").read_text(
        encoding="utf-8"
    )
    assert "remote-bootstrap-direct-base-v8.sh" in coordinator
    assert "validate-verification-marker" in coordinator
    assert "validate-remote-lineage" in bootstrap
    active_path = f"{coordinator}\n{bootstrap}".lower()
    for forbidden in ("docker build", "docker run", "docker load", "docker save"):
        assert forbidden not in active_path


def test_v8_coordinator_dry_run_rejects_remote_root_traversal(tmp_path: Path) -> None:
    if shutil.which("powershell") is None:
        pytest.skip("PowerShell is not available")
    command = _stage_repair_command(tmp_path)
    completed = subprocess.run(command + ["-DryRun"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["status"] == "dry_run_validated"

    rejected = subprocess.run(
        command + ["-RemoteRoot", "/opt/myis/a1.2-v8/../escape", "-DryRun"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "without traversal" in rejected.stderr
