"""Build and validate hash-only CPU-local A2 deployment packages."""

from __future__ import annotations

import gzip
import json
import os
import re
import tarfile
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a2_execution_readiness import validate_execution_bundle

_ARMS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^a2-[a-z0-9-]{7,63}$")
_PROTECTED_NAME = re.compile(
    r"(?:qrels|membership|query[_-]?ids?|credential|secret|provider[_-]?payload|"
    r"protected[_-]?(?:input|data|membership))",
    re.IGNORECASE,
)
_DESTROYED_INSTANCE_ID = "47411176"
_MANIFEST_NAME = "A2_DEPLOYMENT_MANIFEST.json"


class A2DeploymentPackageError(ValueError):
    """Raised when a deployment source or package fails closed."""


@dataclass(frozen=True)
class A2DeploymentAssets:
    """Explicit safe roots and files used to bind an A2 deployment package."""

    model_roots: Mapping[str, Path]
    wheelhouse_root: Path
    a1_baseline_root: Path
    a1_journal_root: Path
    a1_closeout_root: Path
    runtime_identity_path: Path
    frozen_a1_bundle_path: Path
    frozen_a1_bundle_receipt_path: Path
    a2_bundle_path: Path
    a2_bundle_receipt_path: Path


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise A2DeploymentPackageError(f"{role} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2DeploymentPackageError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A2DeploymentPackageError(f"{role} must be a JSON object")
    return value


def _require_safe_file(path: Path, *, role: str, root: Path | None = None) -> Path:
    absolute = path.absolute()
    boundary = root.absolute() if root is not None else absolute.parent
    cursor = absolute
    while True:
        if cursor.is_symlink():
            raise A2DeploymentPackageError(f"{role} is missing or unsafe")
        if cursor == boundary:
            break
        if cursor.parent == cursor:
            raise A2DeploymentPackageError(f"{role} escapes its declared root")
        cursor = cursor.parent
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as error:
        raise A2DeploymentPackageError(f"{role} is missing or unsafe") from error
    if not resolved.is_file():
        raise A2DeploymentPackageError(f"{role} is missing or unsafe")
    if root is not None and not resolved.is_relative_to(root):
        raise A2DeploymentPackageError(f"{role} escapes its declared root")
    return resolved


def _require_safe_root(path: Path, *, role: str, repository_root: Path) -> Path:
    if path.is_symlink():
        raise A2DeploymentPackageError(f"{role} is missing or unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise A2DeploymentPackageError(f"{role} is missing or unsafe") from error
    if not resolved.is_dir() or resolved.is_relative_to(repository_root):
        raise A2DeploymentPackageError(f"{role} is missing or unsafe")
    return resolved


def _safe_relative(value: object, *, role: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise A2DeploymentPackageError(f"{role} path is invalid")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or _PROTECTED_NAME.search(value):
        raise A2DeploymentPackageError(f"{role} path crosses the protected boundary")
    return path.as_posix()


def _parse_sha256sums(path: Path, *, role: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise A2DeploymentPackageError(f"{role} SHA256SUMS is invalid") from error
    for line in lines:
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-f0-9]{64})  (.+)", line)
        if match is None:
            raise A2DeploymentPackageError(f"{role} SHA256SUMS is invalid")
        relative = _safe_relative(match.group(2), role=role)
        if relative in rows:
            raise A2DeploymentPackageError(f"{role} SHA256SUMS has duplicate paths")
        rows[relative] = match.group(1)
    return rows


def _validate_model_root(root: Path, *, arm_id: str) -> dict[str, Any]:
    manifest_path = _require_safe_file(
        root / "runtime-file-manifest.v4.json", role=f"{arm_id} model manifest", root=root
    )
    sums_path = _require_safe_file(root / "SHA256SUMS", role=f"{arm_id} SHA256SUMS", root=root)
    manifest = _load_json(manifest_path, role=f"{arm_id} model manifest")
    if (
        manifest.get("arm_id") != arm_id
        or manifest.get("file_count") != 12
        or manifest.get("manifest_sha256")
        != canonical_sha256({key: value for key, value in manifest.items() if key != "manifest_sha256"})
    ):
        raise A2DeploymentPackageError(f"{arm_id} model manifest identity drift")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 12:
        raise A2DeploymentPackageError(f"{arm_id} model manifest must declare 12 files")
    sums = _parse_sha256sums(sums_path, role=f"{arm_id} model")
    declared: dict[str, tuple[str, int]] = {}
    for row in files:
        if not isinstance(row, Mapping):
            raise A2DeploymentPackageError(f"{arm_id} model manifest row is invalid")
        relative = _safe_relative(row.get("path"), role=f"{arm_id} model")
        sha256 = row.get("sha256")
        size = row.get("size_bytes")
        if not isinstance(sha256, str) or _HASH.fullmatch(sha256) is None or not isinstance(size, int):
            raise A2DeploymentPackageError(f"{arm_id} model manifest row is invalid")
        if relative in declared:
            raise A2DeploymentPackageError(f"{arm_id} model manifest has duplicate paths")
        declared[relative] = (sha256, size)
    if len(sums) != 12 or {key: value[0] for key, value in declared.items()} != sums:
        raise A2DeploymentPackageError(f"{arm_id} model SHA256SUMS differs from its manifest")
    verified: list[dict[str, Any]] = []
    for relative, (sha256, size) in sorted(declared.items()):
        member = _require_safe_file(root / relative, role=f"{arm_id} model member", root=root)
        if member.stat().st_size != size or file_sha256(member) != sha256:
            raise A2DeploymentPackageError(f"{arm_id} model member hash drift")
        verified.append({"path": relative, "sha256": sha256, "size_bytes": size})
    return {
        "arm_id": arm_id,
        "asset_uri": f"owner-store://a1.2/models/{arm_id}",
        "file_count": 12,
        "manifest_file_sha256": file_sha256(manifest_path),
        "manifest_sha256": manifest["manifest_sha256"],
        "sha256sums_sha256": file_sha256(sums_path),
        "file_set_sha256": canonical_sha256(verified),
    }


def _validate_wheelhouse(root: Path) -> dict[str, Any]:
    sums_path = _require_safe_file(root / "SHA256SUMS", role="wheelhouse SHA256SUMS", root=root)
    sidecar_path = _require_safe_file(
        root / "WHEELHOUSE_VALIDATION.json", role="wheelhouse validation sidecar", root=root
    )
    sums = _parse_sha256sums(sums_path, role="wheelhouse")
    if len(sums) != 14:
        raise A2DeploymentPackageError("wheelhouse must declare exactly 14 files")
    verified: list[dict[str, Any]] = []
    for relative, sha256 in sorted(sums.items()):
        member = _require_safe_file(root / relative, role="wheelhouse member", root=root)
        if file_sha256(member) != sha256:
            raise A2DeploymentPackageError("wheelhouse member hash drift")
        verified.append(
            {"path": relative, "sha256": sha256, "size_bytes": member.stat().st_size}
        )
    sidecar = _load_json(sidecar_path, role="wheelhouse validation sidecar")
    if (
        sidecar.get("status") != "PASS"
        or sidecar.get("offline_install") != "PASS"
        or sidecar.get("contains_models_or_protected_data") is not False
        or sidecar.get("platform") != "linux/amd64"
        or sidecar.get("python") != "3.11"
        or sidecar.get("wheel_count") != 13
        or sidecar.get("sha256sums_sha256") != file_sha256(sums_path)
    ):
        raise A2DeploymentPackageError("wheelhouse validation sidecar drift")
    return {
        "asset_uri": "owner-store://a1.2/runtime/wheelhouse",
        "declared_file_count": 14,
        "wheel_count": 13,
        "sha256sums_sha256": file_sha256(sums_path),
        "validation_sidecar_sha256": file_sha256(sidecar_path),
        "file_set_sha256": canonical_sha256(verified),
    }


def _validate_handoff(
    root: Path,
    *,
    role: str,
    manifest_name: str,
    expected_count: int,
    attempt_id: str = "a12-v16-20260811-r15",
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = _require_safe_file(root / manifest_name, role=f"{role} manifest", root=root)
    manifest = _load_json(manifest_path, role=f"{role} manifest")
    expected_schema = {
        "a1_baseline": "myis.armindex-a1.2-a2-baseline-handoff.v16",
        "a1_journal": "myis.armindex-a1.2-journal-eda-handoff.v16",
        "a1_closeout": "myis.armindex-a1.2-remote-closeout-mirror.v16",
    }[role]
    if (
        manifest.get("schema_version") != expected_schema
        or manifest.get("status") != "PASS"
        or manifest.get("attempt_id") != attempt_id
    ):
        raise A2DeploymentPackageError(f"{role} manifest identity drift")
    if role == "a1_baseline" and manifest.get("handoff_id") != (
        f"{attempt_id}-a2-baseline-handoff-v16"
    ):
        raise A2DeploymentPackageError("a1_baseline manifest identity drift")
    if role != "a1_baseline" and manifest.get("aggregate_safe") is not True:
        raise A2DeploymentPackageError(f"{role} manifest is not aggregate-safe")
    count_key = "copied_file_count" if role == "a1_baseline" else "file_count"
    rows_key = "copied_files" if role == "a1_baseline" else "files"
    rows = manifest.get(rows_key)
    if manifest.get(count_key) != expected_count or not isinstance(rows, list) or len(rows) != expected_count:
        raise A2DeploymentPackageError(f"{role} manifest count drift")
    if manifest.get("manifest_sha256") != canonical_sha256(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    ):
        raise A2DeploymentPackageError(f"{role} manifest self-hash drift")
    verified: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise A2DeploymentPackageError(f"{role} manifest row is invalid")
        path_value = row.get("relative_path") if role == "a1_baseline" else row.get("file_name")
        relative = _safe_relative(path_value, role=role)
        sha256 = row.get("sha256")
        size = row.get("size_bytes")
        if not isinstance(sha256, str) or _HASH.fullmatch(sha256) is None or not isinstance(size, int):
            raise A2DeploymentPackageError(f"{role} manifest row is invalid")
        member = _require_safe_file(root / relative, role=f"{role} member", root=root)
        if member.stat().st_size != size or file_sha256(member) != sha256:
            raise A2DeploymentPackageError(f"{role} member hash drift")
        verified.append({"path": relative, "sha256": sha256, "size_bytes": size})
    if len({row["path"] for row in verified}) != expected_count:
        raise A2DeploymentPackageError(f"{role} manifest has duplicate paths")
    return (
        {
            "asset_uri": f"owner-store://a1.2/handoffs/{role.replace('a1_', '')}",
            "source_file_count": expected_count,
            "manifest_file_sha256": file_sha256(manifest_path),
            "manifest_sha256": manifest["manifest_sha256"],
            "file_set_sha256": canonical_sha256(sorted(verified, key=lambda row: row["path"])),
        },
        manifest,
    )


def _validate_runtime_identity(path: Path) -> dict[str, Any]:
    value = _load_json(path, role="A1 runtime identity")
    schema = _load_json(
        Path(__file__).resolve().parents[3]
        / "schemas/armindex/a1.2-live-ssh-runtime-receipt.v16.json",
        role="A1 runtime identity schema",
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2DeploymentPackageError(
            f"A1 runtime identity schema drift: {errors[0].message}"
        )
    if value.get("receipt_sha256") != canonical_sha256(
        {key: item for key, item in value.items() if key != "receipt_sha256"}
    ):
        raise A2DeploymentPackageError("A1 runtime identity self-hash drift")
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True)
    runtime = value.get("runtime")
    if (
        _DESTROYED_INSTANCE_ID in encoded
        or value.get("status") != "PASS_SSH_RUNTIME"
        or not isinstance(runtime, Mapping)
        or runtime.get("platform") != "linux/amd64"
        or runtime.get("python") != "3.11"
        or runtime.get("gpu_count") != 4
        or runtime.get("vram_mib_each") != 24576
        or runtime.get("torch") != "2.6.0+cu118"
        or runtime.get("cuda") != "11.8"
        or runtime.get("gpu_model") != "NVIDIA GeForce RTX 3090"
        or not isinstance(value.get("provider_identity_receipt_sha256"), str)
        or not isinstance(value.get("ssh_runtime_input_sha256"), str)
    ):
        raise A2DeploymentPackageError("A1 runtime identity drift or old instance binding")
    return {
        "asset_uri": "owner-store://a1.2/runtime/ssh-runtime-receipt",
        "file_sha256": file_sha256(path),
        "runtime_receipt_sha256": value.get("receipt_sha256"),
        "platform": "linux/amd64",
        "python": "3.11",
        "torch": "2.6.0+cu118",
        "cuda": "11.8",
        "gpu_count": 4,
        "vram_mib_each": 24576,
    }


def _validate_frozen_a1_bundle(bundle_path: Path, receipt_path: Path) -> dict[str, Any]:
    bundle = _require_safe_file(bundle_path, role="frozen A1 bundle")
    receipt = _load_json(receipt_path, role="frozen A1 bundle receipt")
    if (
        receipt.get("status") != "ENGINEERING_BUNDLE_BUILT_NOT_ADOPTED"
        or receipt.get("clean_worktree") is not True
        or receipt.get("pushed_to_origin_main") is not True
        or receipt.get("frozen_bundle_sha256") != file_sha256(bundle)
        or receipt.get("receipt_sha256")
        != canonical_sha256({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    ):
        raise A2DeploymentPackageError("frozen A1 bundle receipt drift")
    return {
        "asset_uri": "owner-store://a1.2/bundles/frozen-v16",
        "bundle_sha256": receipt["frozen_bundle_sha256"],
        "bundle_size_bytes": bundle.stat().st_size,
        "receipt_file_sha256": file_sha256(receipt_path),
        "receipt_sha256": receipt["receipt_sha256"],
    }


def _validate_a2_bundle(
    repository_root: Path, bundle_path: Path, receipt_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = _load_json(receipt_path, role="A2 bundle receipt")
    if _DESTROYED_INSTANCE_ID in json.dumps(receipt, ensure_ascii=True, sort_keys=True):
        raise A2DeploymentPackageError("A2 bundle receipt binds the destroyed instance")
    try:
        validated = validate_execution_bundle(
            repository_root, bundle_path=bundle_path, receipt=receipt
        )
    except (OSError, ValueError) as error:
        raise A2DeploymentPackageError("A2 execution bundle is invalid") from error
    return (
        {
            "asset_uri": "owner-store://armindex-a2/bundles/current-pushed-head",
            "bundle_sha256": validated["bundle_sha256"],
            "bundle_size_bytes": bundle_path.stat().st_size,
            "bundle_manifest_sha256": validated["bundle_manifest_sha256"],
            "receipt_file_sha256": file_sha256(receipt_path),
            "receipt_sha256": validated["receipt_sha256"],
            "git_commit": validated["git_commit"],
            "git_tree": validated["git_tree"],
        },
        validated,
    )


def validate_deployment_assets(
    repository_root: Path, *, assets: A2DeploymentAssets
) -> dict[str, Any]:
    """Validate only explicitly declared Owner-local assets and return hash bindings."""

    repository = repository_root.resolve(strict=True)
    if set(assets.model_roots) != set(_ARMS):
        raise A2DeploymentPackageError("model roots must cover ARM-02 through ARM-05")
    model_rows = []
    for arm_id in _ARMS:
        model_root = _require_safe_root(
            assets.model_roots[arm_id], role=f"{arm_id} model root", repository_root=repository
        )
        model_rows.append(_validate_model_root(model_root, arm_id=arm_id))
    wheelhouse = _validate_wheelhouse(
        _require_safe_root(
            assets.wheelhouse_root, role="wheelhouse root", repository_root=repository
        )
    )
    baseline_root = _require_safe_root(
        assets.a1_baseline_root, role="A1 baseline handoff root", repository_root=repository
    )
    baseline, baseline_manifest = _validate_handoff(
        baseline_root,
        role="a1_baseline",
        manifest_name="handoff-manifest.v16.json",
        expected_count=28,
    )
    if baseline_manifest.get("a2_execution_authorized") is not False:
        raise A2DeploymentPackageError("A1 baseline handoff cannot authorize A2")
    journal, _ = _validate_handoff(
        _require_safe_root(
            assets.a1_journal_root, role="A1 journal handoff root", repository_root=repository
        ),
        role="a1_journal",
        manifest_name="handoff-manifest.v16.json",
        expected_count=7,
    )
    closeout, _ = _validate_handoff(
        _require_safe_root(
            assets.a1_closeout_root, role="A1 closeout handoff root", repository_root=repository
        ),
        role="a1_closeout",
        manifest_name="mirror-manifest.v16.json",
        expected_count=11,
    )
    safe_return = _require_safe_file(
        baseline_root / "safe-return" / "safe-return.tar.gz",
        role="A1 safe-return archive",
        root=baseline_root,
    )
    if baseline_manifest.get("safe_return_archive_sha256") != file_sha256(safe_return):
        raise A2DeploymentPackageError("A1 safe-return archive binding drift")
    runtime_identity = _validate_runtime_identity(
        _require_safe_file(assets.runtime_identity_path, role="A1 runtime identity")
    )
    frozen_a1 = _validate_frozen_a1_bundle(
        assets.frozen_a1_bundle_path, assets.frozen_a1_bundle_receipt_path
    )
    a2_bundle, a2_receipt = _validate_a2_bundle(
        repository, assets.a2_bundle_path, assets.a2_bundle_receipt_path
    )
    return {
        "models": model_rows,
        "wheelhouse": wheelhouse,
        "a1_safe_return": {
            "asset_uri": "owner-store://armindex-a2/a1-baseline/safe-return.tar.gz",
            "archive_sha256": file_sha256(safe_return),
            "archive_size_bytes": safe_return.stat().st_size,
        },
        "a1_handoffs": {
            "baseline": baseline,
            "journal": journal,
            "closeout": closeout,
        },
        "runtime_identity": runtime_identity,
        "frozen_a1_bundle": frozen_a1,
        "a2_bundle": a2_bundle,
        "a2_bundle_receipt": a2_receipt,
    }


def _write_package(output: Path, manifest: Mapping[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=output.parent, prefix=f".{output.name}.")
    os.close(descriptor)
    temporary = Path(temporary_name)
    encoded = (
        json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    try:
        with (
            temporary.open("wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped,
            tarfile.open(fileobj=zipped, mode="w") as archive,
        ):
            info = tarfile.TarInfo(_MANIFEST_NAME)
            info.size, info.mtime, info.mode = len(encoded), 0, 0o644
            archive.addfile(info, BytesIO(encoded))
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_receipt_schema(repository_root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load_json(
        repository_root / "schemas/armindex/a2-deployment-package-receipt.v1.json",
        role="A2 deployment package receipt schema",
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(receipt)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2DeploymentPackageError(
            f"A2 deployment package receipt validation failed: {errors[0].message}"
        )


def build_deployment_package(
    repository_root: Path,
    *,
    attempt_id: str,
    output_path: Path,
    assets: A2DeploymentAssets,
) -> dict[str, Any]:
    """Build a one-member hash-only package after validating every declared source."""

    repository = repository_root.resolve(strict=True)
    if _ATTEMPT.fullmatch(attempt_id) is None:
        raise A2DeploymentPackageError("attempt ID is invalid")
    output = output_path.resolve()
    if output.is_relative_to(repository) or output.exists():
        raise A2DeploymentPackageError("deployment package output must be new and outside Git")
    bindings = validate_deployment_assets(repository, assets=assets)
    manifest_body = {
        "schema_version": "myis.armindex-a2-deployment-package.v1",
        "attempt_id": attempt_id,
        "status": "PASS_CPU_LOCAL_A2_DEPLOYMENT_PACKAGE",
        "package_mode": "HASH_ONLY_METADATA_AND_POINTERS",
        "provider_instance_binding_status": "UNBOUND_FRESH_INSTANCE_REQUIRED",
        "scientific_authority": False,
        "measured_execution_authorized": False,
        "protected_payload_included": False,
        "model_or_wheel_bytes_included": False,
        "package_members": [_MANIFEST_NAME],
        "assets": {
            key: value for key, value in bindings.items() if key != "a2_bundle_receipt"
        },
    }
    manifest = {
        **manifest_body,
        "deployment_manifest_sha256": canonical_sha256(manifest_body),
    }
    if _DESTROYED_INSTANCE_ID in json.dumps(manifest, ensure_ascii=True, sort_keys=True):
        raise A2DeploymentPackageError("deployment manifest binds the destroyed instance")
    _write_package(output, manifest)
    a2_receipt = bindings["a2_bundle_receipt"]
    receipt_body = {
        "schema_version": "myis.armindex-a2-deployment-package-receipt.v1",
        "receipt_id": f"{attempt_id}-deployment-package-v1",
        "attempt_id": attempt_id,
        "status": "PASS_CPU_LOCAL_A2_DEPLOYMENT_PACKAGE",
        "package_sha256": file_sha256(output),
        "deployment_manifest_sha256": manifest["deployment_manifest_sha256"],
        "a2_bundle_receipt_sha256": a2_receipt["receipt_sha256"],
        "a2_bundle_sha256": a2_receipt["bundle_sha256"],
        "frozen_a1_bundle_sha256": bindings["frozen_a1_bundle"]["bundle_sha256"],
        "model_file_counts": {arm_id: 12 for arm_id in _ARMS},
        "wheelhouse_declared_file_count": 14,
        "handoff_source_file_counts": {"baseline": 28, "journal": 7, "closeout": 11},
        "provider_instance_binding_status": "UNBOUND_FRESH_INSTANCE_REQUIRED",
        "scientific_authority": False,
        "measured_execution_authorized": False,
        "protected_payload_included": False,
        "model_or_wheel_bytes_included": False,
    }
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    _validate_receipt_schema(repository, receipt)
    return {"manifest": manifest, "receipt": receipt}


def validate_deployment_package(
    repository_root: Path,
    *,
    package_path: Path,
    receipt: Mapping[str, Any],
    assets: A2DeploymentAssets | None = None,
) -> dict[str, Any]:
    """Validate the isolated package and optionally re-probe all local source assets."""

    repository = repository_root.resolve(strict=True)
    checked = dict(receipt)
    _validate_receipt_schema(repository, checked)
    if checked.get("receipt_sha256") != canonical_sha256(
        {key: value for key, value in checked.items() if key != "receipt_sha256"}
    ):
        raise A2DeploymentPackageError("deployment receipt self-hash drift")
    package = _require_safe_file(package_path, role="A2 deployment package")
    if file_sha256(package) != checked["package_sha256"]:
        raise A2DeploymentPackageError("deployment package hash drift")
    try:
        with tarfile.open(package, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) != 1 or members[0].name != _MANIFEST_NAME or not members[0].isreg():
                raise A2DeploymentPackageError("deployment package closure is not hash-only")
            stream = archive.extractfile(members[0])
            if stream is None:
                raise A2DeploymentPackageError("deployment manifest is missing")
            manifest = json.loads(stream.read().decode("ascii"))
    except (OSError, tarfile.TarError, UnicodeError, json.JSONDecodeError) as error:
        raise A2DeploymentPackageError("deployment package cannot be read") from error
    if not isinstance(manifest, dict):
        raise A2DeploymentPackageError("deployment manifest is invalid")
    if (
        manifest.get("deployment_manifest_sha256") != checked["deployment_manifest_sha256"]
        or manifest.get("deployment_manifest_sha256")
        != canonical_sha256(
            {key: value for key, value in manifest.items() if key != "deployment_manifest_sha256"}
        )
        or manifest.get("package_mode") != "HASH_ONLY_METADATA_AND_POINTERS"
        or manifest.get("provider_instance_binding_status") != "UNBOUND_FRESH_INSTANCE_REQUIRED"
        or manifest.get("scientific_authority") is not False
        or manifest.get("measured_execution_authorized") is not False
        or manifest.get("protected_payload_included") is not False
        or manifest.get("model_or_wheel_bytes_included") is not False
        or manifest.get("package_members") != [_MANIFEST_NAME]
        or _DESTROYED_INSTANCE_ID in json.dumps(manifest, ensure_ascii=True, sort_keys=True)
    ):
        raise A2DeploymentPackageError("deployment manifest identity or safety drift")
    manifest_assets = manifest.get("assets")
    if not isinstance(manifest_assets, Mapping):
        raise A2DeploymentPackageError("deployment manifest asset bindings are invalid")
    a2_bundle = manifest_assets.get("a2_bundle")
    frozen_a1 = manifest_assets.get("frozen_a1_bundle")
    if (
        not isinstance(a2_bundle, Mapping)
        or not isinstance(frozen_a1, Mapping)
        or a2_bundle.get("bundle_sha256") != checked["a2_bundle_sha256"]
        or a2_bundle.get("receipt_sha256") != checked["a2_bundle_receipt_sha256"]
        or frozen_a1.get("bundle_sha256") != checked["frozen_a1_bundle_sha256"]
    ):
        raise A2DeploymentPackageError("deployment receipt differs from asset bindings")
    if assets is not None:
        rebound = validate_deployment_assets(repository, assets=assets)
        rebound_manifest_assets = {
            key: value for key, value in rebound.items() if key != "a2_bundle_receipt"
        }
        if rebound_manifest_assets != manifest_assets:
            raise A2DeploymentPackageError("deployment source asset drift")
    return {**checked, "validation_status": "PASS"}


__all__ = [
    "A2DeploymentAssets",
    "A2DeploymentPackageError",
    "build_deployment_package",
    "validate_deployment_assets",
    "validate_deployment_package",
]
