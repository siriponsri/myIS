"""Validate the local A6 pending template without permitting materialization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a6_materialization import (
    A6MaterializationError,
    validate_pending_a6_materialization_template,
)
from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json"
DEFAULT_TEMPLATE = ROOT / "control/armindex/a6/a6-pending-a5-closeout-template.v1.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise A6MaterializationError(f"{path} must contain a JSON object")
    return value


def build_validation_receipt(template: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    validated = validate_pending_a6_materialization_template(template, contract)
    body = {
        "schema_version": "myis.armindex-a6-pending-validation-receipt.v1",
        "status": "PASS_A6_PENDING_TEMPLATE_VALIDATED",
        "template_sha256": validated["template_sha256"],
        "a6_contract_sha256": validated["a6_contract_sha256"],
        "authorized_instance_id": validated["authorized_instance_id"],
        "execution_permitted": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "required_aggregate_metrics": validated["required_aggregate_metrics"],
        "claim_boundary": validated["claim_boundary"],
    }
    assert_aggregate_only(body)
    return {**body, "receipt_sha256": canonical_sha256(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_validation_receipt(load_json(args.template), load_json(args.contract))
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
