"""Validate the local A5 pending handoff without opening Selection or Final."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_a5_handoff import (
    A4A5HandoffError,
    validate_pending_a5_handoff_template,
)
from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


def load_template(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise A4A5HandoffError("A5 pending template must be a JSON object")
    return value


def build_validation_receipt(value: dict[str, Any]) -> dict[str, Any]:
    validated = validate_pending_a5_handoff_template(value)
    body = {
        "schema_version": "myis.armindex-a5-pending-validation-receipt.v1",
        "status": "PASS_A5_PENDING_TEMPLATE_VALIDATED",
        "template_sha256": validated["template_sha256"],
        "expected_final_query_count": validated["expected_final_query_count"],
        "execution_permitted": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "claim_boundary": "Validation only; no A4 Selection, D2, Final access, or A5 result exists.",
    }
    assert_aggregate_only(body)
    return {**body, "receipt_sha256": canonical_sha256(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("control/armindex/a5/a5-pending-a4-selection-template.v1.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_validation_receipt(load_template(args.template))
    encoded = json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        if args.output.exists() or args.output.is_symlink():
            raise SystemExit("validation receipt already exists")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="ascii")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
