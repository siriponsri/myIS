from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex import a2_candidate_freeze as freeze
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
BUDGET_PATH = ROOT / "control/budgets/a2-per-arm-autoindex-v1.json"
CONTRACT_PATH = ROOT / "control/armindex/a2/execution-contract.v1.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_a2_contract_binds_exact_five_arm_design_and_controls() -> None:
    controls = freeze._validate_control_set(ROOT)
    budget = controls["budget"]
    contract = controls["contract"]
    bindings = contract["bindings"]

    assert contract["candidate_design"] == freeze.design_summary()
    assert contract["launch_allowed"] is False
    assert contract["measured_execution_allowed"] is False
    assert set(contract["arm_policy"]) == set(freeze.ARMS)
    for arm_id in freeze.DIAGNOSTIC_NON_ADVANCING_ARMS:
        assert contract["arm_policy"][arm_id] == {
            "tier_count": 2,
            "candidate_count": 8,
            "diagnostic_non_advancing": True,
            "advancement_eligible": False,
        }
    for arm_id in freeze.PRIMARY_ADVANCEMENT_ARMS:
        assert contract["arm_policy"][arm_id] == {
            "tier_count": 3,
            "candidate_count": 12,
            "diagnostic_non_advancing": False,
            "advancement_eligible": True,
        }
    assert bindings["campaign_sha256"] == file_sha256(
        ROOT / bindings["campaign_uri"]
    )
    assert bindings["execution_envelope_sha256"] == file_sha256(
        ROOT / bindings["execution_envelope_uri"]
    )
    assert bindings["budget_profile_sha256"] == budget["budget_profile_sha256"]
    assert bindings["official_bridge_file_sha256"] == file_sha256(
        ROOT / bindings["official_bridge_uri"]
    )


def test_a2_budget_scales_a1_wall_time_and_covers_reserve_plus_six_hours() -> None:
    budget = _load(BUDGET_PATH)
    source = budget["source_measurement"]
    projection = budget["runtime_projection"]
    counts = projection["candidate_count_by_arm"]
    wall = source["wall_seconds_sum_by_arm"]

    expected = {
        arm_id: wall[arm_id] / source["measured_programs_per_arm"] * counts[arm_id]
        for arm_id in freeze.ARMS
    }
    assert projection["projected_wall_seconds_by_arm"] == pytest.approx(expected)
    assert projection["worst_case_dense_parallel_critical_path_seconds"] == pytest.approx(
        max(expected[arm_id] for arm_id in freeze.ARMS if arm_id != "ARM-01")
    )
    assert projection["worst_case_dense_gpu_seconds"] == pytest.approx(
        sum(expected[arm_id] for arm_id in freeze.ARMS if arm_id != "ARM-01")
    )
    assert projection["minimum_owner_ttl_seconds"] == pytest.approx(
        projection["worst_case_dense_parallel_critical_path_seconds"] + 6 * 3600
    )
    assert budget["hard_stops"]["remaining_campaign_ceiling_usd"] == pytest.approx(
        150 - 11.161632
    )
    assert budget["admission"]["launch_allowed"] is False
    assert budget["admission"]["no_default_inference"] is True


def test_a2_budget_and_contract_self_hashes_are_current() -> None:
    budget = _load(BUDGET_PATH)
    contract = _load(CONTRACT_PATH)

    assert budget["budget_profile_sha256"] == canonical_sha256(
        {key: value for key, value in budget.items() if key != "budget_profile_sha256"}
    )
    assert contract["contract_sha256"] == canonical_sha256(
        {key: value for key, value in contract.items() if key != "contract_sha256"}
    )
