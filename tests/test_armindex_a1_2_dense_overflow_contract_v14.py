from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_dense_overflow_contract_v14 as validator
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / validator.CONTRACT_PATH


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _rehash(value: dict[str, object]) -> dict[str, object]:
    value["contract_sha256"] = canonical_sha256(
        {key: item for key, item in value.items() if key != "contract_sha256"}
    )
    return value


def _reject(mutator) -> None:
    value = _rehash(mutator(copy.deepcopy(_contract())))
    with pytest.raises(validator.DenseOverflowContractV14Error):
        validator.validate_contract(ROOT, value)


def test_current_frozen_contract_is_strictly_valid() -> None:
    result = validator.validate_contract(ROOT)
    assert result == {
        "status": "PASS",
        "repair_id": "a1.2-additive-dense-overflow-composition-v14",
        "compatible_program_arm_cells": 25,
        "dense_adapter_arms": 4,
        "provider_contact_allowed": False,
        "measured_retrieval_allowed": False,
    }


def test_rehashed_aggregation_tamper_is_rejected() -> None:
    _reject(lambda value: value["composition_semantics"].update({"aggregation": "mean"}) or value)


def test_rehashed_physical_unit_semantics_tamper_is_rejected() -> None:
    _reject(lambda value: value["composition_semantics"].update({"source_token_multiplicity": 2}) or value)


def test_rehashed_overlap_and_omission_tampering_is_rejected() -> None:
    _reject(lambda value: value["composition_semantics"].update({"overlap_tokens": 1}) or value)
    _reject(lambda value: value["composition_semantics"].update({"omission_allowed": True}) or value)


def test_rehashed_authorization_tampering_is_rejected() -> None:
    _reject(lambda value: value["authorization"].update({"measured_retrieval_allowed": True}) or value)
    _reject(lambda value: value["owner_decision"].update({"allow_partial_screen": True}) or value)


def test_rehashed_immutable_lineage_tampering_is_rejected() -> None:
    _reject(lambda value: value["immutable_lineage"].update({"v12_r3_file_sha256": "0" * 64}) or value)
    _reject(lambda value: value["raw_inventory"].update({"inventory_sha256": "0" * 64}) or value)


def test_rehashed_source_hash_tampering_is_rejected() -> None:
    _reject(lambda value: value["implementation"].update({"audit_source_sha256": "0" * 64}) or value)
    _reject(lambda value: value["v9_adapter_lineage"].update({"file_sha256": "0" * 64}) or value)


def test_rehashed_v9_adapter_receipt_mapping_tampering_is_rejected() -> None:
    _reject(
        lambda value: value["arm_postprocessing"]["ARM-03"].update(
            {"adapter_receipt_sha256": "0" * 64}
        )
        or value
    )


def test_v9_dimension_and_model_mapping_are_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(validator.ADAPTERS, "ARM-04", (validator.ADAPTERS["ARM-04"][0], 1024))
    with pytest.raises(validator.DenseOverflowContractV14Error, match="mapping"):
        validator.validate_contract(ROOT)


def test_contract_self_hash_tamper_is_rejected() -> None:
    value = _contract()
    value["contract_sha256"] = "0" * 64
    with pytest.raises(validator.DenseOverflowContractV14Error, match="self-hash"):
        validator.validate_contract(ROOT, value)


def test_schema_rejects_unknown_contract_fields() -> None:
    value = _contract()
    value["unexpected"] = True
    with pytest.raises(validator.DenseOverflowContractV14Error, match="schema"):
        validator.validate_contract(ROOT, value)
