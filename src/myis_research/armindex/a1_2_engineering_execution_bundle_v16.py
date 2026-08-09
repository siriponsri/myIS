"""Fail-closed additive v16 engineering-bundle builder for A1.2.

This module deliberately has no provider, SSH, model-download, or retrieval
operation.  It binds the engineering executor and lifecycle files to the
unchanged v11-v15 scientific contract before a separate admission process can
consider them.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import stat
import subprocess
import tarfile
import tempfile
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

REVISION_ID = "a1.2-engineering-execution-v16"
CONTRACT_PATH = Path("control/armindex/a1.2/engineering-execution-contract.v16.json")
CONTRACT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-engineering-execution-contract.v16.json"
)
BUNDLE_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-engineering-execution-bundle-receipt.v16.json"
)
_BASE_PATHS = (
    CONTRACT_PATH.as_posix(),
    CONTRACT_SCHEMA_PATH.as_posix(),
    BUNDLE_SCHEMA_PATH.as_posix(),
    "src/myis_research/kernel/canonical.py",
    "src/myis_research/armindex/bm25s_adapter.py",
    "src/myis_research/armindex/scientific_common_programs_v11.py",
    "src/myis_research/armindex/a1_2_live_preflight_runtime_v9.py",
    "src/myis_research/armindex/a1_2_engineering_execution_bundle_v16.py",
    "src/myis_research/armindex/a1_2_safe_return_v16.py",
    "scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16.ps1",
)
_SOURCE_PREFIXES = (
    "src/myis_research/armindex/",
    "scripts/a1_2_vast/",
)
_ALLOWED_SUFFIXES = frozenset({".json", ".py", ".ps1"})
_FORBIDDEN_PATH = re.compile(
    r"(?:qrels|membership|query[_-]?ids?|credential|secret|token|id_rsa|id_ed25519|provider[_-]?payload)",
    re.IGNORECASE,
)


class EngineeringExecutionV16Error(ValueError):
    """Raised when a v16 engineering binding is incomplete or drifts."""


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EngineeringExecutionV16Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise EngineeringExecutionV16Error(f"{role} must be an object")
    return value


def _schema(root: Path, schema_path: Path, value: Mapping[str, Any], *, role: str) -> None:
    schema = _load(root / schema_path, role=f"{role} schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        raise EngineeringExecutionV16Error(f"{role} schema failure at {list(errors[0].path)}")


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _safe(value: Mapping[str, Any], *, role: str) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise EngineeringExecutionV16Error(f"{role} crosses the protected boundary") from error


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise EngineeringExecutionV16Error("Git identity cannot be verified")
    return result.stdout.strip()


def _validate_frozen_files(root: Path, files: Mapping[str, Any]) -> None:
    for relative, expected in sorted(files.items()):
        path = root / relative
        if _FORBIDDEN_PATH.search(relative):
            raise EngineeringExecutionV16Error("frozen file path crosses the protected boundary")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise EngineeringExecutionV16Error("frozen file binding is invalid")
        try:
            metadata = path.lstat()
        except OSError as error:
            raise EngineeringExecutionV16Error("frozen v11-v15 file is unavailable") from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or not path.resolve().is_relative_to(root):
            raise EngineeringExecutionV16Error("frozen v11-v15 file is unsafe")
        if file_sha256(path) != expected:
            raise EngineeringExecutionV16Error("frozen v11-v15 hash drift")


def _source_paths(
    contract: Mapping[str, Any],
    *,
    field: str,
    roles: tuple[str, ...],
    require_ready: bool,
) -> tuple[str, ...]:
    sources = contract[field]
    resolved: list[str] = []
    for role in roles:
        source = sources[role]
        relative, expected = source["path"], source["sha256"]
        if not any(relative.startswith(prefix) for prefix in _SOURCE_PREFIXES):
            raise EngineeringExecutionV16Error("engineering source path is outside the approved surface")
        if expected is None:
            if require_ready:
                raise EngineeringExecutionV16Error("engineering source hash is pending")
        elif not isinstance(expected, str) or len(expected) != 64:
            raise EngineeringExecutionV16Error("engineering source hash is invalid")
        resolved.append(relative)
    if len(set(resolved)) != len(resolved):
        raise EngineeringExecutionV16Error("engineering source paths must be distinct")
    return tuple(resolved)


def validate_contract(repository_root: Path, *, require_ready: bool = False) -> dict[str, Any]:
    root = repository_root.resolve()
    contract = _load(root / CONTRACT_PATH, role="v16 engineering contract")
    _schema(root, CONTRACT_SCHEMA_PATH, contract, role="v16 engineering contract")
    if contract.get("contract_sha256") != _self_hash(contract, "contract_sha256"):
        raise EngineeringExecutionV16Error("v16 engineering contract self-hash mismatch")
    _safe(contract, role="v16 engineering contract")
    _validate_frozen_files(root, contract["frozen_file_sha256"])
    if contract["runtime_policy"] != {
        "runtime_downloads_forbidden": True,
        "model_bytes_owner_local_only": True,
        "protected_payload_in_bundle": False,
        "safe_aggregate_export_required": True,
    }:
        raise EngineeringExecutionV16Error("v16 runtime/protected-boundary policy drift")
    if any(contract["authorization"].values()) or any(contract["counters"].values()):
        raise EngineeringExecutionV16Error("v16 cannot authorize measured work")
    executor_sources = _source_paths(
        contract,
        field="executor_sources",
        roles=("retrieval_executor", "execution_lifecycle"),
        require_ready=require_ready,
    )
    support_roles = (
        "safe_return",
        "safe_return_builder",
        "watchdog",
        "input_manifest",
        "measured_runner",
        "remote_arm_worker",
        "distributed_launcher",
        "evaluator_promotion",
    )
    support_sources = _source_paths(
        contract,
        field="support_sources",
        roles=support_roles,
        require_ready=require_ready,
    )
    if contract["status"] == "PENDING_EXECUTOR_INTEGRATION":
        if require_ready:
            raise EngineeringExecutionV16Error("executor integration remains pending")
        return contract
    if contract["status"] != "READY_FOR_CLEAN_BUNDLE":
        raise EngineeringExecutionV16Error("v16 engineering status is invalid")
    for group, roles, sources in (
        ("executor_sources", ("retrieval_executor", "execution_lifecycle"), executor_sources),
        ("support_sources", support_roles, support_sources),
    ):
        for role, relative in zip(roles, sources, strict=True):
            path = root / relative
            try:
                metadata = path.lstat()
            except OSError as error:
                raise EngineeringExecutionV16Error("bound engineering source is unavailable") from error
            if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or path.suffix not in {".py", ".ps1"}:
                raise EngineeringExecutionV16Error("bound engineering source is unsafe")
            if file_sha256(path) != contract[group][role]["sha256"]:
                raise EngineeringExecutionV16Error("bound engineering source hash drift")
    return contract


def bundle_paths(repository_root: Path) -> tuple[str, ...]:
    contract = validate_contract(repository_root, require_ready=True)
    executor_sources = _source_paths(contract, field="executor_sources", roles=("retrieval_executor", "execution_lifecycle"), require_ready=True)
    support_sources = _source_paths(
        contract,
        field="support_sources",
        roles=("safe_return", "safe_return_builder", "watchdog", "input_manifest", "measured_runner", "remote_arm_worker", "distributed_launcher", "evaluator_promotion"),
        require_ready=True,
    )
    paths = tuple(dict.fromkeys((*sorted(contract["frozen_file_sha256"]), *_BASE_PATHS, *executor_sources, *support_sources)))
    if len(paths) != len(set(paths)):
        raise EngineeringExecutionV16Error("v16 bundle path closure contains duplicates")
    return paths


def _bundle_sources(root: Path, paths: tuple[str, ...]) -> None:
    tracked = set(_git(root, "ls-files").splitlines())
    if set(paths) - tracked:
        raise EngineeringExecutionV16Error("v16 bundle contains untracked or missing source")
    for relative in paths:
        path = root / relative
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise EngineeringExecutionV16Error("v16 bundle source is not a unique regular file")
        if path.suffix.lower() not in _ALLOWED_SUFFIXES or metadata.st_size > 8 * 1024 * 1024:
            raise EngineeringExecutionV16Error("v16 bundle source type or size is not allowlisted")
        if not path.resolve().is_relative_to(root):
            raise EngineeringExecutionV16Error("v16 bundle source escapes repository")


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    text = _json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="utf-8") != text:
            raise EngineeringExecutionV16Error("immutable output already exists with different bytes")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_bundle(repository_root: Path, *, output: Path, receipt_output: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    paths = bundle_paths(root)
    target, receipt_target = output.resolve(), receipt_output.resolve()
    if target.is_relative_to(root) or receipt_target.is_relative_to(root) or target == receipt_target:
        raise EngineeringExecutionV16Error("bundle and receipt outputs must be distinct external paths")
    if target.exists() or receipt_target.exists():
        raise EngineeringExecutionV16Error("immutable bundle output already exists")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise EngineeringExecutionV16Error("repository must be clean before bundle creation")
    commit, tree = _git(root, "rev-parse", "HEAD^{commit}"), _git(root, "rev-parse", "HEAD^{tree}")
    if _git(root, "rev-parse", "origin/main") != commit:
        raise EngineeringExecutionV16Error("bundle requires a clean pushed main commit")
    _bundle_sources(root, paths)
    files = [{"path": relative, "size_bytes": (root / relative).stat().st_size, "sha256": file_sha256(root / relative)} for relative in paths]
    path_set_sha256 = canonical_sha256({"paths": list(paths)})
    manifest_body = {"schema_version": "myis.armindex-a1.2-engineering-execution-bundle.v16", "revision_id": REVISION_ID, "git_commit": commit, "git_tree": tree, "paths": list(paths), "bundle_path_set_sha256": path_set_sha256, "files": files, "model_bytes_included": False, "protected_payload_included": False, "runtime_downloads_forbidden": True}
    manifest = {**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    os.close(descriptor)
    temporary = Path(name)
    try:
        with temporary.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for relative in paths:
                source = root / relative
                info = tarfile.TarInfo(relative)
                info.size, info.mtime, info.mode = source.stat().st_size, 0, 0o644
                with source.open("rb") as handle:
                    archive.addfile(info, handle)
            for member, text in sorted({"BUNDLE_MANIFEST.json": _json(manifest), "GIT_COMMIT": commit + "\n", "GIT_TREE": tree + "\n"}.items()):
                data = text.encode("utf-8")
                info = tarfile.TarInfo(member)
                info.size, info.mtime, info.mode = len(data), 0, 0o644
                archive.addfile(info, BytesIO(data))
        body = {"schema_version": "myis.armindex-a1.2-engineering-execution-bundle-receipt.v16", "revision_id": REVISION_ID, "status": "ENGINEERING_BUNDLE_BUILT_NOT_ADOPTED", "clean_worktree": True, "pushed_to_origin_main": True, "git_commit": commit, "git_tree": tree, "frozen_bundle_sha256": file_sha256(temporary), "bundle_manifest_sha256": manifest["manifest_sha256"], "bundle_path_set_sha256": path_set_sha256}
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _schema(root, BUNDLE_SCHEMA_PATH, receipt, role="v16 bundle receipt")
        _safe(receipt, role="v16 bundle receipt")
        _write_immutable(receipt_target, receipt)
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return {"status": "PASS", "bundle_sha256": receipt["frozen_bundle_sha256"], "file_count": len(paths), "git_commit": commit, "git_tree": tree}


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-engineering-execution-v16")
    parser.add_argument("command", choices=("validate", "validate-ready", "bundle-paths", "build-bundle"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        contract = validate_contract(args.repository_root)
        result: Mapping[str, Any] = {"status": "PASS", "revision_id": REVISION_ID, "contract_sha256": contract["contract_sha256"], "ready_for_bundle": contract["status"] == "READY_FOR_CLEAN_BUNDLE"}
    elif args.command == "validate-ready":
        contract = validate_contract(args.repository_root, require_ready=True)
        result = {"status": "PASS", "revision_id": REVISION_ID, "ready_for_bundle": True, "executor_sources": contract["executor_sources"]}
    elif args.command == "bundle-paths":
        result = {"status": "PASS", "paths": list(bundle_paths(args.repository_root))}
    else:
        if args.output is None or args.receipt_output is None:
            parser.error("build-bundle requires --output and --receipt-output")
        result = build_bundle(args.repository_root, output=args.output, receipt_output=args.receipt_output)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
