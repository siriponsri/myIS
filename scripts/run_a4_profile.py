"""Create and launch one frozen A4 profile operation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_remote_launcher import (
    build_a4_launch_integrity_receipt,
    launch_a4_remote_operation,
)
from myis_research.armindex.a4_remote_ranker import build_a4_profile_request
from myis_research.kernel.canonical import canonical_json


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"A4 input is not a JSON object: {path}")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ValueError(f"A4 receipt already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve(strict=True)
    registry = _load(root / "bundle" / "runtime-package" / "profile-registry.json")
    runtime = _load(root / "bundle" / "runtime-package" / "A4_RUNTIME_BINDINGS.json")
    stage = _load(root / "stage" / "stage-receipt.json")
    request = build_a4_profile_request(
        attempt_id=args.attempt_id,
        profile_registry=registry,
        runtime_bindings=runtime,
        profile_id=args.profile,
    )
    request_path = root / "requests" / f"{args.profile}.json"
    _write(request_path, request)
    integrity = build_a4_launch_integrity_receipt(
        attempt_id=args.attempt_id,
        stage_receipt_sha256=stage["receipt_sha256"],
        request_sha256=request["request_sha256"],
        code_bundle_sha256=stage["code_bundle_sha256"],
        runtime_bindings_sha256=runtime["runtime_bindings_sha256"],
    )
    _write(root / "launch-integrity" / f"{args.profile}.json", integrity)
    launch = launch_a4_remote_operation(
        stage,
        integrity,
        request_path=request_path,
        ssh_host=args.host,
        ssh_port=args.port,
        ssh_key_path=args.key,
        known_hosts_path=args.known_hosts,
    )
    _write(root / "launch-receipts" / f"{args.profile}.json", launch)
    print(canonical_json({
        "profile": args.profile,
        "request_sha256": request["request_sha256"],
        "launch_receipt_sha256": launch["receipt_sha256"],
        "remote_pid": launch["remote_pid"],
        "operation_id": launch["operation_id"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
