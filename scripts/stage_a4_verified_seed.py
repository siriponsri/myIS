"""Stage a fresh A4 root from a verified immutable A4 asset seed."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_asset_bundle import validate_a4_hdev_runtime_package
from myis_research.armindex.a4_remote_launcher import (
    build_a4_stage_manifest,
    stage_a4_remote_runtime_from_verified_seed,
)
from myis_research.kernel.canonical import canonical_json, file_sha256


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"A4 staging input is not an object: {path.name}")
    return value


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ValueError(f"A4 staging receipt already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--remote-root", required=True)
    parser.add_argument("--seed-root", required=True)
    parser.add_argument("--runtime-package", type=Path, required=True)
    parser.add_argument("--code-bundle", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    package = args.runtime_package.resolve(strict=True)
    receipt = validate_a4_hdev_runtime_package(package, expected_attempt_id=args.attempt_id)
    runtime = _load(package / "A4_RUNTIME_BINDINGS.json")
    registry = _load(package / "profile-registry.json")
    inventory = _load(package / "assets" / "A4_RUNTIME_ASSETS.json")
    scope = _load(package / "assets" / "hdev-scope.json")
    code_bundle = args.code_bundle.resolve(strict=True)
    manifest = build_a4_stage_manifest(
        attempt_id=args.attempt_id,
        remote_root=args.remote_root,
        runtime_bindings_sha256=runtime["runtime_bindings_sha256"],
        profile_registry_sha256=registry["registry_sha256"],
        code_bundle_sha256=file_sha256(code_bundle),
        runtime_assets_archive_sha256=receipt["archive_sha256"],
        runtime_assets_inventory_sha256=inventory["inventory_sha256"],
        remote_asset_sha256s={
            "asset_inventory": inventory["inventory_sha256"],
            "hdev_scope": scope["scope_sha256"],
            "profile_registry": registry["registry_sha256"],
            "runtime_bindings": runtime["runtime_bindings_sha256"],
        },
    )
    staged = stage_a4_remote_runtime_from_verified_seed(
        manifest,
        code_bundle=code_bundle,
        runtime_bindings=package / "A4_RUNTIME_BINDINGS.json",
        profile_registry=package / "profile-registry.json",
        hdev_scope=package / "assets" / "hdev-scope.json",
        runtime_assets_inventory=package / "assets" / "A4_RUNTIME_ASSETS.json",
        seed_root=args.seed_root,
        ssh_host=args.host,
        ssh_port=args.port,
        ssh_key_path=args.key,
        known_hosts_path=args.known_hosts,
    )
    output = args.output.resolve()
    _write_new(output / "stage-manifest.json", manifest)
    _write_new(output / "stage-receipt.json", staged["stage_receipt"])
    _write_new(output / "verified-seed-receipt.json", staged["seed_receipt"])
    print(
        canonical_json(
            {
                "status": staged["stage_receipt"]["status"],
                "attempt_id": args.attempt_id,
                "stage_receipt_sha256": staged["stage_receipt"]["receipt_sha256"],
                "seed_receipt_sha256": staged["seed_receipt"]["receipt_sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
