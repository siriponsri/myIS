"""Additive A1.2 v8 validation-complete frozen-bundle repair."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
import tarfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_live_preflight_repair_v7 import validate_live_repair_v7 as validate_v7
from .a1_2_vast import V1_BINDINGS, validate_preparation_receipt


REVISION_ID = "a1.2-live-preflight-validation-complete-bundle-v8"
IMAGE_DIGEST = "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
CONTRACT_PATH = Path(
    "control/armindex/a1.2/execution-contract.live-preflight-packaging-repair.v8.json"
)
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-live-preflight-packaging-repair.receipt.v8.json"
)
SCHEMA_PATH = Path("schemas/armindex/a1.2-live-preflight-packaging-repair.v8.json")
RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V8.md")
COORDINATOR_PATH = Path("scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV8.ps1")
V7_CONTRACT_PATH = Path(
    "control/armindex/a1.2/execution-contract.live-preflight-repair.v7.json"
)
V7_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-live-preflight-repair.receipt.v7.json"
)
V7_BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh")
V8_BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v8.sh")
CONTINUATION_POLICY_PATH = Path(
    "control/armindex/a1.2/owner-instance-continuation-policy.v1.json"
)

V2_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-vast-4x3090-migration.receipt.v2.json"
)
V3_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-vast-4x3090-postcommit-migration.receipt.v3.json"
)
V5_CONTRACT_PATH = Path("control/armindex/a1.2/execution-contract.direct-base.v5.json")
V5_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-runtime-minimal-direct-base-migration.receipt.v5.json"
)
REQUIRED_VALIDATOR_FILES = {
    Path("schemas/armindex/a1.2-vast-4x3090-preflight.v2.json"),
    Path("schemas/armindex/a1.2-vast-4x3090-postcommit.v3.json"),
    Path("schemas/armindex/a1.2-runtime-minimal-direct-base.v5.json"),
    V2_RECEIPT_PATH,
    V3_RECEIPT_PATH,
    V5_RECEIPT_PATH,
    RECEIPT_PATH,
}
BASE_PREFIXES = (
    "src/myis_research/",
    "control/armindex/a1.2/",
    "control/budgets/a1.2-common-screen-vast-4x3090-v2.json",
    "control/execution-envelope-a1.2-v2.yaml",
    "scripts/a1_2_vast/",
    "containers/a1_2_vast_4x3090/runtime/requirements.v2.txt",
    "pyproject.toml",
)
FORBIDDEN_PATH = re.compile(
    r"(^|/)(?:qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credentials?|"
    r"protected[_-]?evaluator|provider[_-]?payload)(?:[./_-]|$)|(^|/)\.env(?:\.|$)",
    re.IGNORECASE,
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_ID_RE = re.compile(r"^[a-f0-9]{40,64}$")


class PackagingRepairError(ValueError):
    """Raised when the v8 bundle cannot prove a safe validation closure."""


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PackagingRepairError(f"JSON object required: {path.as_posix()}")
    return value


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _binding_paths(payload: Mapping[str, Any]) -> set[Path]:
    paths: set[Path] = set()
    for field in ("bindings", "v1_preserved_bindings"):
        items = payload.get(field, [])
        if not isinstance(items, list):
            raise PackagingRepairError(f"{field} must be a list")
        for item in items:
            if not isinstance(item, Mapping) or not isinstance(item.get("uri"), str):
                raise PackagingRepairError(f"invalid {field} entry")
            paths.add(Path(str(item["uri"])))
    return paths


def validation_lineage_paths(repository_root: Path) -> set[Path]:
    """Return the exact historical files read by the remote v5 validator."""

    root = repository_root.resolve()
    paths = {Path(relative) for relative in V1_BINDINGS}
    paths.update(REQUIRED_VALIDATOR_FILES)
    for relative in (V2_RECEIPT_PATH, V3_RECEIPT_PATH, V5_CONTRACT_PATH):
        paths.update(_binding_paths(_load_json(root / relative)))
    return paths


def select_bundle_paths(repository_root: Path, tracked_paths: Sequence[str]) -> list[str]:
    root = repository_root.resolve()
    tracked = set(tracked_paths)
    selected = {
        path
        for path in tracked
        if any(path == prefix or path.startswith(prefix) for prefix in BASE_PREFIXES)
    }
    selected.update(path.as_posix() for path in validation_lineage_paths(root))
    selected.update(
        path.as_posix()
        for path in (
            CONTRACT_PATH,
            RECEIPT_PATH,
            SCHEMA_PATH,
            RUNBOOK_PATH,
            COORDINATOR_PATH,
            V7_CONTRACT_PATH,
            V7_RECEIPT_PATH,
            V7_BOOTSTRAP_PATH,
            V8_BOOTSTRAP_PATH,
            CONTINUATION_POLICY_PATH,
        )
    )
    missing = sorted(selected - tracked)
    if missing:
        raise PackagingRepairError(
            "validation-complete bundle references untracked files: " + ", ".join(missing)
        )
    for relative in selected:
        path = root / relative
        if FORBIDDEN_PATH.search(relative):
            raise PackagingRepairError(f"forbidden remote path: {relative}")
        if not path.is_file() or path.is_symlink():
            raise PackagingRepairError(f"bundle path must be a regular tracked file: {relative}")
    return sorted(selected)


def build_validation_complete_bundle(
    repository_root: Path, output_path: Path
) -> dict[str, Any]:
    root = repository_root.resolve()
    target = output_path.resolve()
    if target == root or root in target.parents:
        raise PackagingRepairError("v8 bundle output must stay outside the repository")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise PackagingRepairError("repository must be clean before v8 bundle creation")
    selected = select_bundle_paths(root, _git(root, "ls-files").splitlines())
    entries = [
        {
            "path": relative,
            "sha256": file_sha256(root / relative),
            "size_bytes": (root / relative).stat().st_size,
        }
        for relative in selected
    ]
    manifest: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-frozen-code-bundle.v8",
        "revision_id": REVISION_ID,
        "git_commit": _git(root, "rev-parse", "HEAD^{commit}"),
        "git_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "official_pytorch_image_digest": IMAGE_DIGEST,
        "files": entries,
        "file_count": len(entries),
        "model_bytes_included": False,
        "protected_data_included": False,
        "custom_local_docker_build_included": False,
        "historical_dockerfile_execution_allowed": False,
        "validation_lineage_complete": True,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    metadata = {
        "GIT_COMMIT": str(manifest["git_commit"]) + "\n",
        "GIT_TREE": str(manifest["git_tree"]) + "\n",
        "PYTORCH_IMAGE_DIGEST": IMAGE_DIGEST + "\n",
        "BUNDLE_MANIFEST.json": _json_text(manifest),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"v8 frozen bundle already exists: {target}")
    with target.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for relative in selected:
                    path = root / relative
                    info = tarfile.TarInfo(relative)
                    info.size = path.stat().st_size
                    info.mtime = 0
                    info.mode = 0o755 if relative == V8_BOOTSTRAP_PATH.as_posix() else 0o644
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
                for name, content in metadata.items():
                    data = content.encode("utf-8")
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mtime = 0
                    info.mode = 0o644
                    archive.addfile(info, BytesIO(data))
    return {
        "status": "PASS",
        "bundle_sha256": file_sha256(target),
        "bundle_bytes": target.stat().st_size,
        "file_count": len(entries),
        "manifest_sha256": manifest["manifest_sha256"],
        "git_commit": manifest["git_commit"],
        "git_tree": manifest["git_tree"],
        "validation_lineage_file_count": len(validation_lineage_paths(root)),
    }


def validate_remote_lineage(
    repository_root: Path, expected_commit: str, expected_tree: str
) -> dict[str, Any]:
    """Validate v1-v5 history in a frozen subset that intentionally has no .git."""

    root = repository_root.resolve()
    if not GIT_ID_RE.fullmatch(expected_commit) or not GIT_ID_RE.fullmatch(expected_tree):
        raise PackagingRepairError("expected frozen Git identity is invalid")
    manifest = _load_json(root / "BUNDLE_MANIFEST.json")
    body = dict(manifest)
    manifest_sha256 = body.pop("manifest_sha256", None)
    if manifest_sha256 != canonical_sha256(body):
        raise PackagingRepairError("v8 frozen bundle manifest self-hash mismatch")
    if (
        manifest.get("git_commit") != expected_commit
        or manifest.get("git_tree") != expected_tree
        or (root / "GIT_COMMIT").read_text(encoding="utf-8").strip() != expected_commit
        or (root / "GIT_TREE").read_text(encoding="utf-8").strip() != expected_tree
    ):
        raise PackagingRepairError("v8 frozen Git identity binding mismatch")

    v2 = validate_preparation_receipt(root)
    v3 = _load_json(root / V3_RECEIPT_PATH)
    v3_schema = _load_json(root / "schemas/armindex/a1.2-vast-4x3090-postcommit.v3.json")
    errors = sorted(
        Draft202012Validator(
            v3_schema, format_checker=Draft202012Validator.FORMAT_CHECKER
        ).iter_errors(v3),
        key=lambda error: list(error.path),
    )
    if errors:
        raise PackagingRepairError(f"v3 remote receipt schema failure: {errors[0].message}")
    v3_body = dict(v3)
    if v3_body.pop("receipt_sha256", None) != canonical_sha256(v3_body):
        raise PackagingRepairError("v3 remote receipt self-hash mismatch")
    for binding in v3.get("bindings", []):
        if file_sha256(root / str(binding["uri"])) != binding["sha256"]:
            raise PackagingRepairError(f"v3 remote binding mismatch: {binding['uri']}")
    if v3.get("v2_receipt_sha256") != v2.get("receipt_sha256"):
        raise PackagingRepairError("v3 remote lineage does not bind v2")
    v3_contract = _load_json(root / "control/armindex/a1.2/execution-contract.v3.json")
    if (
        v3_contract.get("launch_allowed") is not False
        or v3_contract.get("adopted_for_execution") is not False
        or any(v3_contract.get("real_counters", {}).values())
        or any(v3_contract.get("resource_counters", {}).values())
        or v3_contract.get("budget") != v3.get("budget")
    ):
        raise PackagingRepairError("v3 remote contract authority or budget mismatch")

    policy = _load_json(root / "control/armindex/a1.2/runtime-minimal-model-policy.v4.json")
    v5_contract = _load_json(root / V5_CONTRACT_PATH)
    v5_receipt = _load_json(root / V5_RECEIPT_PATH)
    v5_schema = _load_json(root / "schemas/armindex/a1.2-runtime-minimal-direct-base.v5.json")
    errors = sorted(
        Draft202012Validator(v5_schema).iter_errors(v5_receipt),
        key=lambda error: list(error.path),
    )
    if errors:
        raise PackagingRepairError(f"v5 remote receipt schema failure: {errors[0].message}")
    for payload, field in (
        (v5_contract, "contract_sha256"),
        (v5_receipt, "receipt_sha256"),
    ):
        payload_body = dict(payload)
        if payload_body.pop(field, None) != canonical_sha256(payload_body):
            raise PackagingRepairError(f"v5 remote {field} mismatch")
    for binding in v5_contract.get("bindings", []):
        if file_sha256(root / str(binding["uri"])) != binding["sha256"]:
            raise PackagingRepairError(f"v5 remote binding mismatch: {binding['uri']}")
    if (
        v5_receipt.get("contract_sha256") != file_sha256(root / V5_CONTRACT_PATH)
        or v5_receipt.get("policy_sha256")
        != file_sha256(root / "control/armindex/a1.2/runtime-minimal-model-policy.v4.json")
        or v5_contract.get("resolved_manifest_digest") != IMAGE_DIGEST
        or v5_contract.get("platform") != "linux/amd64"
        or policy.get("revision_id") != "a1.2-runtime-minimal-frozen-snapshot-v4"
    ):
        raise PackagingRepairError("v5 remote identity or lineage mismatch")
    for payload in (v5_contract, v5_receipt):
        if (
            payload.get("launch_allowed") is not False
            or payload.get("adopted_for_execution") is not False
            or any(float(value) != 0 for value in payload.get("resource_counters", {}).values())
            or any(int(value) != 0 for value in payload.get("real_counters", {}).values())
        ):
            raise PackagingRepairError("v5 remote authority or counters changed")
    return {
        "status": "PASS",
        "validation_mode": "frozen_bundle_metadata_no_git_directory",
        "git_commit": expected_commit,
        "git_tree": expected_tree,
        "v2_receipt_sha256": v2["receipt_sha256"],
        "v3_receipt_sha256": v3["receipt_sha256"],
        "v5_receipt_sha256": v5_receipt["receipt_sha256"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
    }


def _verification_marker_payload(
    expected_commit: str,
    expected_tree: str,
    expected_manifest_digest: str,
    expected_bundle_sha256: str,
) -> dict[str, Any]:
    if (
        not GIT_ID_RE.fullmatch(expected_commit)
        or not GIT_ID_RE.fullmatch(expected_tree)
        or expected_manifest_digest != IMAGE_DIGEST
        or not SHA256_RE.fullmatch(expected_bundle_sha256)
    ):
        raise PackagingRepairError("verification marker identity is invalid")
    payload: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-live-preflight-verification-marker.v8",
        "status": "PASS",
        "revision_id": REVISION_ID,
        "git_commit": expected_commit,
        "git_tree": expected_tree,
        "manifest_digest": expected_manifest_digest,
        "bundle_sha256": expected_bundle_sha256,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval": False,
        "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    payload["marker_sha256"] = canonical_sha256(payload)
    return payload


def write_verification_marker(
    marker_path: Path,
    expected_commit: str,
    expected_tree: str,
    expected_manifest_digest: str,
    expected_bundle_sha256: str,
) -> dict[str, Any]:
    marker = _verification_marker_payload(
        expected_commit,
        expected_tree,
        expected_manifest_digest,
        expected_bundle_sha256,
    )
    target = marker_path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_json_text(marker), encoding="utf-8", newline="")
    return marker


def validate_verification_marker(
    marker_path: Path,
    expected_commit: str,
    expected_tree: str,
    expected_manifest_digest: str,
    expected_bundle_sha256: str,
) -> dict[str, Any]:
    marker = _load_json(marker_path.resolve())
    body = dict(marker)
    marker_sha256 = body.pop("marker_sha256", None)
    if marker_sha256 != canonical_sha256(body):
        raise PackagingRepairError("verification marker self-hash mismatch")
    expected = {
        "schema_version": "myis.armindex-a1.2-live-preflight-verification-marker.v8",
        "status": "PASS",
        "revision_id": REVISION_ID,
        "git_commit": expected_commit,
        "git_tree": expected_tree,
        "manifest_digest": expected_manifest_digest,
        "bundle_sha256": expected_bundle_sha256,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval": False,
    }
    if any(marker.get(key) != value for key, value in expected.items()):
        raise PackagingRepairError("verification marker identity mismatch")
    return {
        "status": "PASS",
        "marker_sha256": marker_sha256,
        "git_commit": expected_commit,
        "git_tree": expected_tree,
        "bundle_sha256": expected_bundle_sha256,
    }
def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    body = dict(value)
    body[field] = canonical_sha256(body)
    return body


def materialize_revision(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_v7(root)
    bindings = [
        {"uri": path.as_posix(), "sha256": file_sha256(root / path)}
        for path in (
            V7_CONTRACT_PATH,
            V7_RECEIPT_PATH,
            CONTINUATION_POLICY_PATH,
            COORDINATOR_PATH,
            V7_BOOTSTRAP_PATH,
            V8_BOOTSTRAP_PATH,
            RUNBOOK_PATH,
            SCHEMA_PATH,
            Path("src/myis_research/armindex/a1_2_live_preflight_packaging_v8.py"),
        )
    ]
    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.live-preflight-packaging-repair.v8",
            "contract_id": REVISION_ID,
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "validation_complete_bundle_repair_prepared_preflight_pending",
            "evidence_class": "live_engineering_preflight_packaging_repair",
            "scientific_authority": False,
            "claim_boundary": "same-instance synthetic packaging repair only; no measured retrieval",
            "migration_from": {
                "uri": V7_RECEIPT_PATH.as_posix(),
                "sha256": file_sha256(root / V7_RECEIPT_PATH),
                "disposition": "preserved_immutable_failed_closed_v7",
            },
            "preserved_live_failures": [
                "v6-initial-wheelhouse-missing-pydantic",
                "v6-supplement-repair-mutated-pycache-tree",
                "v7-frozen-bundle-missing-validation-lineage",
            ],
            "active_correction": {
                "fresh_remote_root": "/opt/myis/a1.2-v8",
                "source_remote_root": "/opt/myis/a1.2-v7",
                "same_instance_reuse": True,
                "upload_only": ["validation_complete_frozen_code_bundle_v8"],
                "reuse_only_after_sha256_validation": [
                    "models",
                    "wheelhouse",
                    "jobs",
                    "supplement_wheelhouse_v7",
                ],
                "validation_lineage_complete": True,
                "historical_dockerfile_hash_only_nonexecuted": True,
                "pythondontwritebytecode": True,
            },
            "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
            "resolved_manifest_digest": IMAGE_DIGEST,
            "platform": "linux/amd64",
            "synthetic_preflight_only": True,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
            },
            "continuation_policy": {
                "uri": CONTINUATION_POLICY_PATH.as_posix(),
                "sha256": file_sha256(root / CONTINUATION_POLICY_PATH),
            },
            "bindings": bindings,
            "next_authorized_action": "Run only the v8 validation-complete same-instance synthetic preflight repair on a fresh remote root.",
        },
        "contract_sha256",
    )
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    contract_path = root / CONTRACT_PATH
    contract_path.write_text(_json_text(contract), encoding="utf-8", newline="")
    receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-live-preflight-packaging-repair.v8",
            "receipt_id": REVISION_ID,
            "revision_id": REVISION_ID,
            "status": contract["status"],
            "evidence_class": contract["evidence_class"],
            "scientific_authority": False,
            "claim_boundary": contract["claim_boundary"],
            "contract_sha256": file_sha256(contract_path),
            "v7_receipt_sha256": file_sha256(root / V7_RECEIPT_PATH),
            "preserved_live_failure_ids": contract["preserved_live_failures"],
            "new_remote_root": "/opt/myis/a1.2-v8",
            "validation_lineage_complete": True,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_runs": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "charged_usd": 0,
            "bindings": bindings,
        },
        "receipt_sha256",
    )
    receipt_path = root / RECEIPT_PATH
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return validate_revision(root)


def validate_revision(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_v7(root)
    contract = _load_json(root / CONTRACT_PATH)
    receipt = _load_json(root / RECEIPT_PATH)
    schema = _load_json(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise PackagingRepairError(f"v8 receipt schema failure: {errors[0].message}")
    for payload, field in ((contract, "contract_sha256"), (receipt, "receipt_sha256")):
        body = dict(payload)
        digest = body.pop(field, None)
        if digest != canonical_sha256(body):
            raise PackagingRepairError(f"v8 {field} mismatch")
    if receipt.get("contract_sha256") != file_sha256(root / CONTRACT_PATH):
        raise PackagingRepairError("v8 receipt does not bind the contract bytes")
    for binding in contract.get("bindings", []):
        if file_sha256(root / str(binding["uri"])) != binding["sha256"]:
            raise PackagingRepairError(f"v8 binding mismatch: {binding['uri']}")
    selected = select_bundle_paths(
        root,
        _git(root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines(),
    )
    if any(FORBIDDEN_PATH.search(path) for path in selected):
        raise PackagingRepairError("v8 selected an unsafe path")
    if (
        contract.get("launch_allowed") is not False
        or contract.get("adopted_for_execution") is not False
        or any(contract.get("real_counters", {}).values())
        or any(contract.get("resource_counters", {}).values())
    ):
        raise PackagingRepairError("v8 cannot authorize execution or change counters")
    return {
        "status": contract["status"],
        "revision_id": REVISION_ID,
        "contract_sha256": contract["contract_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "validation_lineage_file_count": len(validation_lineage_paths(root)),
        "selected_bundle_file_count": len(selected),
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight-packaging-v8")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("materialize")
    sub.add_parser("validate")
    remote = sub.add_parser("validate-remote-lineage")
    remote.add_argument("--expected-commit", required=True)
    remote.add_argument("--expected-tree", required=True)
    for command in ("write-verification-marker", "validate-verification-marker"):
        marker = sub.add_parser(command)
        marker.add_argument("--marker", type=Path, required=True)
        marker.add_argument("--expected-commit", required=True)
        marker.add_argument("--expected-tree", required=True)
        marker.add_argument("--expected-manifest-digest", required=True)
        marker.add_argument("--expected-bundle-sha256", required=True)
    build = sub.add_parser("build-bundle")
    build.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        payload = materialize_revision(args.repository_root)
    elif args.command == "validate":
        payload = validate_revision(args.repository_root)
    elif args.command == "validate-remote-lineage":
        payload = validate_remote_lineage(
            args.repository_root, args.expected_commit, args.expected_tree
        )
    elif args.command == "write-verification-marker":
        payload = write_verification_marker(
            args.marker,
            args.expected_commit,
            args.expected_tree,
            args.expected_manifest_digest,
            args.expected_bundle_sha256,
        )
    elif args.command == "validate-verification-marker":
        payload = validate_verification_marker(
            args.marker,
            args.expected_commit,
            args.expected_tree,
            args.expected_manifest_digest,
            args.expected_bundle_sha256,
        )
    else:
        payload = build_validation_complete_bundle(args.repository_root, args.output)
    print(_json_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
