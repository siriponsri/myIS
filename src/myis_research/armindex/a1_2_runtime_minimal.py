"""Additive A1.2 v4 runtime-minimal model staging controls.

This module stages only a frozen, explicit PyTorch execution allowlist.  It
never contacts a provider, starts CUDA work, loads dense weights, or opens a
protected repository surface.  Owner-local model bytes stay outside Git.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_vast import A12VastError, validate_v1_preserved
from .a1_2_vast_postcommit import validate_postcommit_revision


REVISION_ID = "a1.2-runtime-minimal-frozen-snapshot-v4"
POLICY_PATH = Path("control/armindex/a1.2/runtime-minimal-model-policy.v4.json")
BASE_IMAGE_PATH = Path("control/armindex/a1.2/vast-base-image-contract.v4.json")
CONTRACT_PATH = Path("control/armindex/a1.2/execution-contract.v4.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-runtime-minimal.v4.json")
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-runtime-minimal-migration.receipt.v4.json"
)
OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V4.md")
DENSE_ARMS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
OCI_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
_LOCAL_METADATA_FILES = {"SHA256SUMS", "runtime-file-manifest.v4.json"}


class RuntimeMinimalError(A12VastError):
    """Raised when the v4 minimal-runtime boundary cannot be proven."""


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeMinimalError(f"invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeMinimalError(f"JSON object required: {path}")
    return payload


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _git_blob_oid(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _model_lock(root: Path, arm_id: str) -> tuple[Path, dict[str, Any]]:
    path = root / "control/armindex/a1.2/model-locks" / f"{arm_id}.v1.json"
    return path, _load_json(path)


def load_runtime_policy(repository_root: Path) -> dict[str, Any]:
    """Load the tracked v4 policy and prove it binds each legacy source lock."""

    root = repository_root.resolve()
    policy = _load_json(root / POLICY_PATH)
    if policy.get("schema_version") != "myis.armindex-a1.2-runtime-minimal-policy.v4":
        raise RuntimeMinimalError("unexpected runtime-minimal policy schema")
    if policy.get("revision_id") != REVISION_ID:
        raise RuntimeMinimalError("runtime-minimal policy revision mismatch")
    arms = policy.get("arms")
    if not isinstance(arms, list) or tuple(item.get("arm_id") for item in arms) != DENSE_ARMS:
        raise RuntimeMinimalError("runtime-minimal policy must declare ARM-02 through ARM-05 once")
    for arm in arms:
        arm_id = arm["arm_id"]
        lock_path, lock = _model_lock(root, arm_id)
        if (
            arm.get("model_id") != lock.get("model_id")
            or arm.get("resolved_revision") != lock.get("resolved_revision")
            or arm.get("source_lock_file_sha256") != file_sha256(lock_path)
        ):
            raise RuntimeMinimalError(f"{arm_id} policy does not bind the source lock")
        allowlist = arm.get("allow_patterns")
        if not isinstance(allowlist, list) or allowlist != sorted(set(allowlist)):
            raise RuntimeMinimalError(f"{arm_id} allow_patterns must be sorted and unique")
        if any(not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts for path in allowlist):
            raise RuntimeMinimalError(f"{arm_id} has an unsafe allow pattern")
        if any(path.startswith("onnx/") or path.endswith((".onnx", ".onnx_data")) for path in allowlist):
            raise RuntimeMinimalError(f"{arm_id} allowlist includes an alternate runtime")
        expected_critical = {item["path"]: item["sha256"] for item in lock.get("critical_artifacts", [])}
        declared_critical = {item["path"]: item["sha256"] for item in arm.get("critical_artifacts", [])}
        if declared_critical != expected_critical or not set(expected_critical).issubset(allowlist):
            raise RuntimeMinimalError(f"{arm_id} critical artifact binding mismatch")
        for custom in lock.get("remote_code", []):
            path = custom["path"]
            declared = next((item for item in arm.get("required_custom_code", []) if item.get("path") == path), None)
            if path not in allowlist or declared is None or declared.get("git_oid") != custom["git_oid"]:
                raise RuntimeMinimalError(f"{arm_id} required custom code binding mismatch: {path}")
    return policy


def _arm_policy(policy: Mapping[str, Any], arm_id: str) -> Mapping[str, Any]:
    for arm in policy["arms"]:
        if arm["arm_id"] == arm_id:
            return arm
    raise RuntimeMinimalError(f"unrecognized dense arm: {arm_id}")


def _allowed_files(arm: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(path) for path in arm["allow_patterns"])


def _permitted_nonruntime_path(relative: str, arm: Mapping[str, Any]) -> bool:
    if relative in _LOCAL_METADATA_FILES or relative.startswith(".cache/huggingface/"):
        return True
    if relative.endswith(".part"):
        completed = relative.removesuffix(".part")
        return any(item.get("path") == completed for item in arm.get("excluded_files", []))
    return False


def _iter_files(directory: Path) -> list[str]:
    return sorted(
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    )


def _sha256_sums_text(directory: Path, paths: Sequence[str]) -> str:
    return "".join(f"{file_sha256(directory / relative)}  {relative}\n" for relative in sorted(paths))


def _validate_sha256sums(directory: Path, expected_paths: Sequence[str]) -> dict[str, str]:
    path = directory / "SHA256SUMS"
    if not path.is_file():
        raise RuntimeMinimalError("SHA256SUMS is missing")
    entries: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([a-f0-9]{64})  ([^\r\n]+)", line)
        if match is None:
            raise RuntimeMinimalError(f"malformed SHA256SUMS line {number}")
        digest, relative = match.groups()
        if relative in entries or relative not in expected_paths:
            raise RuntimeMinimalError(f"unexpected SHA256SUMS path: {relative}")
        entries[relative] = digest
    if tuple(sorted(entries)) != tuple(sorted(expected_paths)):
        raise RuntimeMinimalError("SHA256SUMS does not cover exactly the runtime allowlist")
    for relative, expected in entries.items():
        if file_sha256(directory / relative) != expected:
            raise RuntimeMinimalError(f"SHA256SUMS byte mismatch: {relative}")
    return entries


def write_runtime_manifest(repository_root: Path, arm_id: str, model_directory: Path) -> dict[str, Any]:
    """Stream-hash an exactly staged runtime allowlist and write its two receipts."""

    root = repository_root.resolve()
    policy = load_runtime_policy(root)
    arm = _arm_policy(policy, arm_id)
    directory = model_directory.resolve()
    allowed = _allowed_files(arm)
    if not directory.is_dir():
        raise RuntimeMinimalError(f"model directory is missing: {directory}")
    present = set(_iter_files(directory))
    missing = sorted(set(allowed) - present)
    if missing:
        raise RuntimeMinimalError(f"runtime allowlist files are incomplete: {', '.join(missing)}")
    unexpected = sorted(
        relative
        for relative in present - set(allowed)
        if not _permitted_nonruntime_path(relative, arm)
    )
    if unexpected:
        raise RuntimeMinimalError(f"unexpected local model files: {', '.join(unexpected)}")

    sums = _sha256_sums_text(directory, allowed)
    (directory / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="")
    entries = _validate_sha256sums(directory, allowed)
    lock_path, lock = _model_lock(root, arm_id)
    critical = {item["path"]: item["sha256"] for item in arm["critical_artifacts"]}
    for relative, expected in critical.items():
        if entries[relative] != expected:
            raise RuntimeMinimalError(f"critical artifact SHA-256 mismatch: {relative}")

    remote_code: list[dict[str, str]] = []
    for item in arm.get("required_custom_code", []):
        relative = str(item["path"])
        actual_oid = _git_blob_oid(directory / relative)
        if actual_oid != item["git_oid"]:
            raise RuntimeMinimalError(f"required custom code Git OID mismatch: {relative}")
        remote_code.append(
            {"path": relative, "git_oid": actual_oid, "sha256": entries[relative]}
        )
    runtime_bytes = sum((directory / relative).stat().st_size for relative in allowed)
    full_snapshot_bytes = int(arm["upstream_full_snapshot_bytes"])
    if runtime_bytes != int(arm["runtime_minimal_expected_bytes"]):
        raise RuntimeMinimalError(f"runtime-minimal byte total drifted for {arm_id}")
    manifest: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-runtime-file-manifest.v4",
        "revision_id": REVISION_ID,
        "arm_id": arm_id,
        "model_id": arm["model_id"],
        "resolved_revision": arm["resolved_revision"],
        "allowlist_version": policy["allowlist_version"],
        "source_lock_uri": lock_path.relative_to(root).as_posix(),
        "source_lock_file_sha256": file_sha256(lock_path),
        "source_lock_declared_sha256": lock["lock_sha256"],
        "policy_uri": POLICY_PATH.as_posix(),
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "exclusion_policy": policy["exclusion_policy"],
        "files": [
            {"path": relative, "size_bytes": (directory / relative).stat().st_size, "sha256": entries[relative]}
            for relative in sorted(allowed)
        ],
        "file_count": len(allowed),
        "runtime_minimal_bytes": runtime_bytes,
        "upstream_full_snapshot_bytes": full_snapshot_bytes,
        "full_snapshot_bytes_avoided": full_snapshot_bytes - runtime_bytes,
        "critical_artifact_hashes": [
            {"path": relative, "sha256": entries[relative]} for relative in sorted(critical)
        ],
        "required_custom_code": remote_code,
        "preserved_nonruntime_local_paths": sorted(
            path
            for path in present - set(allowed)
            if path not in _LOCAL_METADATA_FILES and _permitted_nonruntime_path(path, arm)
        ),
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    (directory / "runtime-file-manifest.v4.json").write_text(
        _json_text(manifest), encoding="utf-8", newline=""
    )
    return manifest


def validate_runtime_manifest(repository_root: Path, arm_id: str, model_directory: Path) -> dict[str, Any]:
    """Validate staged bytes without loading a dense model or allowing a network fallback."""

    root = repository_root.resolve()
    policy = load_runtime_policy(root)
    arm = _arm_policy(policy, arm_id)
    directory = model_directory.resolve()
    manifest = _load_json(directory / "runtime-file-manifest.v4.json")
    body = dict(manifest)
    recorded_manifest_hash = body.pop("manifest_sha256", None)
    if recorded_manifest_hash != canonical_sha256(body):
        raise RuntimeMinimalError("runtime-file manifest self-hash mismatch")
    allowed = _allowed_files(arm)
    if (
        manifest.get("arm_id") != arm_id
        or manifest.get("model_id") != arm["model_id"]
        or manifest.get("resolved_revision") != arm["resolved_revision"]
        or manifest.get("allowlist_version") != policy["allowlist_version"]
        or manifest.get("source_lock_file_sha256") != arm["source_lock_file_sha256"]
    ):
        raise RuntimeMinimalError("runtime-file manifest model/revision/lock binding mismatch")
    entries = _validate_sha256sums(directory, allowed)
    listed = manifest.get("files")
    expected_listed = [
        {"path": relative, "size_bytes": (directory / relative).stat().st_size, "sha256": entries[relative]}
        for relative in sorted(allowed)
    ]
    if listed != expected_listed:
        raise RuntimeMinimalError("runtime-file manifest files are not deterministic")
    expected_critical = {item["path"]: item["sha256"] for item in arm["critical_artifacts"]}
    if any(entries[path] != digest for path, digest in expected_critical.items()):
        raise RuntimeMinimalError("critical artifact hash mismatch")
    expected_custom = {item["path"]: item["git_oid"] for item in arm.get("required_custom_code", [])}
    for relative, git_oid in expected_custom.items():
        if _git_blob_oid(directory / relative) != git_oid:
            raise RuntimeMinimalError(f"custom code Git OID mismatch: {relative}")
    for relative in _iter_files(directory):
        if relative in allowed or _permitted_nonruntime_path(relative, arm):
            continue
        raise RuntimeMinimalError(f"forbidden non-runtime file in staged directory: {relative}")
    return {
        "status": "PASS",
        "arm_id": arm_id,
        "file_count": len(allowed),
        "runtime_minimal_bytes": manifest["runtime_minimal_bytes"],
        "full_snapshot_bytes_avoided": manifest["full_snapshot_bytes_avoided"],
        "manifest_sha256": manifest["manifest_sha256"],
        "sha256sums_sha256": file_sha256(directory / "SHA256SUMS"),
        "no_network_fallback": True,
        "dense_model_loaded": False,
    }


def stage_runtime_snapshot(repository_root: Path, arm_id: str, model_directory: Path) -> dict[str, Any]:
    """Download exactly the frozen allowlist, sequentially, and resume local bytes."""

    root = repository_root.resolve()
    policy = load_runtime_policy(root)
    arm = _arm_policy(policy, arm_id)
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeMinimalError(
            "BLOCKED_MISSING_HUGGINGFACE_HUB: run through the pinned Owner command in the v4 runbook"
        ) from exc
    directory = model_directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=arm["model_id"],
        revision=arm["resolved_revision"],
        allow_patterns=list(_allowed_files(arm)),
        local_dir=directory,
        local_dir_use_symlinks=False,
        max_workers=1,
    )
    manifest = write_runtime_manifest(root, arm_id, directory)
    return {
        "status": "validated",
        "arm_id": arm_id,
        "model_id": arm["model_id"],
        "resolved_revision": arm["resolved_revision"],
        "allow_patterns": list(_allowed_files(arm)),
        **validate_runtime_manifest(root, arm_id, directory),
        "manifest": manifest,
    }


def validate_offline_runtime_settings(settings: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed unless the staged runtime has no HTTP fallback path."""

    required = {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "local_files_only": True,
        "network_model_download_allowed": False,
    }
    if dict(settings) != required:
        raise RuntimeMinimalError("runtime offline settings are incomplete or allow a network fallback")
    return {"status": "PASS", "network_fallback": False, "settings": required}


