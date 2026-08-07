from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_live_preflight_result_v9 import (
    RECEIPT_PATH as V9_RESULT_RECEIPT_PATH,
)
from myis_research.armindex.a1_2_provider_closeout_result_v10 import (
    RECEIPT_PATH,
    SCHEMA_PATH,
    _validate_expected,
    _validate_payload,
    validate_closeout,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256


ROOT = Path(__file__).resolve().parents[1]


def test_provider_closeout_validates_and_preserves_all_execution_locks() -> None:
    result = validate_closeout(ROOT)
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))

    assert result["status"] == "PASS"
    assert receipt["predecessor"]["receipt_file_sha256"] == file_sha256(
        ROOT / V9_RESULT_RECEIPT_PATH
    )
    assert receipt["provider_closeout"]["owner_disposition"] == (
        "destroyed_and_provider_absence_verified"
    )
    assert receipt["provider_closeout"]["provider_destruction_proven"] is True
    assert receipt["provider_closeout"]["provider_instance_absent_verified"] is True
    assert receipt["provider_closeout"]["endpoint_observation"] == "connection_refused"
    assert receipt["provider_closeout"]["provider_api_query_performed"] is False
    assert receipt["provider_closeout"]["independent_provider_api_record_available"] is False
    assert receipt["pending_provider_checks"] == []
    assert receipt["launch_allowed"] is False
    assert receipt["adopted_for_execution"] is False
    assert receipt["measured_runs"] == 0
    assert receipt["selection_accesses"] == 0
    assert receipt["final_accesses"] == 0
    assert receipt["charged_usd"] == 0


def test_provider_closeout_rejects_self_hash_tampering() -> None:
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
    receipt["provider_closeout"]["provider_instance_absent_verified"] = False

    with pytest.raises(ValueError, match="schema failure|self-hash mismatch"):
        _validate_payload(receipt, schema)


def test_provider_closeout_rejects_rehashed_semantic_tampering() -> None:
    receipt = json.loads((ROOT / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
    receipt["provider_closeout"]["instance_id"] = "99999999"
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )

    with pytest.raises(ValueError, match="schema failure"):
        _validate_payload(receipt, schema)
    with pytest.raises(ValueError, match="frozen disposition facts"):
        _validate_expected(receipt)


def test_v9_historical_provider_state_remains_pending() -> None:
    v9 = json.loads((ROOT / V9_RESULT_RECEIPT_PATH).read_text(encoding="utf-8"))
    assert v9["lifecycle"]["provider_destruction_proven"] is False
    assert v9["owner_disposition"] == "pending_owner_policy_decision"
