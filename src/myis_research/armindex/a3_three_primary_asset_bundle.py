"""Build an opaque Owner-Store asset archive for the concrete A3 ranker."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
import shutil
import stat
import tarfile
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a2_owner_local_engine import _queries
from .a3_three_primary_concrete_ranker import _tree_sha256
from .a3_three_primary_execution import PRIMARY_ARMS, _validate_package_bindings


class A3ThreePrimaryAssetBundleError(ValueError):
    """Raised when a protected A3 runtime bundle cannot be safely composed."""


def build_a3_three_primary_asset_bundle(
    stage_source_root: Path,
    *,
    runtime_bindings: Mapping[str, Any],
    corpus_path: Path,
    queries_path: Path,
    train_scope: Mapping[str, Any],
    winner_program_paths: Mapping[str, Path],
    target_model_directories: Mapping[str, Path],
) -> dict[str, Any]:
    """Create a fresh Owner-Store source root and opaque runtime archive.

    The caller supplies only Owner-local paths.  This function neither contacts
    a provider nor emits corpus, query, program, model, rank, qrel, or
    membership bytes into repository artifacts.
    """

    target = stage_source_root.resolve()
    repository = Path.cwd().resolve()
    if target.is_relative_to(repository) or target.exists() or target.is_symlink():
        raise A3ThreePrimaryAssetBundleError("A3 stage-source root must be a new Owner-Store directory")
    bindings = _runtime_bindings(runtime_bindings)
    corpus, queries = _regular(corpus_path, role="corpus"), _regular(queries_path, role="queries")
    package = bindings.get("package_bindings")
    checked_package = _validate_package_bindings(package) if package is not None else None
    scope = _train_scope(
        train_scope,
        queries_sha256=file_sha256(queries),
        split_commitment_sha256=(checked_package or {}).get("split_commitment_sha256"),
    )
    if len(_queries(queries)) != 250:
        raise A3ThreePrimaryAssetBundleError("A3 bundle requires exactly 250 Train-250 queries")
    if checked_package is not None:
        if checked_package["corpus_sha256"] != file_sha256(corpus):
            raise A3ThreePrimaryAssetBundleError("A3 package corpus hash does not match staged corpus")
        if checked_package["query_bundle_sha256"] != file_sha256(queries):
            raise A3ThreePrimaryAssetBundleError("A3 package query hash does not match staged queries")
    if set(winner_program_paths) != set(PRIMARY_ARMS) or set(target_model_directories) != set(PRIMARY_ARMS):
        raise A3ThreePrimaryAssetBundleError("A3 bundle must cover exactly the three primary arms")
    target.mkdir(parents=True, exist_ok=False)
    assets = target / "assets"
    try:
        assets.mkdir()
        _copy_file(corpus, assets / "corpus.jsonl")
        _copy_file(queries, assets / "queries.jsonl")
        _write_json(assets / "train-scope.json", scope)
        _write_json(assets / "A3_RUNTIME_BINDINGS.json", bindings)
        programs = assets / "programs"
        models = assets / "models"
        programs.mkdir()
        models.mkdir()
        for arm_id in PRIMARY_ARMS:
            program = _winner_program(winner_program_paths[arm_id], expected_sha256=bindings["winner_bindings"][arm_id]["winner_program_sha256"])
            _write_json(programs / f"{arm_id}.json", program)
            source_model = _directory(target_model_directories[arm_id], role=f"{arm_id} model")
            model_destination = models / arm_id
            shutil.copytree(source_model, model_destination, symlinks=False)
            model_tree_sha256 = _tree_sha256(model_destination)
            _write_json(
                model_destination / "A3_ADAPTER_BINDING.json",
                {
                    "arm_id": arm_id,
                    "target_adapter_sha256": bindings["target_adapter_sha256s"][arm_id],
                    "model_tree_sha256": model_tree_sha256,
                },
            )
        inventory = _inventory(assets)
        _write_json(assets / "A3_RUNTIME_ASSETS.json", inventory)
        _write_ranker_wrapper(assets / "bin" / "a3-three-primary-ranker")
        archive = target / "a3-runtime-assets.tar.gz"
        _archive(assets, archive)
        body = {
            "schema_version": "myis.armindex-a3-three-primary-asset-bundle-receipt.v1",
            "status": "PASS_A3_OWNER_STORE_ASSET_BUNDLE",
            "runtime_bindings_sha256": bindings["runtime_bindings_sha256"],
            **({"package_bindings": checked_package} if checked_package is not None else {}),
            "scope": "Train-250",
            "query_count": 250,
            "corpus_sha256": inventory["remote_asset_sha256s"]["corpus_sha256"],
            "queries_sha256": inventory["remote_asset_sha256s"]["queries_sha256"],
            "model_sha256s": inventory["remote_asset_sha256s"]["model_sha256s"],
            "inventory_sha256": file_sha256(assets / "A3_RUNTIME_ASSETS.json"),
            "archive_sha256": file_sha256(archive),
            "archive_bytes": archive.stat().st_size,
            "provider_contacted": False,
            "remote_execution_started": False,
            "protected_payload_included": False,
        }
        assert_aggregate_only(body)
        return {**body, "receipt_sha256": canonical_sha256(body)}
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        raise


def _runtime_bindings(value: Mapping[str, Any]) -> dict[str, Any]:
    bindings = deepcopy(dict(value))
    required = {
        "schema_version", "primary_arm_scope", "budget_extension_sha256", "authority_sha256",
        "manifest_sha256", "admission_sha256", "winner_bindings", "target_adapter_sha256s",
        "runtime_bindings_sha256",
    }
    if set(bindings) not in (required, required | {"package_bindings"}) or bindings.get("schema_version") != "myis.armindex-a3-three-primary-runtime-bindings.v1" or bindings.get("primary_arm_scope") != list(PRIMARY_ARMS):
        raise A3ThreePrimaryAssetBundleError("A3 runtime bindings are invalid")
    digest = bindings.get("runtime_bindings_sha256")
    if not _sha(digest) or digest != canonical_sha256({key: item for key, item in bindings.items() if key != "runtime_bindings_sha256"}):
        raise A3ThreePrimaryAssetBundleError("A3 runtime binding hash drift")
    for arm_id in PRIMARY_ARMS:
        winner = bindings["winner_bindings"].get(arm_id)
        if not isinstance(winner, Mapping) or not _sha(winner.get("winner_program_sha256")) or not _sha(bindings["target_adapter_sha256s"].get(arm_id)):
            raise A3ThreePrimaryAssetBundleError("A3 winner or adapter binding is invalid")
    if "package_bindings" in bindings:
        try:
            bindings["package_bindings"] = _validate_package_bindings(bindings["package_bindings"])
        except ValueError as error:
            raise A3ThreePrimaryAssetBundleError(str(error)) from error
    return bindings


def _train_scope(
    value: Mapping[str, Any],
    *,
    queries_sha256: str,
    split_commitment_sha256: str | None = None,
) -> dict[str, Any]:
    scope = deepcopy(dict(value))
    expected = {
        "schema_version": "myis.armindex-a3-train-scope.v1",
        "scope": "Train-250",
        "split_id": "Train-250",
        "query_count": 250,
        "queries_sha256": queries_sha256,
    }
    if split_commitment_sha256 is not None:
        expected["split_commitment_sha256"] = split_commitment_sha256
    if scope != expected:
        raise A3ThreePrimaryAssetBundleError("A3 asset bundle accepts only the exact Train-250 scope")
    return scope


def _winner_program(path: Path, *, expected_sha256: str) -> dict[str, Any]:
    value = _read_json(_regular(path, role="winner program"), role="winner program")
    if value.get("program_sha256") != expected_sha256 or expected_sha256 != canonical_sha256({key: item for key, item in value.items() if key != "program_sha256"}):
        raise A3ThreePrimaryAssetBundleError("winner program hash differs from the A2 winner binding")
    return value


def _inventory(assets: Path) -> dict[str, Any]:
    models = {arm_id: _tree_sha256(assets / "models" / arm_id, exclude={"A3_ADAPTER_BINDING.json"}) for arm_id in PRIMARY_ARMS}
    body = {
        "schema_version": "myis.armindex-a3-runtime-assets-inventory.v1",
        "remote_asset_sha256s": {
            "corpus_sha256": file_sha256(assets / "corpus.jsonl"),
            "queries_sha256": file_sha256(assets / "queries.jsonl"),
            "model_sha256s": models,
        },
        "ranker_command": ["bin/a3-three-primary-ranker"],
    }
    runtime = json.loads((assets / "A3_RUNTIME_BINDINGS.json").read_text(encoding="utf-8"))
    if "package_bindings" in runtime:
        body["package_bindings"] = runtime["package_bindings"]
    return {**body, "inventory_sha256": canonical_sha256(body)}


def _archive(assets: Path, destination: Path) -> None:
    with tarfile.open(destination, mode="x:gz", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(assets.rglob("*")):
            if path.is_dir():
                continue
            if path.is_symlink() or not path.is_file():
                raise A3ThreePrimaryAssetBundleError("A3 runtime asset tree contains an unsafe member")
            archive.add(path, arcname=path.relative_to(assets).as_posix(), recursive=False)


def _write_ranker_wrapper(path: Path) -> None:
    path.parent.mkdir()
    path.write_text("#!/bin/sh\nexec \"${A3_REMOTE_PYTHON:?}\" -m myis_research.armindex.a3_three_primary_concrete_ranker \"$@\"\n", encoding="ascii")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _copy_file(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)
    shutil.copystat(source, destination)


def _regular(path: Path, *, role: str) -> Path:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise A3ThreePrimaryAssetBundleError(f"{role} is not a regular file")
    return resolved


def _directory(path: Path, *, role: str) -> Path:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_dir():
        raise A3ThreePrimaryAssetBundleError(f"{role} is not a regular directory")
    return resolved


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise A3ThreePrimaryAssetBundleError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A3ThreePrimaryAssetBundleError(f"{role} is invalid")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


__all__ = ["A3ThreePrimaryAssetBundleError", "build_a3_three_primary_asset_bundle"]
