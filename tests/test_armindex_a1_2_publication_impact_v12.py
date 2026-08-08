from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_publication_impact_v12 import (
    CONTRACT_PATH,
    V11_RECEIPT_FILE_SHA256,
    V11_REQUEST_FILE_SHA256,
    _check_self_hash,
    _validate_safe,
    _validate_schema,
    _validate_semantics,
    validate,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def _contract() -> dict[str, object]:
    return json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))


def test_v12_validates_and_binds_unchanged_v11_request_and_receipt() -> None:
    result = validate(ROOT)
    contract = _contract()

    assert result["status"] == "PASS"
    assert contract["v11_binding"]["request"]["file_sha256"] == V11_REQUEST_FILE_SHA256
    assert contract["v11_binding"]["receipt"]["file_sha256"] == V11_RECEIPT_FILE_SHA256
    assert contract["authorization"] == {
        "adopted_for_execution": False,
        "launch_allowed": False,
        "measured_retrieval_allowed": False,
        "provider_contact_allowed": False,
        "selection_open": False,
        "final_open": False,
    }
    assert set(contract["counters"].values()) == {0}


def test_v12_freezes_out_recall_primary_and_ndcg_secondaries() -> None:
    analysis = _contract()["analysis"]
    outcomes = analysis["outcomes"]

    assert outcomes["primary"] == "out_recall_at_100"
    assert outcomes["secondary"] == ["out_ndcg_at_100", "out_ndcg_at_10"]
    assert outcomes["evaluation_unit"] == "patent_family"
    assert outcomes["aggregation"] == "macro_over_eligible_out_queries"
    assert outcomes["cutoff"] == 100
    assert analysis["statistics"]["bootstrap_resamples"] == 10000
    assert analysis["statistics"]["superiority_rule"] == "paired_bootstrap_95ci_lower_gt_zero"


def test_v12_separates_development_selection_and_confirmation() -> None:
    boundary = _contract()["analysis"]["development_confirmation_boundary"]

    assert boundary["rep_dev_role"].startswith("exploratory")
    assert boundary["harness_dev_role"].startswith("exploratory")
    assert boundary["selection_125_role"] == "one_time_finalist_selection_not_confirmation"
    assert boundary["final_872_role"] == "sole_confirmatory_evaluation"
    assert boundary["post_selection_or_final_mutation_allowed"] is False


def test_v12_requires_fair_exposure_interaction_complementarity_and_operations() -> None:
    analysis = _contract()["analysis"]

    assert analysis["candidate_selection"]["max_cell_promotion_allowed"] is False
    assert analysis["candidate_exposure"]["same_total_candidate_depth_required"] is True
    assert analysis["candidate_exposure"]["oracle_metrics_role"] == "frozen_pool_diagnostic_not_deployed_result"
    assert analysis["interaction"]["matrix"] == "program_by_arm_within_arm_and_cross_arm_deltas"
    assert analysis["complementarity"]["equal_depth_union_against_best_single_required"] is True
    assert analysis["operational"]["ranking_replay_is_not_latency_variance_evidence"] is True


def test_v12_rejects_rehashed_semantic_tampering() -> None:
    contract = _contract()
    tampered = copy.deepcopy(contract)
    tampered["analysis"]["candidate_selection"]["max_cell_promotion_allowed"] = True
    tampered["contract_sha256"] = canonical_sha256(
        {key: value for key, value in tampered.items() if key != "contract_sha256"}
    )

    _validate_schema(tampered, ROOT)
    _check_self_hash(tampered)
    with pytest.raises(ValueError, match="max-cell"):
        _validate_semantics(tampered)


def test_v12_rejects_protected_or_secret_like_content() -> None:
    contract = _contract()
    unsafe = copy.deepcopy(contract)
    unsafe["claim_boundary"] = "Bearer abcdefghijklmnopqrstuvwxyz"

    with pytest.raises(ValueError, match="secret-like"):
        _validate_safe(unsafe)
