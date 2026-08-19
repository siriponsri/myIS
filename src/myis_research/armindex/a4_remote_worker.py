"""A4 retrieval-only worker for an isolated remote attempt.

The worker deliberately has no evaluator and does not accept protected split,
qrels, or membership inputs.  It invokes the staged A4 ranker with opaque
asset paths and emits a hash-bound aggregate-safe completion receipt.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a4_remote_ranker import A4RemoteRankerError


class A4RemoteWorkerError(ValueError):
    """Raised when an A4 remote operation cannot complete safely."""


_REQUEST_REQUIRED = {
    "schema_version", "attempt_id", "request_id", "profile_id", "request_sha256",
    "system_sha256", "profile_registry_sha256", "runtime_bindings_sha256",
    "hdev_scope_sha256", "arm_ids", "candidate_depth", "mode", "license_scope",
}
_FORBIDDEN_NAMES = {"qrels", "membership", "query_id", "per_query", "raw_payload", "provider_payload"}


def execute_a4_remote_worker(
    request_path: Path,
    *,
    assets_root: Path,
    output_root: Path,
    ranker_runner: Callable[[Sequence[str]], None] | None = None,
) -> dict[str, Any]:
    """Execute one request and write only an Owner-evaluable package.

    ``ranker_runner`` exists for deterministic local smoke tests.  Production
    execution uses the staged ``a4_remote_ranker`` module and never receives
    an evaluator or protected input path.
    """

    request = validate_a4_worker_request(_load_json(request_path, "A4 worker request"))
    assets = _directory(assets_root, "A4 assets")
    _validate_inventory(assets / "A4_RUNTIME_ASSETS.json", assets, request)
    destination = Path(output_root).resolve()
    if destination.exists() or destination.is_symlink():
        raise A4RemoteWorkerError("A4 output root already exists")
    destination.mkdir(parents=True, exist_ok=False)
    temporary = destination / ".ranker-result.json"
    try:
        command = [
            sys.executable,
            "-m",
            "myis_research.armindex.a4_remote_ranker",
            "--request",
            str(Path(request_path).resolve(strict=True)),
            "--assets-root",
            str(assets),
            "--result",
            str(temporary),
        ]
        (ranker_runner or _run_ranker)(command)
        raw = _load_json(temporary, "A4 ranker result")
        package = _build_package(request, raw)
        _write_json(destination / "ranking-package.json", package)
        completion = _completion_receipt(request, package)
        _write_json(destination / "completion-receipt.json", completion)
        return completion
    except (OSError, ValueError, subprocess.SubprocessError, A4RemoteRankerError) as error:
        _write_failure_marker(destination)
        raise A4RemoteWorkerError("A4 remote worker failed") from error
    finally:
        temporary.unlink(missing_ok=True)


def validate_a4_worker_request(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a request without exposing any protected payload."""

    item = dict(value)
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4RemoteWorkerError("A4 request contains protected payload") from error
    if set(item) != _REQUEST_REQUIRED or item.get("schema_version") != "myis.armindex-a4-remote-profile-request.v1":
        raise A4RemoteWorkerError("A4 worker request schema is invalid")
    if not isinstance(item["attempt_id"], str) or not item["attempt_id"].startswith("a4-goal001-"):
        raise A4RemoteWorkerError("A4 worker request attempt is invalid")
    if item["candidate_depth"] != 100 or item["mode"] not in {"synchronous", "asynchronous"}:
        raise A4RemoteWorkerError("A4 worker request configuration drift")
    arms = item["arm_ids"]
    if not isinstance(arms, list) or not arms or any(arm not in {"ARM-01", "ARM-03", "ARM-04", "ARM-05"} for arm in arms):
        raise A4RemoteWorkerError("A4 worker arm scope is invalid")
    if item["license_scope"] == "commercial_capable" and "ARM-03" in arms:
        raise A4RemoteWorkerError("research-only ARM-03 entered commercial profile")
    if item["profile_id"] == "ARM-03_RESEARCH_REFERENCE" and arms != ["ARM-03"]:
        raise A4RemoteWorkerError("research reference scope is invalid")
    _self_hash(item, "request_sha256", "A4 worker request")
    return item


def validate_a4_completion_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(value)
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4RemoteWorkerError("A4 completion contains protected payload") from error
    required = {
        "schema_version", "status", "attempt_id", "request_sha256", "ranking_sha256",
        "coverage", "latency", "qrels_opened", "membership_opened", "protected_payload_included",
        "ranking_embedded", "receipt_sha256",
    }
    if set(item) != required or item.get("schema_version") != "myis.armindex-a4-remote-completion-receipt.v1":
        raise A4RemoteWorkerError("A4 completion receipt schema is invalid")
    if item.get("status") != "PASS_A4_REMOTE_RETRIEVAL_READY_FOR_OWNER_EVALUATION":
        raise A4RemoteWorkerError("A4 completion status is invalid")
    if any(item.get(field) is not False for field in ("qrels_opened", "membership_opened", "protected_payload_included", "ranking_embedded")):
        raise A4RemoteWorkerError("A4 worker crossed protected boundary")
    coverage = item.get("coverage")
    if not isinstance(coverage, Mapping) or coverage.get("expected_units") != 100 or coverage.get("completed_units") != 100:
        raise A4RemoteWorkerError("A4 completion coverage is incomplete")
    for field in ("request_sha256", "ranking_sha256", "receipt_sha256"):
        _require_sha256(item.get(field), field)
    _self_hash(item, "receipt_sha256", "A4 completion receipt")
    return item


