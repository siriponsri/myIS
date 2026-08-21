"""Build and validate a fresh opaque A4 Selection-125 runtime package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_asset_bundle import (
    build_a4_selection_runtime_package,
    validate_a4_selection_runtime_package,
)
from myis_research.kernel.canonical import canonical_json


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-prepare-a4-selection-runtime-bundle")
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--predecessor-binding", required=True, type=Path)
    parser.add_argument("--profile-registry", required=True, type=Path)
    parser.add_argument("--hdev-package", required=True, type=Path)
    parser.add_argument("--selection-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = build_a4_selection_runtime_package(
        hdev_package_root=args.hdev_package,
        selection_input_root=args.selection_input,
        output_root=args.output,
        attempt_id=args.attempt_id,
        predecessor_binding=_load(args.predecessor_binding),
        profile_registry=_load(args.profile_registry),
    )
    checked = validate_a4_selection_runtime_package(args.output, expected_attempt_id=args.attempt_id)
    print(canonical_json({"status": checked["status"], "receipt_sha256": receipt["receipt_sha256"], "query_count": checked["selection_query_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