def build_frozen_code_bundle(repository_root: Path, output_path: Path) -> dict[str, Any]:
    """Build a deterministic code-only transfer archive; model bytes are never in it."""

    root = repository_root.resolve()
    target = output_path.resolve()
    if target == root or root in target.parents:
        raise RuntimeMinimalError("frozen code bundle must be outside the repository")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeMinimalError("repository must be clean before frozen code bundle creation")
    base = _load_json(root / BASE_IMAGE_PATH)
    digest = base.get("image", {}).get("digest")
    if not isinstance(digest, str) or not OCI_RE.fullmatch(digest):
        raise RuntimeMinimalError("v4 requires a resolved official PyTorch image digest")
    prefixes = (
        "src/myis_research/",
        "control/armindex/a1.2/",
        "control/budgets/a1.2-common-screen-vast-4x3090-v2.json",
        "control/execution-envelope-a1.2-v2.yaml",
        "scripts/a1_2_vast/",
        "containers/a1_2_vast_4x3090/runtime/requirements.v2.txt",
        "pyproject.toml",
    )
    selected = sorted(
        path
        for path in _git(root, "ls-files").splitlines()
        if any(path == prefix or path.startswith(prefix) for prefix in prefixes)
        and "Dockerfile" not in path
    )
    if not selected:
        raise RuntimeMinimalError("v4 code bundle selected no files")
    forbidden = ("qrels", "membership", "query_ids", "id_rsa", "id_ed25519", "credential")
    if any(any(fragment in Path(path).name.lower() for fragment in forbidden) for path in selected):
        raise RuntimeMinimalError("v4 code bundle included a protected or credential-like file")
    entries = [
        {"path": relative, "sha256": file_sha256(root / relative), "size_bytes": (root / relative).stat().st_size}
        for relative in selected
    ]
    manifest: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-frozen-code-bundle.v4",
        "revision_id": REVISION_ID,
        "git_commit": _git(root, "rev-parse", "HEAD^{commit}"),
        "git_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "official_pytorch_image_digest": digest,
        "files": entries,
        "file_count": len(entries),
        "model_bytes_included": False,
        "custom_local_docker_build_included": False,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    metadata = {
        "GIT_COMMIT": manifest["git_commit"] + "\n",
        "GIT_TREE": manifest["git_tree"] + "\n",
        "PYTORCH_IMAGE_DIGEST": digest + "\n",
        "BUNDLE_MANIFEST.json": _json_text(manifest),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"frozen code bundle already exists: {target}")
    with target.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for relative in selected:
                    path = root / relative
                    info = tarfile.TarInfo(relative)
                    info.size = path.stat().st_size
                    info.mtime = 0
                    info.mode = 0o755 if path.suffix == ".sh" else 0o644
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
        "official_pytorch_image_digest": digest,
    }