def validate_a4_ranking_package(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the aggregate-safe package consumed by the Owner evaluator."""

    item = dict(value)
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4RemoteWorkerError("A4 ranking package contains protected payload") from error
    required = {"schema_version", "status", "attempt_id", "request_sha256", "rankings", "coverage", "latency", "resource", "protected_payload_included", "ranking_sha256"}
    if set(item) != required or item.get("schema_version") != "myis.armindex-a4-remote-ranking-package.v1" or item.get("status") != "PASS_A4_REMOTE_RANKING_PACKAGE":
        raise A4RemoteWorkerError("A4 ranking package schema is invalid")
    if item.get("protected_payload_included") is not False or not isinstance(item.get("rankings"), Mapping) or len(item["rankings"]) != 100:
        raise A4RemoteWorkerError("A4 ranking package coverage or boundary is invalid")
    coverage = item.get("coverage")
    if not isinstance(coverage, Mapping) or coverage.get("expected_units") != 100 or coverage.get("completed_units") != 100:
        raise A4RemoteWorkerError("A4 ranking package coverage is incomplete")
    _require_sha256(item.get("request_sha256"), "request_sha256")
    _self_hash(item, "ranking_sha256", "A4 ranking package")
    return item


def _build_package(request: Mapping[str, Any], raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != {"rankings", "coverage", "latency", "resource"}:
        raise A4RemoteWorkerError("A4 ranker output schema is invalid")
    try:
        assert_aggregate_only(raw)
    except ValueError as error:
        raise A4RemoteWorkerError("A4 ranker output contains protected payload") from error
    coverage = raw["coverage"]
    rankings = raw["rankings"]
    if not isinstance(coverage, Mapping) or coverage.get("expected_units") != 100 or coverage.get("completed_units") != 100:
        raise A4RemoteWorkerError("A4 ranker coverage is incomplete")
    if not isinstance(rankings, Mapping) or len(rankings) != 100:
        raise A4RemoteWorkerError("A4 ranker output does not cover HDEV-100")
    body = {
        "schema_version": "myis.armindex-a4-remote-ranking-package.v1",
        "status": "PASS_A4_REMOTE_RANKING_PACKAGE",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "rankings": rankings,
        "coverage": dict(coverage),
        "latency": dict(raw["latency"]),
        "resource": dict(raw["resource"]),
        "protected_payload_included": False,
    }
    return {**body, "ranking_sha256": canonical_sha256(body)}


def _completion_receipt(request: Mapping[str, Any], package: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a4-remote-completion-receipt.v1",
        "status": "PASS_A4_REMOTE_RETRIEVAL_READY_FOR_OWNER_EVALUATION",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "ranking_sha256": package["ranking_sha256"],
        "coverage": package["coverage"],
        "latency": package["latency"],
        "qrels_opened": False,
        "membership_opened": False,
        "protected_payload_included": False,
        "ranking_embedded": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _validate_inventory(path: Path, assets: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    inventory = _load_json(path, "A4 runtime inventory")
    if inventory.get("schema_version") != "myis.armindex-a4-runtime-assets-inventory.v1":
        raise A4RemoteWorkerError("A4 inventory identity is invalid")
    if inventory.get("attempt_id") != request["attempt_id"] or inventory.get("profile_registry_sha256") != request["profile_registry_sha256"]:
        raise A4RemoteWorkerError("A4 inventory is not bound to request")
    if inventory.get("protected_payload_included") is not False:
        raise A4RemoteWorkerError("A4 inventory crosses protected boundary")
    _self_hash(inventory, "inventory_sha256", "A4 runtime inventory")
    expected = inventory.get("asset_sha256s")
    if not isinstance(expected, Mapping):
        raise A4RemoteWorkerError("A4 inventory asset hashes are invalid")
    entries = list(assets.rglob("*"))
    if any(path.is_symlink() for path in entries):
        raise A4RemoteWorkerError("A4 inventory contains symbolic link")
    observed = {path.relative_to(assets).as_posix(): file_sha256(path) for path in entries if path.is_file() and path.name != "A4_RUNTIME_ASSETS.json"}
    if dict(expected) != observed:
        raise A4RemoteWorkerError("A4 inventory asset hash drift")
    return inventory


def _run_ranker(arguments: Sequence[str]) -> None:
    subprocess.run(list(arguments), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _load_json(path: Path, role: str) -> dict[str, Any]:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_file():
        raise A4RemoteWorkerError(f"{role} is unsafe")
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A4RemoteWorkerError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A4RemoteWorkerError(f"{role} is invalid")
    return value


def _directory(path: Path, role: str) -> Path:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_dir():
        raise A4RemoteWorkerError(f"{role} is unsafe")
    return candidate


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(canonical_json(value) + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _write_failure_marker(root: Path) -> None:
    try:
        (root / "worker.failure").write_text("FAIL\n", encoding="ascii")
    except OSError:
        pass


def _require_sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise A4RemoteWorkerError(f"{field} must be SHA-256")


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    _require_sha256(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4RemoteWorkerError(f"{role} self-hash mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a4-remote-worker")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(canonical_json(execute_a4_remote_worker(args.request, assets_root=args.assets_root, output_root=args.output_root)))
    return 0


__all__ = ["A4RemoteWorkerError", "execute_a4_remote_worker", "validate_a4_completion_receipt", "validate_a4_ranking_package", "validate_a4_worker_request"]


if __name__ == "__main__":
    raise SystemExit(main())
