from __future__ import annotations

import pytest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from myis_research.armindex.a3_three_primary_owner_evaluator import validate_aggregate_result
from myis_research.kernel.canonical import canonical_sha256
_MODULE_SPEC = spec_from_file_location(
    "evaluate_a3_harnessopt_owner_local",
    Path(__file__).parents[1] / "scripts" / "evaluate_a3_harnessopt_owner_local.py",
)
assert _MODULE_SPEC and _MODULE_SPEC.loader
_MODULE = module_from_spec(_MODULE_SPEC)
_MODULE_SPEC.loader.exec_module(_MODULE)

A3HarnessOptOwnerEvaluationError = _MODULE.A3HarnessOptOwnerEvaluationError
evaluate_harnessopt_evidence = _MODULE.evaluate_harnessopt_evidence


BINDING = "a" * 64


def _configuration(binding: str = BINDING) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-harness.v2",
        "harness_id": "test-harness",
        "profile": "BALANCED",
        "frozen_bindings_sha256": binding,
        "arm_ids": ["ARM-03", "ARM-04", "ARM-05"],
        "invocation_order": ["ARM-03", "ARM-04", "ARM-05"],
        "execution_mode": "parallel",
        "initial_depth_by_arm": {"ARM-03": 100, "ARM-04": 100, "ARM-05": 100},
        "maximum_depth_by_arm": {"ARM-03": 100, "ARM-04": 100, "ARM-05": 100},
        "fusion": {"method": "rrf", "rrf_k": 60, "weights": {"ARM-03": 1.0, "ARM-04": 1.0, "ARM-05": 1.0}},
        "routing": [],
        "early_stop": {"max_escalations": 2, "score_margin": 0.1, "rank_stability": 0.9},
        "cache_policy": "frozen_read_only",
        "latency_profile": "balanced",
        "runtime_features": [],
    }
    body["config_sha256"] = canonical_sha256(body)
    return body


def _batch(iteration: int, binding: str = BINDING) -> dict[str, object]:
    candidates = []
    for index, role in enumerate(
        ("quality_exploit", "cost_latency_ablation", "routing_hypothesis", "diversity_profile"), start=1
    ):
        candidate_id = f"test-i{iteration}-c{index}"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "role": role,
                "hypothesis": "A bounded test hypothesis.",
                "matched_ablation_id": f"test-i{iteration}-c{3 - index}" if index <= 2 else None,
                "scientific_payload_sha256": f"{index}{iteration}" * 32,
                "configuration": _configuration(binding),
                "verifier_status": "accepted",
            }
        )
    body: dict[str, object] = {
        "schema_version": "myis.armindex-harness-batch.v1",
        "batch_id": f"test-i{iteration}",
        "iteration": iteration,
        "frozen_bindings_sha256": binding,
        "status": "frozen_before_evaluation",
        "candidates": candidates,
    }
    body["batch_sha256"] = canonical_sha256(body)
    return body


def _runtime_bindings() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a3-three-primary-runtime-bindings.v1",
        "primary_arm_scope": ["ARM-03", "ARM-04", "ARM-05"],
        "budget_extension_sha256": "b" * 64,
        "authority_sha256": "c" * 64,
        "manifest_sha256": "d" * 64,
        "admission_sha256": "e" * 64,
        "winner_bindings": {
            arm: {"winner_program_sha256": "f" * 64, "winner_selection_receipt_sha256": "1" * 64}
            for arm in ("ARM-03", "ARM-04", "ARM-05")
        },
        "target_adapter_sha256s": {arm: "2" * 64 for arm in ("ARM-03", "ARM-04", "ARM-05")},
        "package_bindings": {key: "3" * 64 for key in (
            "corpus_sha256", "query_bundle_sha256", "split_commitment_sha256", "evaluator_sha256",
            "qrels_commitment_sha256", "membership_commitment_sha256", "runtime_lock_sha256", "data_handoff_sha256",
        )},
    }
    body["runtime_bindings_sha256"] = canonical_sha256(body)
    return body


def _fixed_result() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a3-three-primary-aggregate-result.v1",
        "status": "PASS_A3_OWNER_LOCAL_AGGREGATE_EVALUATION",
        "operation_id": "fixed-all-primary-rrf60",
        "operation_kind": "fixed_union",
        "request_sha256": "4" * 64,
        "ranking_sha256": "5" * 64,
        "evaluator_binding_sha256": "6" * 64,
        "evaluator_input_sha256": "7" * 64,
        "metrics": {"recall_at_100/out": "0.42", "ndcg_at_100/out": "0.31", "ndcg_at_10/out": "0.12"},
        "latency": {"wall_seconds": 1.0, "search_p95_seconds": 0.2},
        "coverage": {"expected_units": 250, "completed_units": 250},
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    body["receipt_sha256"] = canonical_sha256(body)
    validate_aggregate_result(body)
    return body


def test_flat_three_batch_harness_surface_reuses_fixed_reference() -> None:
    runtime = _runtime_bindings()
    fixed = _fixed_result()
    safe_return = {"aggregate_result_receipt_sha256s": {"fixed-all-primary-rrf60": fixed["receipt_sha256"]}}
    binding = str(runtime["runtime_bindings_sha256"])
    result = evaluate_harnessopt_evidence(runtime, [_batch(1, binding), _batch(2, binding), _batch(3, binding)], fixed, safe_return)

    assert result["status"] == "PASS_A3_HARNESSOPT_FLAT_SURFACE"
    assert result["complete_batch_count"] == 3
    assert result["candidate_count"] == 12
    assert result["unique_action_signature_count"] == 1
    assert {row["reference_operation_id"] for row in result["candidates"]} == {"fixed-all-primary-rrf60"}


def test_harnessopt_requires_complete_batches() -> None:
    runtime = _runtime_bindings()
    fixed = _fixed_result()
    safe_return = {"aggregate_result_receipt_sha256s": {"fixed-all-primary-rrf60": fixed["receipt_sha256"]}}
    with pytest.raises(A3HarnessOptOwnerEvaluationError, match="exactly three"):
        evaluate_harnessopt_evidence(runtime, [_batch(1, str(runtime["runtime_bindings_sha256"]))], fixed, safe_return)


def test_harnessopt_rejects_unbound_fixed_reference() -> None:
    runtime = _runtime_bindings()
    fixed = _fixed_result()
    with pytest.raises(A3HarnessOptOwnerEvaluationError, match="bound by safe return"):
        binding = str(runtime["runtime_bindings_sha256"])
        evaluate_harnessopt_evidence(runtime, [_batch(1, binding), _batch(2, binding), _batch(3, binding)], fixed, {})
