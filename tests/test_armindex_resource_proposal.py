from __future__ import annotations

import copy
from pathlib import Path

import pytest

from myis_research.armindex.resource_proposal import (
    load_and_validate_gpu_proposal,
    validate_gpu_proposal,
)


ROOT = Path(__file__).resolve().parents[1]


def test_a12_gpu_proposal_is_bounded_and_non_authorizing() -> None:
    proposal = load_and_validate_gpu_proposal(ROOT)

    assert proposal["status"] == "proposal_not_adopted_execution_locked"
    assert proposal["proposed_gpu_spec"]["gpu_count"] == 1
    assert proposal["proposed_gpu_spec"]["minimum_vram_gib"] == 24
    assert proposal["proposed_gpu_spec"]["a100_or_h100_required"] is False
    assert proposal["time_estimate"]["gpu_reservation_hours_min"] == 8
    assert proposal["time_estimate"]["gpu_reservation_hours_max"] == 16
    assert proposal["budget_estimate"]["common_screen_hard_stop"] == 18
    assert proposal["budget_estimate"]["a1_total_hard_stop"] == 23
    assert proposal["budget_estimate"]["campaign_hard_stop"] == 100


def test_a12_gpu_proposal_rejects_mutation() -> None:
    proposal = load_and_validate_gpu_proposal(ROOT)
    proposal = copy.deepcopy(proposal)
    proposal["status"] = "approved"

    with pytest.raises(ValueError, match="cannot authorize"):
        validate_gpu_proposal(ROOT, proposal)
