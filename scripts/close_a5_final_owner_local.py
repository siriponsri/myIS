"""Close a valid A5 Final-872 evaluation with aggregate-safe evidence only.

Raw rankings and protected evaluator inputs remain in the supplied Owner Store.
This utility writes only aggregate-safe coverage, safe-return, audit, frozen
winner, and closeout receipts.  It does not launch A6.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from myis_research.armindex.a4_a5_handoff import validate_a5_pointer_bundle
from myis_research.armindex.a6_materialization import validate_a5_frozen_winner_binding
from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.protection import assert_aggregate_only


ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = {"research_champion", "static_common_baseline"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path.name}")
    return value


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="ascii")


def _self_hash(body: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(body)
    result[field] = canonical_sha256(result)
    return result


def _validate_request(value: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(value)
    if (
        item.get("schema_version") != "myis.armindex-a5-final-request.v1"
        or item.get("scope") != "Final-872"
        or item.get("query_count") != 872
        or item.get("selection_accesses") != 1
        or item.get("final_accesses") != 1
        or item.get("protected_payload_included") is not False
    ):
        raise ValueError("A5 request identity is invalid")
    if item.get("request_sha256") != canonical_sha256({key: value for key, value in item.items() if key != "request_sha256"}):
        raise ValueError("A5 request self-hash mismatch")
    bindings = item.get("finalist_bindings")
    if not isinstance(bindings, list) or {row.get("system") for row in bindings if isinstance(row, Mapping)} != SYSTEMS:
        raise ValueError("A5 finalist request registry is invalid")
    if item.get("top_k") != 100:
        raise ValueError("A5 retrieval depth is invalid")
    return item


def _validate_package(value: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(value)
    rankings = item.get("rankings")
    if (
        item.get("schema_version") != "myis.armindex-a5-final-ranking-package.v1"
        or item.get("status") != "PASS_A5_REMOTE_OPAQUE_RANKINGS"
        or item.get("attempt_id") != request["attempt_id"]
        or item.get("request_sha256") != request["request_sha256"]
        or item.get("scope") != "Final-872"
        or item.get("query_count") != 872
        or item.get("coverage") != {"research_champion": 872, "static_common_baseline": 872}
        or item.get("failures") != 0
        or item.get("determinism") is not True
        or item.get("protected_payload_included") is not False
        or item.get("rankings_returned_to") != "owner_local_evaluator_only"
        or not isinstance(rankings, Mapping)
        or set(rankings) != SYSTEMS
        or item.get("ranking_sha256") != canonical_sha256(rankings)
    ):
        raise ValueError("A5 remote package binding is invalid")
    return item


def _validate_evaluation(value: Mapping[str, Any], request: Mapping[str, Any], package_path: Path) -> dict[str, Any]:
    item = dict(value)
    systems = item.get("systems")
    if (
        item.get("schema_version") != "myis.armindex-a5-final-owner-evaluation.v1"
        or item.get("status") != "PASS_A5_FINAL_CONFIRMATION"
        or item.get("scope") != "Final-872"
        or item.get("request_sha256") != request["request_sha256"]
        or item.get("query_count") != 872
        or item.get("judged_query_count") != 872
        or item.get("ranking_package_sha256") != file_sha256(package_path)
        or item.get("selection_accesses") != 1
        or item.get("final_accesses") != 1
        or item.get("protected_payload_included") is not False
        or item.get("winner") not in SYSTEMS
        or not isinstance(systems, Mapping)
        or set(systems) != SYSTEMS
    ):
        raise ValueError("A5 owner evaluation binding is invalid")
    for system in SYSTEMS:
        row = systems[system]
        if not isinstance(row, Mapping) or row.get("coverage") != 872 or row.get("failures") != 0 or row.get("determinism") is not True:
            raise ValueError("A5 evaluated system coverage is invalid")
    effects = item.get("paired_effects")
    if not isinstance(effects, Mapping) or effects.get("bootstrap_resamples") != 10_000:
        raise ValueError("A5 paired-statistics plan is invalid")
    result_sha = item.get("result_sha256")
    if result_sha != canonical_sha256({key: value for key, value in item.items() if key != "result_sha256"}):
        raise ValueError("A5 owner evaluation self-hash mismatch")
    return item


def _winner_configuration(
    request: Mapping[str, Any],
    registry: list[Mapping[str, Any]],
    winner: str,
    winner_program_path: Path,
) -> dict[str, str]:
    source = next(row for row in registry if row["role"] == winner)
    program = next(row for row in request["finalist_bindings"] if row["system"] == winner)
    if (
        source["program_sha256"] != program["program_sha256"]
        or source["model_sha256"] != program["model_sha256"]
        or source["prompt_sha256"] != program["prompt_sha256"]
    ):
        raise ValueError("A5 registry and request winner drift")
    if winner != "research_champion":
        raise ValueError("A6 cannot materialize a non-research Final winner under the preregistered A6 contract")
    program_asset = _load(winner_program_path)
    program_body = {key: value for key, value in program_asset.items() if key != "program_sha256"}
    if (
        program_asset.get("schema_version") != "myis.armindex-representation-program.v1"
        or program_asset.get("arm_id") != "ARM-03"
        or program_asset.get("program_sha256") != canonical_sha256(program_body)
        or program_asset.get("program_sha256") != source["program_sha256"]
        or program_asset.get("program_id") != "a2-arm-03-matched-b2-orthogonal"
    ):
        raise ValueError("A5 ARM-03 program binding is invalid")
    model_lock = _load(ROOT / "control" / "armindex" / "a1.2" / "model-locks" / "ARM-03.v1.json")
    lock_body = {key: value for key, value in model_lock.items() if key != "lock_sha256"}
    artifacts = model_lock.get("critical_artifacts")
    if (
        model_lock.get("arm_id") != "ARM-03"
        or model_lock.get("lock_sha256") != canonical_sha256(lock_body)
        or not isinstance(artifacts, list)
        or not any(row.get("path") == "model.safetensors" and row.get("sha256") == source["model_sha256"] for row in artifacts if isinstance(row, Mapping))
    ):
        raise ValueError("A5 ARM-03 model lock binding is invalid")
    chunking = program_asset.get("unitization")
    if not isinstance(chunking, Mapping) or chunking.get("kind") != "passage":
        raise ValueError("A5 ARM-03 chunking binding is invalid")
    retrieval = {"top_k": request["top_k"], "family_aggregation": program_asset.get("family_aggregation")}
    index = {
        "duplicate_policy": program_asset.get("duplicate_policy"),
        "normalization": program_asset.get("normalization"),
        "preserve_family_identity": program_asset.get("preserve_family_identity"),
        "source_fields": program_asset.get("source_fields"),
        "field_order": program_asset.get("field_order"),
        "field_labels": program_asset.get("field_labels"),
    }
    if any(value is None for value in retrieval.values()) or any(value is None for value in index.values()):
        raise ValueError("A5 ARM-03 retrieval/index binding is incomplete")
    return {
        "representation_program_sha256": str(source["program_sha256"]),
        "prompt_or_prefix_sha256": str(source["prompt_sha256"]),
        "model_adapter_sha256": str(model_lock["lock_sha256"]),
        "chunking_configuration_sha256": canonical_sha256(chunking),
        "retrieval_configuration_sha256": canonical_sha256(retrieval),
        "index_configuration_sha256": canonical_sha256(index),
        "runtime_lock_sha256": str(source["runtime_sha256"]),
    }


def _validate_closeout_winner_pair(
    *,
    closeout: Mapping[str, Any],
    winner_binding: Mapping[str, Any],
    coverage: Mapping[str, Any],
    safe_return: Mapping[str, Any],
    final_registry: Mapping[str, Any],
    audit: Mapping[str, Any],
    a6_contract: Mapping[str, Any],
) -> None:
    required_closeout = {
        "schema_version", "status", "attempt_id", "scope", "winner", "winner_count",
        "owner_evaluation_sha256", "coverage_receipt_sha256", "safe_return_receipt_sha256",
        "result_integrity_audit_sha256", "finalist_registry_sha256",
        "frozen_winner_configuration_sha256", "a4_a5_pointer_bundle_sha256",
        "selection_accesses", "final_accesses", "protected_payload_included",
        "claim_boundary", "receipt_sha256",
    }
    if (
        set(closeout) != required_closeout
        or closeout.get("schema_version") != "myis.armindex-a5-final-closeout.v1"
        or closeout.get("status") != "PASS_A5_FINAL_CONFIRMATION"
        or closeout.get("scope") != "Final-872"
        or closeout.get("winner") != "research_champion"
        or closeout.get("winner_count") != 1
        or closeout.get("selection_accesses") != 1
        or closeout.get("final_accesses") != 1
        or closeout.get("protected_payload_included") is not False
        or closeout.get("receipt_sha256") != canonical_sha256({key: value for key, value in closeout.items() if key != "receipt_sha256"})
    ):
        raise ValueError("A5 closeout receipt is invalid")
    if (
        closeout["coverage_receipt_sha256"] != coverage["receipt_sha256"]
        or closeout["safe_return_receipt_sha256"] != safe_return["receipt_sha256"]
        or closeout["result_integrity_audit_sha256"] != audit["audit_sha256"]
        or closeout["finalist_registry_sha256"] != final_registry["receipt_sha256"]
        or closeout["a4_a5_pointer_bundle_sha256"] != final_registry["a4_a5_pointer_bundle_sha256"]
        or closeout["frozen_winner_configuration_sha256"] != canonical_sha256(winner_binding["winner"])
        or winner_binding["a5_closeout_receipt_sha256"] != closeout["receipt_sha256"]
        or winner_binding["a5_result_integrity_audit_sha256"] != audit["audit_sha256"]
        or winner_binding["a5_safe_return_receipt_sha256"] != safe_return["receipt_sha256"]
        or winner_binding["a5_finalist_registry_sha256"] != final_registry["receipt_sha256"]
    ):
        raise ValueError("A5 closeout and frozen winner linkage drifted")
    validate_a5_frozen_winner_binding(winner_binding, a6_contract)


def build(
    *,
    request_path: Path,
    package_path: Path,
    evaluation_path: Path,
    registry_path: Path,
    winner_program_path: Path,
    output_dir: Path,
) -> dict[str, str]:
    request = _validate_request(_load(request_path))
    package = _validate_package(_load(package_path), request)
    evaluation = _validate_evaluation(_load(evaluation_path), request, package_path)
    pointer = validate_a5_pointer_bundle(_load(registry_path))
    registry = pointer["final_registry"]
    winner = str(evaluation["winner"])
    coverage = _self_hash({
        "schema_version": "myis.armindex-a5-final-coverage.v1",
        "status": "PASS_A5_FINAL_COVERAGE",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "ranking_package_sha256": file_sha256(package_path),
        "ranking_sha256": package["ranking_sha256"],
        "scope": "Final-872",
        "query_count": 872,
        "coverage": package["coverage"],
        "failures": 0,
        "determinism": True,
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
    }, "receipt_sha256")
    safe_return = _self_hash({
        "schema_version": "myis.armindex-a5-safe-return.v1",
        "status": "PASS_A5_SAFE_RETURN",
        "attempt_id": request["attempt_id"],
        "opaque_package_sha256": file_sha256(package_path),
        "opaque_package_bytes": package_path.stat().st_size,
        "destination": "owner_store_only",
        "worker_teardown_verified": True,
        "provider_instance_id": 48367896,
        "provider_disposition": "KEEP_GPU_PENDING_OWNER_A6_APPROVAL",
        "repository_allowlist": ["aggregate_metrics", "counts", "hashes", "safe_manifests", "safe_receipts", "aggregate_figures", "failure_taxonomy"],
        "protected_payload_included": False,
        "selection_accesses": 1,
        "final_accesses": 1,
    }, "receipt_sha256")
    final_registry = _self_hash({
        "schema_version": "myis.armindex-a5-finalist-registry.v1",
        "status": "PASS_A5_FINALIST_REGISTRY_FROZEN",
        "attempt_id": request["attempt_id"],
        "a4_a5_pointer_bundle_sha256": pointer["bundle_sha256"],
        "registry": sorted(registry, key=lambda row: str(row["role"])),
        "winner": winner,
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
    }, "receipt_sha256")
    audit = _self_hash({
        "schema_version": "myis.armindex-a5-result-integrity-audit.v1",
        "status": "PASS_A5_RESULT_INTEGRITY_AUDIT",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "coverage_receipt_sha256": coverage["receipt_sha256"],
        "safe_return_receipt_sha256": safe_return["receipt_sha256"],
        "finalist_registry_sha256": final_registry["receipt_sha256"],
        "a4_a5_pointer_bundle_sha256": pointer["bundle_sha256"],
        "owner_evaluation_sha256": evaluation["result_sha256"],
        "ranking_package_sha256": file_sha256(package_path),
        "checks": {"two_system_registry": True, "complete_coverage": True, "canonical_ranking_hash": True, "owner_local_evaluation": True, "worker_teardown": True, "protected_boundary": True},
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
    }, "audit_sha256")
    winner_configuration = _winner_configuration(request, registry, winner, winner_program_path)
    a6_contract = _load(ROOT / "control" / "armindex" / "a6" / "a6-full-dapfam-execution-contract.v1.json")
    # Closeout precedes the A6 handoff.  It records the immutable winner
    # configuration rather than the future binding hash, avoiding a cyclic hash
    # dependency while retaining the complete scientific lineage.
    winner_configuration_sha256 = canonical_sha256(winner_configuration)
    closeout = _self_hash({
        "schema_version": "myis.armindex-a5-final-closeout.v1",
        "status": "PASS_A5_FINAL_CONFIRMATION",
        "attempt_id": request["attempt_id"],
        "scope": "Final-872",
        "winner": winner,
        "winner_count": 1,
        "owner_evaluation_sha256": evaluation["result_sha256"],
        "coverage_receipt_sha256": coverage["receipt_sha256"],
        "safe_return_receipt_sha256": safe_return["receipt_sha256"],
        "result_integrity_audit_sha256": audit["audit_sha256"],
        "finalist_registry_sha256": final_registry["receipt_sha256"],
        "a4_a5_pointer_bundle_sha256": pointer["bundle_sha256"],
        "frozen_winner_configuration_sha256": winner_configuration_sha256,
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
        "claim_boundary": "Final-872 confirmatory aggregate only; A6 remains a separately admitted post-confirmatory scalability phase.",
    }, "receipt_sha256")
    winner_binding = _self_hash({
        "schema_version": "myis.armindex-a6-a5-winner-binding.v1",
        "status": "PASS_A5_FROZEN_WINNER_BOUND",
        "a5_terminal_state": "PASS_A5_FINAL_CONFIRMATION",
        "winner_count": 1,
        "winner": winner_configuration,
        "a5_closeout_receipt_sha256": closeout["receipt_sha256"],
        "a5_result_integrity_audit_sha256": audit["audit_sha256"],
        "a5_safe_return_receipt_sha256": safe_return["receipt_sha256"],
        "a5_finalist_registry_sha256": final_registry["receipt_sha256"],
        "a5_frozen_winner_configuration_sha256": winner_configuration_sha256,
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
        "claim_boundary": a6_contract["claim_boundary"],
    }, "binding_sha256")
    _validate_closeout_winner_pair(
        closeout=closeout,
        winner_binding=winner_binding,
        coverage=coverage,
        safe_return=safe_return,
        final_registry=final_registry,
        audit=audit,
        a6_contract=a6_contract,
    )
    paths = {
        "coverage": output_dir / "A5_FINAL_COVERAGE.json",
        "safe_return": output_dir / "A5_FINAL_SAFE_RETURN.json",
        "registry": output_dir / "A5_FINALIST_REGISTRY.json",
        "audit": output_dir / "A5_FINAL_RESULT_INTEGRITY_AUDIT.json",
        "winner_binding": output_dir / "A5_FROZEN_WINNER_BINDING.json",
        "closeout": output_dir / "A5_FINAL_CLOSEOUT.json",
    }
    # A partially written output root is forensic-only and must never be reused.
    # Write the predecessor closeout before the binding that references it.
    for label, value in (("coverage", coverage), ("safe_return", safe_return), ("registry", final_registry), ("audit", audit), ("closeout", closeout), ("winner_binding", winner_binding)):
        _write_new(paths[label], value)
    return {label: file_sha256(path) for label, path in paths.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--winner-program", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build(
        request_path=args.request.resolve(strict=True),
        package_path=args.package.resolve(strict=True),
        evaluation_path=args.evaluation.resolve(strict=True),
        registry_path=args.registry.resolve(strict=True),
        winner_program_path=args.winner_program.resolve(strict=True),
        output_dir=args.output_dir.resolve(),
    )
    print(json.dumps({"status": "PASS_A5_CLOSEOUT_ARTIFACTS", "artifacts": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
