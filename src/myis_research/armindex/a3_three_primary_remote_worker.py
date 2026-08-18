"""Remote-only worker for one receipt-bound three-primary A3 operation.

The worker has no evaluator and cannot open qrels or split membership.  A
hash-bound executable in the opaque asset bundle performs retrieval, writes a
transient ranking result under the isolated remote root, and this worker
normalizes it through the A3 remote-ranking contract.  Only the ranking package
is eligible to return to the Owner-local evaluator.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256
from ..protection import assert_aggregate_only
from .a3_three_primary_remote_retriever import (
    A3ThreePrimaryRemoteRetrieverError,
    run_remote_retrieval_cell,
    validate_remote_cell_request,
)


_INVENTORY_KEYS = {
    "schema_version",
    "remote_asset_sha256s",
    "ranker_command",
    "inventory_sha256",
}
_COMPLETION_KEYS = {
    "schema_version",
    "status",
    "operation_id",
    "request_sha256",
    "ranking_sha256",
    "ranking_package_receipt_sha256",
    "coverage",
    "latency",
    "qrels_opened",
    "membership_opened",
    "rankings_embedded",
    "protected_payload_included",
    "receipt_sha256",
}


class A3ThreePrimaryRemoteWorkerError(ValueError):
    """Raised when the remote retrieval boundary cannot be safely executed."""


def execute_a3_remote_worker(
    request_path: Path,
    *,
    assets_root: Path,
    output_root: Path,
    ranker_runner: Callable[[Sequence[str]], None] | None = None,
) -> dict[str, Any]:
    """Run a bound ranker and emit a transient package plus safe completion.

    The ranker is invoked with opaque paths and writes JSON to a local temporary
    file.  Its stdout and stderr are never relayed into a receipt.  It must
    return only ``rankings``, ``coverage``, and ``latency``; unexpected fields,
    including qrels or membership, fail closed in the package validator.
    """

    request = validate_remote_cell_request(_load_json(request_path, role="remote request"))
    assets = assets_root.resolve(strict=True)
    if assets.is_symlink() or not assets.is_dir():
        raise A3ThreePrimaryRemoteWorkerError("assets root is unsafe")
    inventory = _validate_inventory(
        _load_json(assets / "A3_RUNTIME_ASSETS.json", role="runtime asset inventory"),
        assets_root=assets,
        expected_assets=request["remote_asset_sha256s"],
    )
    destination = output_root.resolve()
    if destination.exists() or destination.is_symlink():
        raise A3ThreePrimaryRemoteWorkerError("remote operation output already exists")
    destination.mkdir(parents=True, exist_ok=False)
    temporary = destination / ".ranker-result.json"
    try:
        command = [
            *inventory["ranker_command"],
            "--request",
            str(request_path.resolve(strict=True)),
            "--assets-root",
            str(assets),
            "--result",
            str(temporary),
        ]
        (ranker_runner or _run_ranker)(command)
        raw = _load_json(temporary, role="ranker result")
        package = run_remote_retrieval_cell(request, ranker=lambda _request: raw)
        _write_json(destination / "ranking-package.json", package)
        completion = _completion_receipt(package)
        _write_json(destination / "completion-receipt.json", completion)
        return completion
    except (OSError, ValueError, A3ThreePrimaryRemoteRetrieverError, subprocess.SubprocessError) as error:
        _write_failure_marker(destination)
        raise A3ThreePrimaryRemoteWorkerError("A3 remote worker failed") from error
    finally:
        temporary.unlink(missing_ok=True)


def validate_a3_remote_completion_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the aggregate-safe worker completion receipt."""

    receipt = _aggregate_copy(value, role="remote completion receipt")
    if set(receipt) != _COMPLETION_KEYS:
        raise A3ThreePrimaryRemoteWorkerError("remote completion receipt fields are incomplete")
    if (
        receipt["schema_version"] != "myis.armindex-a3-three-primary-remote-completion-receipt.v1"
        or receipt["status"] != "PASS_A3_REMOTE_RETRIEVAL_READY_FOR_OWNER_EVALUATION"
        or receipt["qrels_opened"] is not False
        or receipt["membership_opened"] is not False
        or receipt["rankings_embedded"] is not False
        or receipt["protected_payload_included"] is not False
    ):
        raise A3ThreePrimaryRemoteWorkerError("remote completion receipt identity is invalid")
    for field in ("request_sha256", "ranking_sha256", "ranking_package_receipt_sha256"):
        _require_sha256(receipt[field], field)
    _validate_coverage(receipt["coverage"])
    _validate_latency(receipt["latency"])
    _self_hash(receipt, "receipt_sha256", role="remote completion receipt")
    return receipt


