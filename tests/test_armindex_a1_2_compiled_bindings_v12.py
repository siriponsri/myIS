from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_compiled_bindings_v12 import (
    _self_hash,
    pending_template,
    validate_binding_set,
    write_pending_template,
)


ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64


def _completed() -> dict[str, object]:
    value = deepcopy(pending_template(ROOT))
    value["binding_set_id"] = "a1.2-v12-owner-local-test"
    value["status"] = "validated_owner_local_protected_compilation"
    value["claim_boundary"] = (
        "Aggregate-safe test receipt for validator coverage only. It contains hashes and counts, not protected corpus, queries, qrels, membership, rankings, credentials, paths, or model bytes."
    )
    value["owner_local_receipts"] = {
        "handoff_receipt_sha256": "1" * 64,
        "protected_transfer_manifest_sha256": "2" * 64,
        "corpus_bundle_sha256": "3" * 64,
        "query_bundle_sha256": "4" * 64,
        "split_commitment_sha256": "5" * 64,
        "evaluator_sha256": "6" * 64,
        "ephemeral_token_map_sha256": "7" * 64,
    }
    lock = {
        item["arm_id"]: item
        for item in __import__("json").loads(
            (
                ROOT
                / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json"
            ).read_text()
        )["model_locks"]
    }
    bindings = []
    for index, expected in enumerate(value["expected_bindings"], start=1):
        arm = expected["arm_id"]
        bindings.append(
            {
                **expected,
                "compiler_source_manifest_sha256": value["frozen_bindings"][
                    "compiler_source_manifest_sha256"
                ],
                "model_lock_file_sha256": lock[arm]["file_sha256"],
                "adapter_contract_sha256": lock[arm]["adapter_contract_sha256"],
                "tokenizer_sha256": lock[arm]["tokenizer_sha256"],
                "effective_input_limit": lock[arm]["effective_input_limit"] or 512,
                "rendered_input_max_tokens": 512,
                "compiled_representation_sha256": f"{index + 100:064x}",
                "unit_count": 1,
                "coverage_gap_count": 0,
                "omitted_unit_count": 0,
                "truncation_count": 0,
                "overlength_count": 0,
                "index_manifest_sha256": f"{index + 200:064x}",
            }
        )
    value["bindings"] = bindings
    value["binding_set_sha256"] = _self_hash(value)
    return value


def test_pending_template_is_deterministic_and_has_exact_25_bindings() -> None:
    first = pending_template(ROOT)
    second = pending_template(ROOT)

    assert first == second
    assert len(first["expected_bindings"]) == 25
    assert first["bindings"] == []
    assert validate_binding_set(ROOT, first)["actual_bindings"] == 0


def test_write_template_requires_external_owner_local_path(tmp_path: Path) -> None:
    output = tmp_path / "compiled-bindings.json"

    result = write_pending_template(ROOT, output)

    assert output.is_file()
    assert result["status"] == "pending_owner_local_protected_compilation"
    with pytest.raises(ValueError, match="outside the repository"):
        write_pending_template(ROOT, ROOT / "compiled-bindings.json")


def test_completed_receipt_requires_exact_25_unique_safe_bindings() -> None:
    value = _completed()

    result = validate_binding_set(ROOT, value)

    assert result["status"] == "validated_owner_local_protected_compilation"
    assert result["expected_bindings"] == 25
    assert result["actual_bindings"] == 25


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("truncation_count", 1, "gap, omission, truncation, or overlength"),
        ("coverage_gap_count", 1, "gap, omission, truncation, or overlength"),
        ("omitted_unit_count", 1, "gap, omission, truncation, or overlength"),
        ("overlength_count", 1, "gap, omission, truncation, or overlength"),
        ("rendered_input_max_tokens", 513, "overlength rendered input"),
    ],
)
def test_completed_receipt_fails_closed_on_nonzero_or_overlength(
    field: str,
    value: int,
    message: str,
) -> None:
    receipt = _completed()
    target = (
        receipt["bindings"][10]
        if field == "rendered_input_max_tokens"
        else receipt["bindings"][0]
    )
    target[field] = value
    receipt["binding_set_sha256"] = _self_hash(receipt)

    with pytest.raises(ValueError, match=message):
        validate_binding_set(ROOT, receipt)


def test_completed_receipt_rejects_missing_matrix_member_and_unsafe_path() -> None:
    receipt = _completed()
    receipt["bindings"][-1]["binding_id"] = receipt["bindings"][-2]["binding_id"]
    receipt["binding_set_sha256"] = _self_hash(receipt)
    with pytest.raises(ValueError, match="unique and cover"):
        validate_binding_set(ROOT, receipt)

    unsafe = _completed()
    unsafe["claim_boundary"] += " C:\\Users\\owner\\private"
    unsafe["binding_set_sha256"] = _self_hash(unsafe)
    with pytest.raises(
        ValueError, match="protected, credential-like, or absolute-path"
    ):
        validate_binding_set(ROOT, unsafe)


def test_completed_receipt_rejects_frozen_tokenizer_or_model_drift() -> None:
    receipt = _completed()
    receipt["bindings"][0]["tokenizer_sha256"] = H
    receipt["binding_set_sha256"] = _self_hash(receipt)

    with pytest.raises(ValueError, match="tokenizer hash mismatch"):
        validate_binding_set(ROOT, receipt)


@pytest.mark.parametrize(
    ("arm_id", "field", "value", "message"),
    [
        ("ARM-01", "effective_input_limit", 513, "unbounded lexical input limit"),
        ("ARM-02", "effective_input_limit", 16384, "effective-input limit mismatch"),
        ("ARM-03", "adapter_contract_sha256", H, "adapter-contract hash mismatch"),
    ],
)
def test_completed_receipt_rejects_invented_limit_or_adapter_binding(
    arm_id: str,
    field: str,
    value: int | str,
    message: str,
) -> None:
    receipt = _completed()
    binding = next(item for item in receipt["bindings"] if item["arm_id"] == arm_id)
    binding[field] = value
    receipt["binding_set_sha256"] = _self_hash(receipt)

    with pytest.raises(ValueError, match=message):
        validate_binding_set(ROOT, receipt)
