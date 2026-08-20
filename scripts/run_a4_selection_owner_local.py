"""Run the one allowed A4 Selection exposure inside the Owner Store only.

The protected input path must contain the paired Selection-125 metric vectors.
This command writes only an aggregate-safe receipt and refuses an existing
receipt path, so it cannot silently rerun Selection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_selection_runner import run_selection_owner_local
from myis_research.kernel.canonical import canonical_json


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--preflight-counter", type=Path, required=True)
    parser.add_argument("--protected-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    args = parser.parse_args()
    owner_root = args.owner_store_root.resolve(strict=True)
    paths = [args.registry, args.preflight_counter, args.protected_input, args.output]
    for path in paths:
        resolved = path.resolve()
        if resolved != owner_root and owner_root not in resolved.parents:
            raise ValueError(f"Selection path is outside Owner Store: {path}")
        if path.is_symlink():
            raise ValueError(f"Selection path cannot be a symlink: {path}")
    receipt = run_selection_owner_local(
        _load(args.registry),
        _load(args.protected_input),
        preflight_counter=_load(args.preflight_counter),
        selection_output_path=args.output,
    )
    print(canonical_json({
        "status": receipt["status"],
        "receipt_sha256": receipt["receipt_sha256"],
        "selection_accesses": receipt["selection_accesses"],
        "final_accesses": receipt["final_accesses"],
        "protected_payload_included": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
