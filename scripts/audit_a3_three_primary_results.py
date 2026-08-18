"""Audit the completed A3 batch using aggregate-safe output only.

The audit revalidates the exact 14-operation request, ranking-return lineage,
aggregate result receipts, fixed-control/transfer coverage, HarnessOpt
boundary, and safe return.  It writes no rankings, qrels, membership, or
per-query outcomes.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a3_three_primary_owner_evaluator import validate_aggregate_result
from myis_research.armindex.a3_three_primary_remote_launcher import (
    validate_a3_remote_stage_manifest,
    validate_a3_remote_stage_receipt,
    validate_a3_transient_ranking_return_receipt,
)
from myis_research.armindex.a3_three_primary_remote_retriever import (
    validate_remote_cell_request,
    validate_remote_ranking_package,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.protection import assert_aggregate_only


PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
FIXED_OPERATIONS = (
    "fixed-all-primary-rrf60",
    "fixed-best-single",
    "fixed-commercial-only-fixed-union",
    "fixed-top-three-rrf60",
    "fixed-top-two-rrf60",
)
TRANSFER_OPERATIONS = tuple(
    f"transfer-arm-{source[-2:]}-to-arm-{target[-2:]}"
    for source in PRIMARY_ARMS
    for target in PRIMARY_ARMS
)
EXPECTED_OPERATIONS = frozenset((*FIXED_OPERATIONS, *TRANSFER_OPERATIONS))


class A3ResultAuditError(ValueError):
    """Raised when the completed A3 evidence is not internally consistent."""


def audit_a3_results(
    *,
    owner_store_root: Path,
    stage_manifest_path: Path,
    stage_receipt_path: Path,
    runtime_bindings_path: Path,
    requests_dir: Path,
    rankings_dir: Path,
    return_receipts_dir: Path,
    aggregate_results_dir: Path,
    safe_return_path: Path,
    harnessopt_evaluation_path: Path,
) -> dict[str, Any]:
    root = owner_store_root.resolve(strict=True)
    stage = validate_a3_remote_stage_receipt(_load(stage_receipt_path, "stage receipt"))
    manifest = validate_a3_remote_stage_manifest(_load(stage_manifest_path, "stage manifest"))
    if stage["stage_manifest_sha256"] != manifest["stage_manifest_sha256"]:
        raise A3ResultAuditError("stage receipt does not bind the stage manifest")
    runtime = _load(runtime_bindings_path, "runtime bindings")
    _validate_runtime(runtime)
    if runtime["runtime_bindings_sha256"] != manifest["runtime_bindings_sha256"]:
        raise A3ResultAuditError("runtime binding drift")

    paths = {
        "requests": requests_dir,
        "rankings": rankings_dir,
        "return receipts": return_receipts_dir,
        "aggregate results": aggregate_results_dir,
    }
    for role, path in paths.items():
        _inside(root, path, role)
    request_paths = _json_files(requests_dir, "requests")
    ranking_paths = _json_files(rankings_dir, "rankings")
    return_paths = _json_files(return_receipts_dir, "return receipts")
    aggregate_paths = {
        path.name.removesuffix(".aggregate-result.json"): path
        for path in aggregate_results_dir.glob("*.aggregate-result.json")
    }
    if any(path.is_symlink() or not path.is_file() for path in aggregate_results_dir.glob("*.aggregate-result.json")):
        raise A3ResultAuditError("aggregate result directory contains an unsafe file")
    if any(set(values) != EXPECTED_OPERATIONS for values in (request_paths, ranking_paths, return_paths, aggregate_paths)):
        raise A3ResultAuditError("A3 evidence does not contain exactly 14 operations")

    aggregate_receipts: dict[str, str] = {}
    metrics: dict[str, Any] = {}
    for operation_id in sorted(EXPECTED_OPERATIONS):
        request = validate_remote_cell_request(_load(request_paths[operation_id], "remote request"))
        ranking = validate_remote_ranking_package(_load(ranking_paths[operation_id], "ranking package"))
        returned = validate_a3_transient_ranking_return_receipt(_load(return_paths[operation_id], "return receipt"))
        aggregate = validate_aggregate_result(_load(aggregate_paths[operation_id], "aggregate result"))
        if request["operation_id"] != operation_id or ranking["operation_id"] != operation_id or returned["operation_id"] != operation_id or aggregate["operation_id"] != operation_id:
            raise A3ResultAuditError("operation identity drift")
        if returned["request_sha256"] != request["request_sha256"] or returned["ranking_sha256"] != ranking["ranking_sha256"]:
            raise A3ResultAuditError("return receipt lineage drift")
        if returned["ranking_package_receipt_sha256"] != ranking["receipt_sha256"] or returned["ranking_package_file_sha256"] != file_sha256(ranking_paths[operation_id]):
            raise A3ResultAuditError("ranking package file lineage drift")
        if aggregate["request_sha256"] != request["request_sha256"] or aggregate["ranking_sha256"] != ranking["ranking_sha256"]:
            raise A3ResultAuditError("aggregate result lineage drift")
        if aggregate["coverage"]["expected_units"] != 250 or aggregate["coverage"]["completed_units"] != 250:
            raise A3ResultAuditError("Train-250 aggregate coverage is incomplete")
        aggregate_receipts[operation_id] = aggregate["receipt_sha256"]
        metrics[operation_id] = {
            "metrics": aggregate["metrics"],
            "latency": aggregate["latency"],
            "coverage": aggregate["coverage"],
        }

    safe = _load(safe_return_path, "safe return")
    if safe.get("status") != "PASS_A3_AGGREGATE_SAFE_RETURN" or safe.get("aggregate_result_count") != 14 or safe.get("rankings_returned") is not False or safe.get("protected_payload_included") is not False or safe.get("per_query_outcomes_included") is not False:
        raise A3ResultAuditError("safe return boundary drift")
    if safe.get("aggregate_result_receipt_sha256s") != aggregate_receipts or safe.get("receipt_sha256") != canonical_sha256({key: value for key, value in safe.items() if key != "receipt_sha256"}):
        raise A3ResultAuditError("safe return receipt lineage drift")

    harness = _load(harnessopt_evaluation_path, "HarnessOpt evaluation")
    if harness.get("status") != "PASS_A3_HARNESSOPT_FLAT_SURFACE" or harness.get("complete_batch_count") != 3 or harness.get("candidate_count") != 12 or harness.get("unique_action_signature_count") != 1 or harness.get("protected_payload_included") is not False or harness.get("per_query_outcomes_included") is not False:
        raise A3ResultAuditError("HarnessOpt boundary drift")
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-three-primary-result-integrity-audit.v1",
        "status": "PASS_A3_RESULT_INTEGRITY_AUDIT",
        "attempt_id": stage["attempt_id"],
        "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
        "stage_manifest_sha256": manifest["stage_manifest_sha256"],
        "stage_receipt_sha256": stage["receipt_sha256"],
        "operation_count": 14,
        "transfer_operation_count": len(TRANSFER_OPERATIONS),
        "fixed_operation_count": len(FIXED_OPERATIONS),
        "train250_expected_units": 250,
        "aggregate_result_receipt_sha256s": aggregate_receipts,
        "metrics_and_latency": metrics,
        "safe_return_receipt_sha256": safe["receipt_sha256"],
        "harnessopt_evaluation_sha256": harness["evaluation_sha256"],
        "protected_payload_included": False,
        "rankings_included": False,
        "per_query_outcomes_included": False,
    }
    assert_aggregate_only(body)
    return {**body, "audit_sha256": canonical_sha256(body)}


def _validate_runtime(value: Mapping[str, Any]) -> None:
    required = {"schema_version", "primary_arm_scope", "runtime_bindings_sha256"}
    if not required.issubset(value) or value["schema_version"] != "myis.armindex-a3-three-primary-runtime-bindings.v1" or value["primary_arm_scope"] != list(PRIMARY_ARMS):
        raise A3ResultAuditError("runtime bindings are invalid")
    if value["runtime_bindings_sha256"] != canonical_sha256({key: item for key, item in value.items() if key != "runtime_bindings_sha256"}):
        raise A3ResultAuditError("runtime bindings self-hash drift")


def _json_files(path: Path, role: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in path.glob("*.json"):
        if item.is_symlink() or not item.is_file() or item.stem in result:
            raise A3ResultAuditError(f"{role} contains an unsafe file")
        result[item.stem] = item
    return result


def _inside(root: Path, path: Path, role: str) -> None:
    resolved = path.resolve(strict=True)
    if resolved == root or root not in resolved.parents:
        raise A3ResultAuditError(f"{role} escapes Owner Store")


def _load(path: Path, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.resolve(strict=True).read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A3ResultAuditError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A3ResultAuditError(f"{role} must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--stage-manifest", type=Path, required=True)
    parser.add_argument("--stage-receipt", type=Path, required=True)
    parser.add_argument("--runtime-bindings", type=Path, required=True)
    parser.add_argument("--requests-dir", type=Path, required=True)
    parser.add_argument("--rankings-dir", type=Path, required=True)
    parser.add_argument("--return-receipts-dir", type=Path, required=True)
    parser.add_argument("--aggregate-results-dir", type=Path, required=True)
    parser.add_argument("--safe-return", type=Path, required=True)
    parser.add_argument("--harnessopt-evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_a3_results(
        owner_store_root=args.owner_store_root,
        stage_manifest_path=args.stage_manifest,
        stage_receipt_path=args.stage_receipt,
        runtime_bindings_path=args.runtime_bindings,
        requests_dir=args.requests_dir,
        rankings_dir=args.rankings_dir,
        return_receipts_dir=args.return_receipts_dir,
        aggregate_results_dir=args.aggregate_results_dir,
        safe_return_path=args.safe_return,
        harnessopt_evaluation_path=args.harnessopt_evaluation,
    )
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise SystemExit("audit output already exists")
    _inside(args.owner_store_root.resolve(strict=True), output.parent, "audit output")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
    print(json.dumps({"status": result["status"], "audit_sha256": result["audit_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