def validate_v4_revision(repository_root: Path) -> dict[str, Any]:
    """Validate the additive contract and receipt, while proving v1-v3 remain intact."""

    root = repository_root.resolve()
    validate_v1_preserved(root)
    v3 = validate_postcommit_revision(root, require_clean=False)
    policy = load_runtime_policy(root)
    base = _load_json(root / BASE_IMAGE_PATH)
    contract = _load_json(root / CONTRACT_PATH)
    receipt = _load_json(root / RECEIPT_PATH)
    schema = _load_json(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise RuntimeMinimalError(f"v4 receipt schema failure: {errors[0].message}")
    for item, field in ((contract, "contract_sha256"), (receipt, "receipt_sha256")):
        body = dict(item)
        recorded = body.pop(field, None)
        if recorded != canonical_sha256(body):
            raise RuntimeMinimalError(f"v4 {field} mismatch")
    for binding in contract.get("bindings", []):
        if file_sha256(root / binding["uri"]) != binding["sha256"]:
            raise RuntimeMinimalError(f"v4 contract binding mismatch: {binding['uri']}")
    if receipt.get("contract_sha256") != file_sha256(root / CONTRACT_PATH):
        raise RuntimeMinimalError("v4 receipt does not bind the v4 contract bytes")
    if receipt.get("policy_sha256") != file_sha256(root / POLICY_PATH):
        raise RuntimeMinimalError("v4 receipt does not bind the runtime policy bytes")
    if receipt.get("v3_receipt_sha256") != v3["v2_receipt_sha256"] and receipt.get("v3_receipt_sha256") != _load_json(root / "campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-postcommit-migration.receipt.v3.json")["receipt_sha256"]:
        raise RuntimeMinimalError("v4 receipt does not preserve the v3 receipt lineage")
    if base.get("image", {}).get("repository") != "pytorch/pytorch" or not OCI_RE.fullmatch(str(base.get("image", {}).get("digest", ""))):
        raise RuntimeMinimalError("v4 base image is not an immutable official PyTorch digest")
    for payload in (contract, receipt):
        if payload.get("launch_allowed") is not False or payload.get("adopted_for_execution") is not False:
            raise RuntimeMinimalError("v4 cannot authorize launch or adoption")
        if any(float(value) != 0 for value in payload.get("resource_counters", {}).values()) or any(int(value) != 0 for value in payload.get("real_counters", {}).values()):
            raise RuntimeMinimalError("v4 counters must remain zero")
    return {
        "status": "runtime_minimal_prepared_launch_locked",
        "revision_id": REVISION_ID,
        "policy_sha256": file_sha256(root / POLICY_PATH),
        "base_image_digest": base["image"]["digest"],
        "runtime_minimal_expected_bytes": sum(int(arm["runtime_minimal_expected_bytes"]) for arm in policy["arms"]),
        "full_snapshot_expected_bytes": sum(int(arm["upstream_full_snapshot_bytes"]) for arm in policy["arms"]),
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-runtime-minimal")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "validate-manifest"):
        item = sub.add_parser(command)
        item.add_argument("--repository-root", type=Path, default=Path.cwd())
        item.add_argument("--arm", choices=DENSE_ARMS, required=True)
        item.add_argument("--model-directory", type=Path, required=True)
    bundle = sub.add_parser("build-code-bundle")
    bundle.add_argument("--repository-root", type=Path, default=Path.cwd())
    bundle.add_argument("--output", type=Path, required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "stage":
        payload = stage_runtime_snapshot(args.repository_root, args.arm, args.model_directory)
    elif args.command == "validate-manifest":
        payload = validate_runtime_manifest(args.repository_root, args.arm, args.model_directory)
    elif args.command == "build-code-bundle":
        payload = build_frozen_code_bundle(args.repository_root, args.output)
    else:
        payload = validate_v4_revision(args.repository_root)
    print(_json_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
