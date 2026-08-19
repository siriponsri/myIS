from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a6_materialization import (
    A6MaterializationError,
    build_pending_a6_materialization_template,
    validate_pending_a6_materialization_template,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "control" / "armindex" / "a6" / "a6-full-dapfam-execution-contract.v1.json"
TEMPLATE_PATH = ROOT / "control" / "armindex" / "a6" / "a6-pending-a5-closeout-template.v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_builds_fail_closed_a6_template() -> None:
    template = build_pending_a6_materialization_template(_contract())
    validated = validate_pending_a6_materialization_template(template, _contract())
    assert validated["status"] == "PENDING_A5_CLOSEOUT"
    assert validated["authorized_instance_id"] == 47790578
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
