"""Build a contract-only A4 readiness binding from audited A3 evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return value


def build_binding(audit: dict[str, Any], safe_return: dict[str, Any], harness: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    if audit.get("status") != "PASS_A3_RESULT_INTEGRITY_AUDIT":
        raise ValueError("A3 result-integrity audit is not passing")
    if safe_return.get("status") != "PASS_A3_AGGREGATE_SAFE_RETURN" or safe_return.get("aggregate_result_count") != 14:
        raise ValueError("A3 safe return is not complete")
    if harness.get("status") != "PASS_A3_HARNESSOPT_FLAT_SURFACE" or harness.get("candidate_count") != 12:
        raise ValueError("A3 HarnessOpt evidence is not complete")
    if runtime.get("runtime_bindings_sha256") != audit.get("runtime_bindings_sha256"):
        raise ValueError("runtime bindings do not match A3 audit")
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a4-readiness-binding.v1",
        "status": "contract_only_ready",
        "phase_id": "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "a3_attempt_id": audit["attempt_id"],
        "a3_closeout_verified": True,
        "a3_result_integrity_audit_sha256": audit["audit_sha256"],
        "a3_safe_return_receipt_sha256": safe_return["receipt_sha256"],
        "a3_harnessopt_evaluation_sha256": harness["evaluation_sha256"],
        "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
        "winner_program_sha256s": {arm: value["winner_program_sha256"] for arm, value in runtime["winner_bindings"].items()},
        "primary_arm_scope": list(runtime["primary_arm_scope"]),
        "transfer_operation_count": audit["transfer_operation_count"],
        "fixed_control_count": audit["fixed_operation_count"],
        "train250_query_count": audit["train250_expected_units"],
        "harnessopt_complete_batch_count": harness["complete_batch_count"],
        "harnessopt_candidate_count": harness["candidate_count"],
        "harnessopt_unique_action_signature_count": harness["unique_action_signature_count"],
        "selection_permitted": False,
        "final_permitted": False,
        "measured_execution": False,
        "protected_payload_included": False,
        "claim_boundary": "contract_only_a4_readiness_no_production_measurement_no_selection_no_final",
    }
    assert_aggregate_only(body)
    return {**body, "binding_sha256": canonical_sha256(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--safe-return", type=Path, required=True)
    parser.add_argument("--harnessopt", type=Path, required=True)
    parser.add_argument("--runtime-bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_binding(_load(args.audit), _load(args.safe_return), _load(args.harnessopt), _load(args.runtime_bindings))
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("A4 readiness binding already exists")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"status": result["status"], "binding_sha256": result["binding_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
