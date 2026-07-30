from __future__ import annotations

import pytest

from myis_research.owner_local import OwnerLocalContractError, build_receipt, canonical_sha256, validate_receipt, validate_request


def request(decision: str = "P1_CPU_EXECUTION_ENVELOPE") -> dict[str, object]:
    phase, stage = {
        "P1_CPU_EXECUTION_ENVELOPE": ("P1_CPU_BASELINE", "train_selection"),
        "D2_OPEN_FINAL": ("P3_FINAL", "final"),
        "D3_SUBMIT_RELEASE": ("P4_PUBLICATION", "report"),
    }[decision]
    return {
        "schema_version": "myis.owner-local-request.v2",
        "request_id": "scope-aggregate-01",
        "decision_id": decision,
        "phase_id": phase,
        "stage": stage,
        "scope": {"campaign": "a" * 64, "split": "b" * 64},
        "git_commit": "c" * 40,
        "input_hashes": {"manifest": "d" * 64},
    }


def metrics(decision: str = "P1_CPU_EXECUTION_ENVELOPE") -> list[dict[str, object]]:
    if decision != "P1_CPU_EXECUTION_ENVELOPE":
        return [{"name": "recall_at_100", "value": 0.5, "n": 2, "hits": 1, "scope": scope, "split": "train_selection", "direction": "maximize", "denominator": "queries_with_positive_family_relevance", "evidence_role": "primary"} for scope in ("ALL", "IN", "OUT")]
    return [
        {"arm": arm, "name": "recall_at_100", "value": 0.5, "n": 2, "retrieved_relevant": 1, "relevant_total": 2, "scope": scope, "split": split, "direction": "maximize", "denominator": "macro_mean_per_query_relevant_families", "evidence_role": "primary" if scope == "OUT" else "secondary"}
        for arm in ("R0", "R0-W") for split in ("train", "selection") for scope in ("ALL", "IN", "OUT")
    ]


def lineage() -> dict[str, str]:
    return {"dataset_sha256": "a" * 64, "corpus_sha256": "b" * 64, "query_sha256": "c" * 64, "qrels_sha256": "d" * 64, "split_sha256": "e" * 64, "index_sha256": "f" * 64, "evaluator_sha256": "0" * 64}


def receipt_arguments(decision: str) -> dict[str, object]:
    if decision == "P1_CPU_EXECUTION_ENVELOPE":
        return {"aggregate_counts": {"documents": 3, "train_queries": 2, "selection_queries": 2}, "aggregate_hashes": {f"{arm.lower()}_{split}_metrics": "e" * 64 for arm in ("R0", "R0-W") for split in ("train", "selection")}}
    return {"aggregate_counts": {"n": 3}, "aggregate_hashes": {"metric_sha256": "e" * 64}}


def test_request_hash_is_stable_under_mapping_order() -> None:
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})
    assert validate_request(request())["decision_id"] == "P1_CPU_EXECUTION_ENVELOPE"


@pytest.mark.parametrize("decision", ["P1_CPU_EXECUTION_ENVELOPE", "D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"])
def test_valid_decisions_build_and_validate_receipt(decision: str) -> None:
    receipt = build_receipt(request(decision), **receipt_arguments(decision), metrics=metrics(decision), cost_usd=0.0, latency_seconds=0.1, lineage_hashes=lineage())
    assert validate_receipt(receipt)["decision_id"] == decision


def test_d1_and_phase_mismatched_gates_are_rejected() -> None:
    with pytest.raises(OwnerLocalContractError):
        validate_request({**request(), "decision_id": "D1_START_CAMPAIGN"})
    with pytest.raises(OwnerLocalContractError):
        validate_request({**request("D2_OPEN_FINAL"), "phase_id": "P1_CPU_BASELINE", "stage": "train_selection"})


@pytest.mark.parametrize("key", ["query_id", "qrels", "per_query_outcomes", "membership", "raw_payload"])
def test_protected_fields_are_rejected(key: str) -> None:
    payload = request()
    payload["scope"] = {key: "a" * 64}
    with pytest.raises((OwnerLocalContractError, ValueError)):
        validate_request(payload)


def test_unknown_field_and_list_are_rejected() -> None:
    payload = request()
    payload["extra"] = True
    with pytest.raises(OwnerLocalContractError):
        validate_request(payload)
    payload = request()
    payload["scope"] = ["a" * 64]
    with pytest.raises(OwnerLocalContractError):
        validate_request(payload)


def test_tampered_receipt_is_rejected() -> None:
    receipt = build_receipt(request(), **receipt_arguments("P1_CPU_EXECUTION_ENVELOPE"), metrics=metrics(), cost_usd=0.0, latency_seconds=0.1, lineage_hashes=lineage())
    receipt["aggregate_counts"] = {"n": 4}
    with pytest.raises(OwnerLocalContractError):
        validate_receipt(receipt)


def test_p1_matrix_and_semantic_bounds_fail_closed() -> None:
    kwargs = receipt_arguments("P1_CPU_EXECUTION_ENVELOPE")
    invalid_matrix = metrics()
    invalid_matrix[-1] = {**invalid_matrix[-1], "scope": "ALL"}
    with pytest.raises(OwnerLocalContractError, match="exact R0/R0-W"):
        build_receipt(request(), **kwargs, metrics=invalid_matrix, cost_usd=0.0, latency_seconds=0.1, lineage_hashes=lineage())
    invalid_bounds = metrics()
    invalid_bounds[0] = {**invalid_bounds[0], "retrieved_relevant": 3}
    with pytest.raises(OwnerLocalContractError, match="cannot exceed"):
        build_receipt(request(), **kwargs, metrics=invalid_bounds, cost_usd=0.0, latency_seconds=0.1, lineage_hashes=lineage())
