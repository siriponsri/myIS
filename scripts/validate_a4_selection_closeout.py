"""Validate aggregate-safe fresh A4 Selection-125 return and closeout.

This is intentionally separate from the historical HDEV-100 validator. It
opens only Owner-Store ranking packages and emits hashes, counts, resources,
and teardown evidence; protected qrels/membership never leave Owner Store.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_selection_evaluator import _validate_package
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256
from myis_research.protection import assert_aggregate_only


PROFILES = ("FAST", "BALANCED", "DEEP", "ARM-03_RESEARCH_REFERENCE")
SCOPE_SHA256 = "c56dac147aa985162b89181e864e2fe9418334e553159d18909958bc7c9e3a11"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write(path: Path, value: dict[str, Any]) -> dict[str, Any]:
    if path.exists() or path.is_symlink():
        raise ValueError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    selection = _load(args.selection_receipt.resolve(strict=True))
    if selection.get("status") != "PASS_A4_SELECTION_EXPOSED_ONCE" or selection.get("selection_accesses") != 1 or selection.get("final_accesses") != 0:
        raise ValueError("Selection receipt is not a valid one-shot PASS")
    attempt_id = root.name
    packages: dict[str, dict[str, Any]] = {}
    refs: dict[str, dict[str, Any]] = {}
    for profile in PROFILES:
        package_path = root / "selection-return" / f"{profile}-selection" / "ranking-package.json"
        package = _validate_package(_load(package_path), expected_scope_hash=SCOPE_SHA256, attempt_id=attempt_id)
        if package["coverage"] != {"expected_units": 125, "completed_units": 125} or package["failures"] != 0 or package["determinism"] is not True:
            raise ValueError(f"{profile} is incomplete or non-deterministic")
        packages[profile] = package
        refs[profile] = {
            "profile_id": profile,
            "package_sha256": file_sha256(package_path),
            "ranking_sha256": package["ranking_sha256"],
            "request_sha256": package["request_sha256"],
            "coverage": package["coverage"],
            "latency": package["latency"],
            "resource": package["resource"],
            "failures": package["failures"],
            "determinism": package["determinism"],
        }
    legal_path = root / "selection-closeout-v2" / "A4_LEGAL_TRANSFER.json"
    if not legal_path.is_file() or legal_path.is_symlink():
        raise ValueError("Selection attempt is missing isolated legal-transfer receipt")
    legal = _load(legal_path)
    if legal.get("schema_version") != "myis.armindex-a4-legal-transfer-receipt.v1":
        raise ValueError("legal-transfer receipt schema is invalid")
    if legal.get("status") != "PASS_A4_LEGAL_TRANSFER_ISOLATED":
        raise ValueError("legal-transfer isolation is not PASS")
    if legal.get("attempt_id") != attempt_id:
        raise ValueError("legal-transfer attempt identity is mixed")
    if legal.get("mini", {}).get("status") != "UNSUPPORTED":
        raise ValueError("Selection legal mini must preserve the unsupported status")
    if legal.get("full", {}).get("status") != "NOT_RUN":
        raise ValueError("Selection legal full transfer must remain not run")
    if legal.get("selection_accesses") != 0 or legal.get("final_accesses") != 0:
        raise ValueError("legal-transfer receipt changed gated counters")
    if legal.get("patent_retuning") is not False or legal.get("protected_payload_included") is not False:
        raise ValueError("legal-transfer receipt crossed an isolation boundary")
    coverage_body = {
        "schema_version": "myis.armindex-a4-selection-coverage-receipt.v1",
        "status": "PASS_A4_SELECTION_COMPLETE_PROFILE_COVERAGE",
        "attempt_id": attempt_id,
        "selection_scope_sha256": SCOPE_SHA256,
        "selection_query_count": 125,
        "evaluated_out_query_count": 90,
        "profiles": refs,
        "legal_transfer_receipt_sha256": file_sha256(legal_path),
        "legal_transfer_status": legal["mini"]["status"],
        "selection_accesses": 1,
        "final_accesses": 0,
        "protected_payload_included": False,
        "claim_boundary": "Fresh Selection-125 package coverage only; no Final result.",
    }
    coverage = {**coverage_body, "receipt_sha256": canonical_sha256(coverage_body)}
    safe_body = {
        "schema_version": "myis.armindex-a4-selection-safe-return-receipt.v1",
        "status": "PASS_A4_SELECTION_SAFE_RETURN",
        "attempt_id": attempt_id,
        "coverage_receipt_sha256": coverage["receipt_sha256"],
        "returned_profiles": list(PROFILES),
        "remote_workers_teardown_verified": True,
        "selection_accesses": 1,
        "final_accesses": 0,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
        "claim_boundary": "Aggregate-safe return of hash-bound Selection packages; protected evaluator inputs remain Owner-local.",
    }
    safe = {**safe_body, "receipt_sha256": canonical_sha256(safe_body)}
    audit_body = {
        "schema_version": "myis.armindex-a4-selection-result-integrity-audit.v1",
        "status": "PASS_A4_SELECTION_RESULT_INTEGRITY_AUDIT",
        "attempt_id": attempt_id,
        "coverage_receipt_sha256": coverage["receipt_sha256"],
        "safe_return_receipt_sha256": safe["receipt_sha256"],
        "selection_receipt_sha256": selection["receipt_sha256"],
        "all_profile_coverage_complete": True,
        "all_profile_failures_zero": True,
        "all_profile_deterministic": True,
        "legal_transfer_isolated": True,
        "selection_accesses": 1,
        "final_accesses": 0,
        "protected_payload_included": False,
        "claim_boundary": "A4 Selection aggregate integrity only; A5 Final result does not exist.",
    }
    audit = {**audit_body, "audit_sha256": canonical_sha256(audit_body)}
    for value in (coverage, safe, audit):
        assert_aggregate_only(value)
    out = args.output_root.resolve()
    if out.exists() or out.is_symlink():
        raise ValueError("A4 Selection closeout output root must be fresh")
    out.mkdir(parents=True)
    _write(out / "A4_SELECTION_COVERAGE.json", coverage)
    _write(out / "A4_SELECTION_SAFE_RETURN.json", safe)
    _write(out / "A4_SELECTION_RESULT_INTEGRITY_AUDIT.json", audit)
    print(canonical_json({"status": audit["status"], "audit_sha256": audit["audit_sha256"], "coverage_sha256": coverage["receipt_sha256"], "safe_return_sha256": safe["receipt_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
