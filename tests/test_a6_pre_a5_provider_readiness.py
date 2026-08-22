"""Focused checks for the non-executable A6 v2 provider-readiness plan."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a6_materialization import (
    A6MaterializationError,
    validate_a6_pre_a5_provider_readiness_plan,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json"
PLAN = ROOT / "control/armindex/a6/a6-pre-a5-provider-readiness.v2.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="ascii"))


def _rehash(value: dict) -> dict:
    value["plan_sha256"] = canonical_sha256({key: item for key, item in value.items() if key != "plan_sha256"})
    return value


def test_checked_in_v2_readiness_plan_is_non_executable_and_fresh() -> None:
    plan = validate_a6_pre_a5_provider_readiness_plan(_load(PLAN), _load(CONTRACT))
    assert plan["candidate_provider"]["instance_id"] == 48367896
    assert plan["candidate_provider"]["identity_verified"] is False
    assert plan["aggregate_health_observation"]["status"] == "NOT_OBSERVED"
    assert plan["remote_pre_stage"]["status"] == "NOT_CREATED"
    assert plan["execution_permitted"] is False


@pytest.mark.parametrize(
    ("mutate",),
    [
        (lambda value: value["candidate_provider"].update({"instance_id": 47790578}),),
        (lambda value: value["remote_pre_stage"].update({"empty_parent_created": True}),),
        (lambda value: value.update({"provider_contact_performed": True}),),
    ],
)
def test_v2_readiness_plan_rejects_stale_or_remote_progress(mutate) -> None:
    plan = _load(PLAN)
    mutate(plan)
    with pytest.raises(A6MaterializationError):
        validate_a6_pre_a5_provider_readiness_plan(_rehash(plan), _load(CONTRACT))
