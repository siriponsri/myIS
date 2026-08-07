from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_live_preflight_result_v9 import (
    RECEIPT_PATH,
    SCHEMA_PATH,
    _validate_expected_receipt,
    _validate_receipt_payload,
    validate_result,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def test_live_synthetic_result_validates_and_keeps_scientific_counters_closed() -> None:
    result = validate_result(ROOT)
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))

    assert result["status"] == "PASS"
    assert receipt["attempt_id"] == "a12-v9-20260807-06"
    assert [item["arm_id"] for item in receipt["arms"]] == [
        "ARM-02",
        "ARM-03",
        "ARM-04",
        "ARM-05",
    ]
    assert {item["status"] for item in receipt["arms"]} == {"PASS"}
    assert receipt["qwen"]["measured_adapter_max_input_tokens"] == 32768
    assert receipt["lifecycle"]["checkpoint_resume"] == "PASS"
    assert receipt["lifecycle"]["guest_process_teardown"] == "PASS"
    assert receipt["lifecycle"]["provider_destruction_proven"] is False
    assert receipt["launch_allowed"] is False
    assert receipt["adopted_for_execution"] is False
    assert receipt["measured_runs"] == 0
    assert receipt["selection_accesses"] == 0
    assert receipt["final_accesses"] == 0
    assert receipt["charged_usd"] == 0


def test_live_synthetic_result_rejects_self_hash_tampering() -> None:
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
    receipt["qwen"]["measured_adapter_max_input_tokens"] = 16384

    with pytest.raises(ValueError, match="schema failure|self-hash mismatch"):
        _validate_receipt_payload(receipt, schema)


def test_live_synthetic_result_rejects_rehashed_semantic_tampering() -> None:
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
    receipt["provider"]["instance_id"] = "99999999"
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )

    _validate_receipt_payload(receipt, schema)
    with pytest.raises(ValueError, match="frozen attempt facts"):
        _validate_expected_receipt(ROOT, receipt)
