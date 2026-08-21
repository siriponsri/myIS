"""Build the fresh A4 HARNESS-DEV runtime package inside Owner-local storage.

The builder copies immutable source model/corpus assets into a new A4 root.  It
never imports A3 execution code or reuses a remote A3 root/cache; it merely
uses the frozen bytes as an Owner-local source from which a new A4 package and
hash closure are made.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .a4_execution import validate_a4_predecessor_binding
from .a4_hdev_materializer import validate_a4_hdev_handoff
from .a4_selection_materializer import validate_selection_input_materialization


_DENSE_ARMS = ("ARM-03", "ARM-04", "ARM-05")
_COPY_MEMBERS = ("corpus.jsonl",)
_PROTECTED_NAME_PARTS = ("qrel", "membership", "ranking", "credential", "secret", "provider_payload")


class A4AssetBundleError(ValueError):
    """Raised when a fresh A4 runtime package cannot be safely assembled."""


def build_a4_selection_runtime_package(
    *,
    hdev_package_root: Path,
    selection_input_root: Path,
    output_root: Path,
    attempt_id: str,
    predecessor_binding: Mapping[str, Any],
    profile_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a fresh opaque Selection-125 runtime package.

    The HDEV package is an immutable asset seed: only its corpus, programs,
    and model trees are copied.  The Selection query package is read from the
    validated Owner Store materialization and is copied as opaque
    ``work_token``/``text`` JSONL.  Qrels, membership, rankings, and evaluator
    payloads are intentionally never read or included in the remote package.
    """

    if not isinstance(attempt_id, str) or not attempt_id.startswith("a4-"):
        raise A4AssetBundleError("A4 Selection attempt identity is invalid")
    predecessor = validate_a4_predecessor_binding(predecessor_binding)
    profile = _profile_registry(profile_registry, attempt_id=attempt_id, predecessor=predecessor)
    source_package = _directory(hdev_package_root, "validated HDEV runtime package")
    source_receipt = _load_json(_file(source_package / "A4_RUNTIME_PACKAGE_RECEIPT.json", "HDEV runtime receipt"))
    source_attempt = source_receipt.get("attempt_id")
    if not isinstance(source_attempt, str) or source_attempt == attempt_id:
        raise A4AssetBundleError("Selection package requires a distinct fresh attempt identity")
    validate_a4_hdev_runtime_package(source_package, expected_attempt_id=source_attempt)
    source_assets = _directory(source_package / "assets", "validated HDEV runtime assets")

    selection_root = _directory(selection_input_root, "Selection input materialization")
    selection_receipt_file = _file(
        selection_root / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json",
        "Selection input receipt",
    )
    selection_receipt = _load_json(selection_receipt_file)
    selection_attempt = selection_receipt.get("attempt_id")
    if not isinstance(selection_attempt, str):
        raise A4AssetBundleError("Selection input receipt attempt identity is invalid")
    validate_selection_input_materialization(selection_root, expected_attempt_id=selection_attempt)
    query_file = _selection_query_file(selection_root, selection_receipt)
    rows = _query_rows(query_file, None)
    if len(rows) != 125:
        raise A4AssetBundleError("Selection input package must contain exactly 125 queries")

    destination = Path(output_root).resolve()
    if destination.exists() or destination.is_symlink():
        raise A4AssetBundleError("fresh A4 Selection package destination already exists")
    destination.mkdir(parents=True, exist_ok=False)
    assets = destination / "assets"
    try:
        assets.mkdir()
        _copy_selection_seed_assets(source_assets, assets)
        _write_json(assets / "queries.jsonl", rows, jsonl=True)
        scope_body = {
            "schema_version": "myis.armindex-a4-selection-scope.v1",
            "scope": "Selection-125",
            "population": "OUT",
            "query_count": 125,
            "parent_split_sha256": _sha256(selection_receipt.get("parent_split_sha256"), "parent_split_sha256"),
            "selection_input_receipt_sha256": file_sha256(selection_receipt_file),
            "query_bundle_sha256": file_sha256(assets / "queries.jsonl"),
            "selection_accesses": 0,
            "final_accesses": 0,
            "protected_payload_included": False,
        }
        scope = {**scope_body, "scope_sha256": canonical_sha256(scope_body)}
        _write_json(assets / "selection-scope.json", scope)
        inventory_body = {
            "schema_version": "myis.armindex-a4-runtime-assets-inventory.v1",
            "attempt_id": attempt_id,
            "asset_sha256s": _asset_hashes(assets),
            "selection_scope_sha256": scope["scope_sha256"],
            "profile_registry_sha256": profile["registry_sha256"],
            "selection_input_receipt_sha256": file_sha256(selection_receipt_file),
            "protected_payload_included": False,
        }
        inventory = {**inventory_body, "inventory_sha256": canonical_sha256(inventory_body)}
        _write_json(assets / "A4_RUNTIME_ASSETS.json", inventory)
        runtime_body = {
            "schema_version": "myis.armindex-a4-runtime-bindings.v1",
            "attempt_id": attempt_id,
            "predecessor_binding_sha256": predecessor["binding_sha256"],
            "profile_registry_sha256": profile["registry_sha256"],
            "selection_scope_sha256": scope["scope_sha256"],
            "asset_inventory_sha256": inventory["inventory_sha256"],
            "winner_program_sha256s": predecessor["winner_program_sha256s"],
            "primary_arm_scope": list(_DENSE_ARMS),
            "protected_payload_included": False,
        }
        runtime = {**runtime_body, "runtime_bindings_sha256": canonical_sha256(runtime_body)}
        _write_json(destination / "A4_RUNTIME_BINDINGS.json", runtime)
        archive = destination / "a4-selection-runtime-assets.tar.gz"
        _tar_directory(assets, archive)
        body = {
            "schema_version": "myis.armindex-a4-selection-runtime-package-receipt.v1",
            "status": "PASS_A4_SELECTION_RUNTIME_PACKAGE",
            "attempt_id": attempt_id,
            "source_hdev_attempt_id": source_attempt,
            "selection_input_receipt_sha256": file_sha256(selection_receipt_file),
            "selection_scope_sha256": scope["scope_sha256"],
            "asset_inventory_sha256": inventory["inventory_sha256"],
            "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
            "selection_query_count": 125,
            "archive_sha256": file_sha256(archive),
            "archive_size_bytes": archive.stat().st_size,
            "protected_payload_included": False,
            "selection_accesses": 0,
            "final_accesses": 0,
        }
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _write_json(destination / "A4_SELECTION_RUNTIME_PACKAGE_RECEIPT.json", receipt)
        return receipt
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def validate_a4_selection_runtime_package(root: Path, *, expected_attempt_id: str) -> dict[str, Any]:
    """Validate a complete Selection-125 package before remote staging."""

    package = _directory(root, "A4 Selection runtime package")
    receipt = _load_json(_file(package / "A4_SELECTION_RUNTIME_PACKAGE_RECEIPT.json", "Selection runtime receipt"))
    if receipt.get("attempt_id") != expected_attempt_id or receipt.get("status") != "PASS_A4_SELECTION_RUNTIME_PACKAGE":
        raise A4AssetBundleError("A4 Selection runtime package identity is invalid")
    _self_hash(receipt, "receipt_sha256", "Selection runtime receipt")
    if receipt.get("selection_query_count") != 125 or receipt.get("selection_accesses") != 0 or receipt.get("final_accesses") != 0:
        raise A4AssetBundleError("Selection runtime package scope/counters are invalid")
    runtime = _load_json(_file(package / "A4_RUNTIME_BINDINGS.json", "Selection runtime bindings"))
    _self_hash(runtime, "runtime_bindings_sha256", "Selection runtime bindings")
    assets = _directory(package / "assets", "Selection runtime assets")
    expected_top = {"corpus.jsonl", "queries.jsonl", "selection-scope.json", "programs", "models", "A4_RUNTIME_ASSETS.json"}
    if {path.name for path in assets.iterdir()} != expected_top:
        raise A4AssetBundleError("Selection runtime assets contain unexpected files")
    scope = _load_json(_file(assets / "selection-scope.json", "Selection scope"))
    _self_hash(scope, "scope_sha256", "Selection scope")
    if scope.get("schema_version") != "myis.armindex-a4-selection-scope.v1" or scope.get("scope") != "Selection-125" or scope.get("population") != "OUT" or scope.get("query_count") != 125:
        raise A4AssetBundleError("Selection scope is invalid")
    if scope.get("selection_accesses") != 0 or scope.get("final_accesses") != 0 or scope.get("protected_payload_included") is not False:
        raise A4AssetBundleError("Selection scope counters/protection are invalid")
    rows = _query_rows(_file(assets / "queries.jsonl", "Selection query package"), None)
    if len(rows) != 125:
        raise A4AssetBundleError("Selection query package coverage is incomplete")
    inventory = _load_json(_file(assets / "A4_RUNTIME_ASSETS.json", "Selection runtime inventory"))
    _self_hash(inventory, "inventory_sha256", "Selection runtime inventory")
    if inventory.get("asset_sha256s") != _asset_hashes(assets, exclude={"A4_RUNTIME_ASSETS.json"}):
        raise A4AssetBundleError("Selection runtime asset inventory hash drift")
    if inventory.get("selection_scope_sha256") != scope["scope_sha256"] or runtime.get("selection_scope_sha256") != scope["scope_sha256"] or runtime.get("asset_inventory_sha256") != inventory["inventory_sha256"]:
        raise A4AssetBundleError("Selection runtime scope/inventory binding drift")
    if receipt.get("archive_sha256") != file_sha256(_file(package / "a4-selection-runtime-assets.tar.gz", "Selection runtime archive")):
        raise A4AssetBundleError("Selection runtime archive hash drift")
    _validate_archive_names(package / "a4-selection-runtime-assets.tar.gz")
    return receipt


