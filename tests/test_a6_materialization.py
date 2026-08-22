from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a6_materialization import (
    A6MaterializationError,
    build_pending_a6_materialization_template,
    validate_a5_frozen_winner_binding,
    validate_a6_attempt_admission,
    validate_pending_a6_materialization_template,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "control" / "armindex" / "a6" / "a6-full-dapfam-execution-contract.v1.json"
TEMPLATE_PATH = ROOT / "control" / "armindex" / "a6" / "a6-pending-a5-closeout-template.v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _winner_binding() -> dict:
    contract = _contract()
    winner = {field: "a" * 64 for field in contract["frozen_input_contract"]["must_match_a5"]}
    body = {
        "schema_version": "myis.armindex-a6-a5-winner-binding.v1",
        "status": "PASS_A5_FROZEN_WINNER_BOUND",
        "a5_terminal_state": "PASS_A5_FINAL_CONFIRMATION",
        "winner_count": 1,
        "winner": winner,
        "a5_closeout_receipt_sha256": "b" * 64,
        "a5_result_integrity_audit_sha256": "b" * 64,
        "a5_safe_return_receipt_sha256": "b" * 64,
        "a5_finalist_registry_sha256": "b" * 64,
        "a5_frozen_winner_configuration_sha256": canonical_sha256(winner),
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
        "claim_boundary": contract["claim_boundary"],
    }
    return {**body, "binding_sha256": canonical_sha256(body)}


def _admission(winner: dict) -> dict:
    contract = _contract()
    body = {
        "schema_version": "myis.armindex-a6-attempt-admission.v1",
        "status": "PASS_A6_FRESH_ATTEMPT_ADMISSION",
        "execution_permitted": True,
        "launch_allowed": True,
        "a6_contract_sha256": contract["contract_sha256"],
        "a5_winner_binding_sha256": winner["binding_sha256"],
        "attempt_id": "a6-goal001-20260820T010203Z-a1",
        "attempt_root_pointer": "a6/a6-goal001-20260820T010203Z-a1",
        "authorized_instance_id": 48367896,
        "provider_identity_sha256": "c" * 64,
        "fresh_quote_sha256": "c" * 64,
        "budget_admission_sha256": "c" * 64,
        "runtime_health_sha256": "c" * 64,
        "gpu_health_sha256": "c" * 64,
        "disk_health_sha256": "c" * 64,
        "safe_export_manifest_sha256": "c" * 64,
        "fresh_attempt_root_required": True,
        "stale_runtime_reuse_forbidden": True,
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
        "claim_boundary": contract["claim_boundary"],
    }
    return {**body, "admission_sha256": canonical_sha256(body)}


def test_builds_fail_closed_a6_template() -> None:
    template = build_pending_a6_materialization_template(_contract())
    validated = validate_pending_a6_materialization_template(template, _contract())
    assert validated["status"] == "PENDING_A5_CLOSEOUT"
    assert validated["authorized_instance_id"] == 48367896
    assert validated["selection_accesses"] == validated["final_accesses"] == 0


def test_checked_in_template_matches_contract() -> None:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert validate_pending_a6_materialization_template(template, _contract()) == template


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution_permitted", True),
        ("a5_frozen_winner_configuration", "a" * 64),
        ("full_corpus_source_sha256", "b" * 64),
        ("owner_store_root", "a6/attempt"),
        ("authorized_instance_id", 1),
    ],
)
def test_pending_template_rejects_pre_a5_or_unsafe_state(field: str, value: object) -> None:
    template = build_pending_a6_materialization_template(_contract())
    template[field] = value
    with pytest.raises(A6MaterializationError):
        validate_pending_a6_materialization_template(template, _contract())


def test_contract_hash_or_same_instance_policy_cannot_drift() -> None:
    contract = _contract()
    contract["provider_admission"]["authorized_instance_id"] = 1
    with pytest.raises(A6MaterializationError):
        build_pending_a6_materialization_template(contract)


def test_a5_winner_binding_and_fresh_a6_admission_validate() -> None:
    contract = _contract()
    winner = _winner_binding()
    assert validate_a5_frozen_winner_binding(winner, contract)["winner_count"] == 1
    admission = _admission(winner)
    assert validate_a6_attempt_admission(admission, contract, winner)["authorized_instance_id"] == 48367896


def test_a6_admission_rejects_winner_drift_and_stale_reuse() -> None:
    contract = _contract()
    winner = _winner_binding()
    tampered_winner = {**winner, "winner": {**winner["winner"], "runtime_lock_sha256": "d" * 64}}
    tampered_winner["a5_frozen_winner_configuration_sha256"] = canonical_sha256(tampered_winner["winner"])
    tampered_winner["binding_sha256"] = canonical_sha256({key: value for key, value in tampered_winner.items() if key != "binding_sha256"})
    admission = _admission(winner)
    with pytest.raises(A6MaterializationError):
        validate_a6_attempt_admission(admission, contract, tampered_winner)
    stale = {**admission, "stale_runtime_reuse_forbidden": False}
    stale["admission_sha256"] = canonical_sha256({key: value for key, value in stale.items() if key != "admission_sha256"})
    with pytest.raises(A6MaterializationError):
        validate_a6_attempt_admission(stale, contract, winner)
