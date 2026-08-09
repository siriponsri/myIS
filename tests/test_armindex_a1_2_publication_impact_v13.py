from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_publication_impact_v13 import (
    CONTRACT_PATH,
    U011_FILE_SHA256,
    V12_FILE_SHA256,
    _check_self_hash,
    _validate_schema,
    _validate_semantics,
    validate,
)
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def _contract() -> dict[str, object]:
    return json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))


def _rehash(value: dict[str, object]) -> dict[str, object]:
    value["contract_sha256"] = canonical_sha256(
        {key: item for key, item in value.items() if key != "contract_sha256"}
    )
    return value


def test_v13_validates_and_preserves_v12_and_historical_metric_source() -> None:
    result = validate(ROOT)
    contract = _contract()

    assert result["status"] == "PASS"
    assert contract["v12_binding"]["file_sha256"] == V12_FILE_SHA256
    assert contract["historical_metric_reconciliation"]["source"]["file_sha256"] == U011_FILE_SHA256
    assert contract["historical_metric_reconciliation"]["resolution"] == (
        "additive_scope_specific_metric_supersession_without_source_rewrite"
    )


def test_v13_freezes_candidate_exposure_identity_and_metric_hierarchy() -> None:
    contract = _contract()

    assert contract["study_identity"]["a1_2_study_type"] == (
        "candidate_exposure_and_representation_screening"
    )
    assert contract["study_identity"]["retriever_family_effects"] == (
        "pre_registered_family_grouped_arm_contrasts"
    )
    assert contract["analysis"]["outcomes"]["primary"] == "out_recall_at_100"
    assert contract["analysis"]["outcomes"]["secondary"] == [
        "out_ndcg_at_100", "out_ndcg_at_10",
    ]


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("analysis", "candidate_selection", "max_cell_promotion_allowed"), True),
        (("analysis", "candidate_exposure", "same_total_candidate_depth_required"), False),
        (("analysis", "complementarity", "equal_depth_union_against_best_single_required"), False),
        (("analysis", "interaction", "universal_causal_claim_allowed"), True),
        (("analysis", "operational", "resource_sampling_cadence_bound"), False),
        (("study_identity", "retriever_family_effects"), "unregistered"),
    ],
)
def test_v13_rejects_rehashed_tampering_of_every_analysis_family(
    path: tuple[str, ...], replacement: object
) -> None:
    tampered = copy.deepcopy(_contract())
    target: dict[str, object] = tampered
    for key in path[:-1]:
        target = target[key]  # type: ignore[assignment]
    target[path[-1]] = replacement
    tampered = _rehash(tampered)

    with pytest.raises(ValueError, match="schema failure"):
        _validate_schema(tampered, ROOT)
    _check_self_hash(tampered)
    with pytest.raises(ValueError):
        _validate_semantics(tampered)


def test_v13_keeps_development_only_and_zero_counters() -> None:
    contract = _contract()

    assert contract["study_identity"]["evidence_stage"] == "development_diagnostic_evidence_only"
    assert contract["study_identity"]["publication_claim_before_final_allowed"] is False
    assert contract["analysis"]["development_confirmation_boundary"]["selection_125_role"] == (
        "one_time_finalist_selection_not_confirmation"
    )
    assert contract["analysis"]["development_confirmation_boundary"]["final_872_role"] == (
        "sole_confirmatory_evaluation"
    )
    assert set(contract["counters"].values()) == {0}