def _validate_inventory(
    value: Mapping[str, Any], *, assets_root: Path, expected_assets: Mapping[str, Any]
) -> dict[str, Any]:
    inventory = _aggregate_copy(value, role="runtime asset inventory")
    if set(inventory) - (_INVENTORY_KEYS | {"package_bindings"}) or inventory["schema_version"] != "myis.armindex-a3-runtime-assets-inventory.v1":
        raise A3ThreePrimaryRemoteWorkerError("runtime asset inventory fields are incomplete")
    if inventory["remote_asset_sha256s"] != expected_assets:
        raise A3ThreePrimaryRemoteWorkerError("runtime asset inventory is not bound to the request")
    command = inventory["ranker_command"]
    if not isinstance(command, list) or not command or any(not isinstance(part, str) or not part for part in command):
        raise A3ThreePrimaryRemoteWorkerError("runtime ranker command is invalid")
    _self_hash(inventory, "inventory_sha256", role="runtime asset inventory")
    # Enforce the frozen local-only model contract for the child ranker.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    executable = (assets_root / command[0]).resolve(strict=True)
    if executable.is_symlink() or not executable.is_file() or not executable.is_relative_to(assets_root):
        raise A3ThreePrimaryRemoteWorkerError("runtime ranker executable must remain inside opaque assets")
    return {**inventory, "ranker_command": [str(executable), *command[1:]]}


def _completion_receipt(package: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a3-three-primary-remote-completion-receipt.v1",
        "status": "PASS_A3_REMOTE_RETRIEVAL_READY_FOR_OWNER_EVALUATION",
        "operation_id": package["operation_id"],
        "request_sha256": package["request_sha256"],
        "ranking_sha256": package["ranking_sha256"],
        "ranking_package_receipt_sha256": package["receipt_sha256"],
        "coverage": package["coverage"],
        "latency": package["latency"],
        "qrels_opened": False,
        "membership_opened": False,
        "rankings_embedded": False,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _run_ranker(arguments: Sequence[str]) -> None:
    subprocess.run(list(arguments), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise A3ThreePrimaryRemoteWorkerError(f"{role} is not a regular file")
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise A3ThreePrimaryRemoteWorkerError(f"{role} is not valid JSON") from error
    if not isinstance(value, dict):
        raise A3ThreePrimaryRemoteWorkerError(f"{role} must be an object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    serialized = canonical_json(dict(value)) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(serialized)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _write_failure_marker(root: Path) -> None:
    try:
        root.mkdir(parents=True, exist_ok=True)
        (root / "worker.failure").write_text("FAIL\n", encoding="ascii")
    except OSError:
        pass


def _aggregate_copy(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A3ThreePrimaryRemoteWorkerError(f"{role}: {error}") from error
    return result


def _validate_coverage(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != {"expected_units", "completed_units"} or value["expected_units"] != value["completed_units"]:
        raise A3ThreePrimaryRemoteWorkerError("remote completion coverage is incomplete")


def _validate_latency(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != {"wall_seconds", "search_p95_seconds"}:
        raise A3ThreePrimaryRemoteWorkerError("remote completion latency is invalid")


def _require_sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise A3ThreePrimaryRemoteWorkerError(f"{field} must be SHA-256")


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    _require_sha256(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A3ThreePrimaryRemoteWorkerError(f"{role} self-hash does not bind its contents")


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a3-three-primary-remote-worker")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--assets-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    receipt = execute_a3_remote_worker(args.request, assets_root=args.assets_root, output_root=args.output_root)
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
