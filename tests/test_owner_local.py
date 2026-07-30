from __future__ import annotations

import pytest

from myis_research.owner_local import (
    OwnerLocalContractError,
    build_receipt,
    canonical_sha256,
    validate_receipt,
    validate_request,
)


def request(decision: str = "P1_CPU_EXECUTION_ENVELOPE") -> dict[str, object]:
    return {
        "schema_version": "myis.owner-local-request.v1",
        "request_id": "scope-aggregate-01",
        "decision_id": decision,
        "scope": {"campaign": "a" * 64, "split": "b" * 64},
        "git_commit": "c" * 40,
        "input_hashes": {"manifest": "d" * 64},
    }


def test_request_hash_is_stable_under_mapping_order() -> None:
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})
    assert validate_request(request())["decision_id"] == "P1_CPU_EXECUTION_ENVELOPE"


@pytest.mark.parametrize("decision", ["P1_CPU_EXECUTION_ENVELOPE", "D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"])
def test_valid_decisions_build_and_validate_receipt(decision: str) -> None:
    receipt = build_receipt(request(decision), aggregate_counts={"n": 3}, aggregate_hashes={"metric": "e" * 64})
    assert validate_receipt(receipt)["decision_id"] == decision


def test_d1_and_legacy_gates_are_rejected() -> None:
    with pytest.raises(OwnerLocalContractError):
        validate_request(request("D1_START_CAMPAIGN"))


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
    receipt = build_receipt(request(), aggregate_counts={"n": 3}, aggregate_hashes={"metric": "e" * 64})
    receipt["aggregate_counts"] = {"n": 4}
    with pytest.raises(OwnerLocalContractError):
        validate_receipt(receipt)
