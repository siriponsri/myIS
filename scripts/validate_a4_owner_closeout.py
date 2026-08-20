"""Validate aggregate-safe A4 closeout evidence in Owner Store.

This validator never opens ranking packages, qrels, membership, or per-query
outcomes. It checks only the aggregate receipts required before Selection or
conditional D2 can be considered.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_evaluator import validate_a4_profile_result
from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


ATTEMPT_ID = "a4-goal001-20260819T180000Z-a4x12"
PROFILES = ("FAST", "BALANCED", "DEEP", "ARM-03_RESEARCH_REFERENCE")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _self_hash(value: dict[str, Any], field: str, role: str) -> None:
    observed = value.get(field)
    expected = canonical_sha256({key: item for key, item in value.items() if key != field})
    if observed != expected:
        raise ValueError(f"{role} self-hash mismatch")


def build_audit(root: Path) -> dict[str, Any]:
    evaluations = {
        profile: _load(root / "hdev-evaluations" / f"{profile}.json")
        for profile in PROFILES
    }
    checked = [validate_a4_profile_result(value) for value in evaluations.values()]
    if {item["profile_id"] for item in checked} != set(PROFILES):
        raise ValueError("A4 evaluation set is incomplete")
    for item in checked:
        if item["attempt_id"] != ATTEMPT_ID:
            raise ValueError("A4 attempts are mixed")
        if item["coverage"] != {"expected_units": 100, "completed_units": 100}:
            raise ValueError(f"{item['profile_id']} coverage is incomplete")
        if item["failures"] != 0 or item["determinism"] is not True:
            raise ValueError(f"{item['profile_id']} is not deterministic and complete")

    coverage = _load(root / "hdev-evaluations" / "A4_COMPLETE_PROFILE_COVERAGE.json")
    _self_hash(coverage, "receipt_sha256", "A4 coverage receipt")
    if coverage.get("status") != "PASS_A4_COMPLETE_PROFILE_COVERAGE":
        raise ValueError("A4 coverage receipt is not PASS")
    if coverage.get("commercial_profile_count") != 3 or coverage.get("research_reference_count") != 1:
        raise ValueError("A4 coverage receipt does not include all four measurements")
    if coverage.get("protected_payload_included") is not False:
        raise ValueError("A4 coverage crossed the protected boundary")

    legal = _load(root / "hdev-evaluations" / "A4_LEGAL_TRANSFER.json")
    if legal.get("status") != "PASS_A4_LEGAL_TRANSFER_ISOLATED":
        raise ValueError("legal transfer isolation is not PASS")
    if legal.get("selection_accesses") != 0 or legal.get("final_accesses") != 0:
        raise ValueError("legal transfer changed gated counters")
    if legal.get("protected_payload_included") is not False or legal.get("patent_retuning") is not False:
        raise ValueError("legal transfer crossed an isolation boundary")

    frontier = _load(root / "hdev-evaluations" / "A4_COMMERCIAL_FRONTIER.json")
    if frontier.get("status") != "PASS_A4_NON_DOMINATED_FRONTIER":
        raise ValueError("commercial frontier receipt is not PASS")
    assert_aggregate_only(frontier)

    return {
        "schema_version": "myis.armindex-a4-result-integrity-audit.v1",
        "status": "PASS_A4_RESULT_INTEGRITY_AUDIT",
        "attempt_id": ATTEMPT_ID,
        "profile_ids": list(PROFILES),
        "profile_receipt_sha256": {
            profile: evaluations[profile]["receipt_sha256"] for profile in PROFILES
        },
        "coverage_receipt_sha256": coverage["receipt_sha256"],
        "legal_transfer_receipt_sha256": legal["receipt_sha256"],
        "commercial_frontier_receipt_sha256": frontier["receipt_sha256"],
        "all_profile_coverage_complete": True,
        "all_profile_failures_zero": True,
        "all_profile_deterministic": True,
        "legal_transfer_isolated": True,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "claim_boundary": "A4 aggregate integrity only; Selection and Final evidence do not exist.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    body = build_audit(args.root)
    result = {**body, "audit_sha256": canonical_sha256(body)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refusing to overwrite {args.output}")
    args.output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"status": result["status"], "audit_sha256": result["audit_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