def _selection_query_file(selection_root: Path, receipt: Mapping[str, Any]) -> Path:
    artifacts = receipt.get("protected_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 1 or not isinstance(artifacts[0], Mapping):
        raise A4AssetBundleError("Selection input protected artifact declaration is invalid")
    relative = artifacts[0].get("relative_path")
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise A4AssetBundleError("Selection input protected artifact path is invalid")
    candidate = (selection_root / relative).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_file() or not candidate.is_relative_to(selection_root):
        raise A4AssetBundleError("Selection input query package is unsafe")
    declared = artifacts[0].get("sha256")
    if not isinstance(declared, str) or declared != file_sha256(candidate):
        raise A4AssetBundleError("Selection input query package hash drift")
    return candidate


def _copy_selection_seed_assets(source_assets: Path, destination: Path) -> None:
    """Copy only the immutable retrieval components from a validated HDEV seed."""

    _copy_file(_file(source_assets / "corpus.jsonl", "HDEV seed corpus"), destination / "corpus.jsonl")
    programs = destination / "programs"
    models = destination / "models"
    programs.mkdir()
    models.mkdir()
    for arm_id in _DENSE_ARMS:
        _copy_file(
            _file(source_assets / "programs" / f"{arm_id}.json", f"HDEV seed {arm_id} program"),
            programs / f"{arm_id}.json",
        )
        _copy_tree(_directory(source_assets / "models" / arm_id, f"HDEV seed {arm_id} model"), models / arm_id)


def _validate_archive_names(path: Path) -> None:
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
    except (OSError, tarfile.TarError) as error:
        raise A4AssetBundleError("Selection runtime archive is invalid") from error
    names = {member.name for member in members}
    if any(member.issym() or member.islnk() or not member.isfile() for member in members):
        raise A4AssetBundleError("Selection runtime archive contains unsafe member")
    if any(any(part in name.lower() for part in _PROTECTED_NAME_PARTS) for name in names):
        raise A4AssetBundleError("Selection runtime archive contains protected artifact name")
    required = {"corpus.jsonl", "queries.jsonl", "selection-scope.json", "A4_RUNTIME_ASSETS.json"}
    if not required.issubset(names) or "hdev-scope.json" in names:
        raise A4AssetBundleError("Selection runtime archive scope is invalid")


def _sha256(value: Any, role: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise A4AssetBundleError(f"{role} is invalid")
    return value


def build_a4_hdev_runtime_package(
    *,
    source_assets_root: Path,
    train_package_root: Path,
    split_membership_path: Path,
    output_root: Path,
    attempt_id: str,
    predecessor_binding: Mapping[str, Any],
    profile_registry: Mapping[str, Any],
    hdev_handoff_root: Path | None = None,
) -> dict[str, Any]:
    """Copy a 100-query HDEV package and emit a self-hashed A4 asset bundle."""

    predecessor = validate_a4_predecessor_binding(predecessor_binding)
    profile = _profile_registry(profile_registry, attempt_id=attempt_id, predecessor=predecessor)
    source = _directory(source_assets_root, "source assets")
    train = _directory(train_package_root, "Train-250 package")
    split = _file(split_membership_path, "HDEV membership")
    destination = Path(output_root).resolve()
    if destination.exists() or destination.is_symlink():
        raise A4AssetBundleError("fresh A4 package destination already exists")
    handoff_receipt: Mapping[str, Any] | None = None
    if hdev_handoff_root is not None:
        handoff_receipt = validate_a4_hdev_handoff(hdev_handoff_root, expected_attempt_id=attempt_id)
        query_source = _file(
            Path(hdev_handoff_root) / "protected" / "hdev-queries.jsonl",
            "validated HDEV query package",
        )
        rows = _query_rows(query_source, None)
        if len(rows) != 100:
            raise A4AssetBundleError("validated HDEV handoff does not contain 100 queries")
    else:
        hdev = _hdev_tokens(split)
        rows = _query_rows(_file(train / "inputs" / "queries.jsonl", "Train-250 queries"), hdev)
    destination.mkdir(parents=True, exist_ok=False)
    assets = destination / "assets"
    try:
        assets.mkdir()
        _copy_file(_file(source / "corpus.jsonl", "source corpus"), assets / "corpus.jsonl")
        _write_json(assets / "queries.jsonl", rows, jsonl=True)
        programs = assets / "programs"
        programs.mkdir()
        models = assets / "models"
        models.mkdir()
        for arm_id in _DENSE_ARMS:
            _copy_file(_file(source / "programs" / f"{arm_id}.json", f"{arm_id} program"), programs / f"{arm_id}.json")
            _copy_tree(_directory(source / "models" / arm_id, f"{arm_id} model"), models / arm_id)
        scope = {
            "schema_version": "myis.armindex-a4-harness-dev-scope.v1",
            "scope": "HARNESS-DEV",
            "query_count": 100,
            "hdev_membership_sha256": handoff_receipt["hdev_membership_sha256"] if handoff_receipt else file_sha256(split),
            "hdev_handoff_receipt_sha256": handoff_receipt["receipt_sha256"] if handoff_receipt else None,
            "query_bundle_sha256": file_sha256(assets / "queries.jsonl"),
            "protected_payload_included": False,
        }
        scope["scope_sha256"] = canonical_sha256(scope)
        _write_json(assets / "hdev-scope.json", scope)
        inventory_body = {
            "schema_version": "myis.armindex-a4-runtime-assets-inventory.v1",
            "attempt_id": attempt_id,
            "asset_sha256s": _asset_hashes(assets),
            "hdev_scope_sha256": scope["scope_sha256"],
            "profile_registry_sha256": profile["registry_sha256"],
            "hdev_handoff_receipt_sha256": handoff_receipt["receipt_sha256"] if handoff_receipt else None,
            "protected_payload_included": False,
        }
        inventory = {**inventory_body, "inventory_sha256": canonical_sha256(inventory_body)}
        _write_json(assets / "A4_RUNTIME_ASSETS.json", inventory)
        runtime_body = {
            "schema_version": "myis.armindex-a4-runtime-bindings.v1",
            "attempt_id": attempt_id,
            "predecessor_binding_sha256": predecessor["binding_sha256"],
            "profile_registry_sha256": profile["registry_sha256"],
            "hdev_scope_sha256": scope["scope_sha256"],
            "asset_inventory_sha256": inventory["inventory_sha256"],
            "winner_program_sha256s": predecessor["winner_program_sha256s"],
            "primary_arm_scope": list(_DENSE_ARMS),
            "hdev_handoff_receipt_sha256": handoff_receipt["receipt_sha256"] if handoff_receipt else None,
            "protected_payload_included": False,
        }
        runtime = {**runtime_body, "runtime_bindings_sha256": canonical_sha256(runtime_body)}
        _write_json(destination / "A4_RUNTIME_BINDINGS.json", runtime)
        archive = destination / "a4-runtime-assets.tar.gz"
        _tar_directory(assets, archive)
        body = {
            "schema_version": "myis.armindex-a4-runtime-package-receipt.v1",
            "status": "PASS_A4_HDEV_RUNTIME_PACKAGE",
            "attempt_id": attempt_id,
            "asset_inventory_sha256": inventory["inventory_sha256"],
            "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
            "hdev_query_count": 100,
            "hdev_membership_sha256": handoff_receipt["hdev_membership_sha256"] if handoff_receipt else file_sha256(split),
            "hdev_handoff_receipt_sha256": handoff_receipt["receipt_sha256"] if handoff_receipt else None,
            "archive_sha256": file_sha256(archive),
            "archive_size_bytes": archive.stat().st_size,
            "protected_payload_included": False,
        }
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _write_json(destination / "A4_RUNTIME_PACKAGE_RECEIPT.json", receipt)
        return receipt
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def validate_a4_hdev_runtime_package(root: Path, *, expected_attempt_id: str) -> dict[str, Any]:
    """Validate a complete fresh A4 package before it is allowed to stage."""

    package = _directory(root, "A4 runtime package")
    receipt = _load_json(_file(package / "A4_RUNTIME_PACKAGE_RECEIPT.json", "runtime package receipt"))
    if receipt.get("attempt_id") != expected_attempt_id or receipt.get("status") != "PASS_A4_HDEV_RUNTIME_PACKAGE":
        raise A4AssetBundleError("A4 runtime package identity is invalid")
    _self_hash(receipt, "receipt_sha256", "runtime package receipt")
    runtime = _load_json(_file(package / "A4_RUNTIME_BINDINGS.json", "runtime bindings"))
    _self_hash(runtime, "runtime_bindings_sha256", "runtime bindings")
    assets = _directory(package / "assets", "runtime assets")
    scope = _load_json(_file(assets / "hdev-scope.json", "HDEV scope"))
    _self_hash(scope, "scope_sha256", "HDEV scope")
    if scope.get("scope") != "HARNESS-DEV" or scope.get("query_count") != 100:
        raise A4AssetBundleError("A4 runtime package must contain exactly HDEV-100")
    rows = _query_rows(_file(assets / "queries.jsonl", "HDEV query package"), None)
    if len(rows) != 100:
        raise A4AssetBundleError("A4 HDEV query package coverage is incomplete")
    inventory = _load_json(_file(assets / "A4_RUNTIME_ASSETS.json", "runtime inventory"))
    _self_hash(inventory, "inventory_sha256", "runtime inventory")
    if inventory.get("asset_sha256s") != _asset_hashes(assets, exclude={"A4_RUNTIME_ASSETS.json"}):
        raise A4AssetBundleError("A4 runtime asset inventory hash drift")
    if runtime.get("asset_inventory_sha256") != inventory["inventory_sha256"]:
        raise A4AssetBundleError("A4 runtime inventory binding drift")
    handoff_sha = receipt.get("hdev_handoff_receipt_sha256")
    if handoff_sha is not None:
        if not isinstance(handoff_sha, str) or len(handoff_sha) != 64:
            raise A4AssetBundleError("A4 HDEV handoff binding is invalid")
        if scope.get("hdev_handoff_receipt_sha256") != handoff_sha or runtime.get("hdev_handoff_receipt_sha256") != handoff_sha:
            raise A4AssetBundleError("A4 HDEV handoff binding drift")
    if receipt.get("archive_sha256") != file_sha256(_file(package / "a4-runtime-assets.tar.gz", "runtime archive")):
        raise A4AssetBundleError("A4 runtime archive hash drift")
    return receipt


def _profile_registry(value: Mapping[str, Any], *, attempt_id: str, predecessor: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema_version") != "myis.armindex-a4-profile-registry.v1":
        raise A4AssetBundleError("A4 profile registry is invalid")
    if value.get("attempt_id") != attempt_id or value.get("predecessor_binding_sha256") != predecessor["binding_sha256"]:
        raise A4AssetBundleError("A4 profile registry does not bind this package")
    _self_hash(value, "registry_sha256", "A4 profile registry")
    return dict(value)


def _hdev_tokens(path: Path) -> set[str]:
    membership = _load_json(path)
    raw = membership.get("harness_dev") if isinstance(membership, Mapping) else None
    if not isinstance(raw, list) or len(raw) != 100 or any(not isinstance(token, str) or not token for token in raw):
        raise A4AssetBundleError("HDEV membership must contain 100 opaque tokens")
    tokens = set(raw)
    if len(tokens) != 100:
        raise A4AssetBundleError("HDEV membership tokens are duplicated")
    return tokens


def _query_rows(path: Path, selected: set[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            raise A4AssetBundleError("query package is not JSONL") from error
        if not isinstance(item, dict) or set(item) - {"work_token", "text"} or set(item) != {"work_token", "text"}:
            raise A4AssetBundleError("query package contains unsupported fields")
        token, text = item["work_token"], item["text"]
        if not isinstance(token, str) or not token or not isinstance(text, str) or not text:
            raise A4AssetBundleError("query package has invalid opaque work token")
        if token in seen:
            raise A4AssetBundleError("query package has duplicate opaque work token")
        seen.add(token)
        if selected is None or token in selected:
            rows.append(item)
    if selected is not None and {row["work_token"] for row in rows} != selected:
        raise A4AssetBundleError("HDEV membership does not match Train-250 queries")
    return rows


def _asset_hashes(root: Path, *, exclude: set[str] | None = None) -> dict[str, str]:
    forbidden = exclude or set()
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda candidate: candidate.relative_to(root).as_posix()):
        if path.is_dir():
            continue
        if path.is_symlink() or not path.is_file():
            raise A4AssetBundleError("runtime asset package contains an unsafe entry")
        relative = path.relative_to(root).as_posix()
        if relative in forbidden:
            continue
        if any(part in relative.lower() for part in _PROTECTED_NAME_PARTS):
            raise A4AssetBundleError("runtime asset package contains protected artifact name")
        result[relative] = file_sha256(path)
    if not result:
        raise A4AssetBundleError("runtime asset package is empty")
    return result


def _tar_directory(source: Path, destination: Path) -> None:
    with tarfile.open(destination, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(source.rglob("*"), key=lambda candidate: candidate.relative_to(source).as_posix()):
            if path.is_dir():
                continue
            relative = path.relative_to(source).as_posix()
            info = archive.gettarinfo(str(path), arcname=relative)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            with path.open("rb") as handle:
                archive.addfile(info, handle)


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        raise A4AssetBundleError("A4 package model destination exists")
    shutil.copytree(source, destination, symlinks=False)
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise A4AssetBundleError("source model tree contains a symlink")


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _write_json(path: Path, value: Any, *, jsonl: bool = False) -> None:
    if jsonl:
        rendered = "".join(canonical_json(row) + "\n" for row in value)
    else:
        rendered = canonical_json(value) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A4AssetBundleError("Owner-local package JSON is invalid") from error


def _directory(path: Path, role: str) -> Path:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_dir():
        raise A4AssetBundleError(f"{role} must be a regular directory")
    return candidate


def _file(path: Path, role: str) -> Path:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_file():
        raise A4AssetBundleError(f"{role} must be a regular file")
    return candidate


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    digest = value.get(field)
    if not isinstance(digest, str) or len(digest) != 64:
        raise A4AssetBundleError(f"{role} self-hash is invalid")
    if digest != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4AssetBundleError(f"{role} self-hash does not match")


__all__ = [
    "A4AssetBundleError",
    "build_a4_hdev_runtime_package",
    "build_a4_selection_runtime_package",
    "validate_a4_hdev_runtime_package",
    "validate_a4_selection_runtime_package",
]
