from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from myis_research.armindex.a3_three_primary_execution import (
    A3ThreePrimaryExecutionError,
    PRIMARY_ARMS,
    build_three_primary_execution_contract,
    build_three_primary_runtime_bindings,
    validate_fixed_union_contract,
    validate_three_primary_admission,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _self_hash(value: dict[str, object], field: str) -> dict[str, object]:
    unsigned = {key: item for key, item in value.items() if key != field}
    value[field] = canonical_sha256(unsigned)
    return value


def _static_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        _load("control/budgets/armindex-budget-extension-a3-three-primary.v1.json"),
        _load("control/armindex/a3/a3-three-primary-preparation-authority.v1.json"),
        _load("control/armindex/a3/a3-three-primary-preparation-manifest.v1.json"),
    )


def _admission(
    budget: dict[str, object], authority: dict[str, object], manifest: dict[str, object]
) -> dict[str, object]:
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-admission.v1",
            "status": "PASS_A3_FRESH_ADMISSION",
            "budget_extension_sha256": budget["budget_extension_sha256"],
            "authority_sha256": authority["authority_sha256"],
            "manifest_sha256": manifest["manifest_sha256"],
            "a2_closeout_receipt_sha256": authority["a2_predecessor_bindings"][
                "a2_closeout_receipt_sha256"
            ],
            "provider_identity_sha256": "1" * 64,
            "all_fee_quote_sha256": "2" * 64,
            "campaign_budget_amendment_receipt_sha256": "3" * 64,
            "quote_age_seconds": 900,
            "target_ttl_seconds": 48 * 60 * 60,
            "a3_projected_total_usd": "35.00",
            "campaign_projected_total_usd": "180.00",
            "admission_sha256": "",
        },
        "admission_sha256",
    )


def _runtime_bindings() -> dict[str, object]:
    budget, authority, manifest = _static_inputs()
    return build_three_primary_runtime_bindings(
        budget,
        authority,
        manifest,
        _admission(budget, authority, manifest),
        {
            arm_id: {
                "winner_program_sha256": str(index + 4) * 64,
                "winner_selection_receipt_sha256": authority["a2_predecessor_bindings"][
                    "primary_winner_receipt_sha256s"
                ][arm_id],
            }
            for index, arm_id in enumerate(PRIMARY_ARMS)
        },
        {arm_id: str(index + 7) * 64 for index, arm_id in enumerate(PRIMARY_ARMS)},
    )


def _fixed_union(runtime_bindings_sha256: str) -> dict[str, object]:
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-fixed-union.v1",
            "status": "frozen_before_evaluation",
            "frozen_runtime_bindings_sha256": runtime_bindings_sha256,
            "evaluation_depth_by_arm": {arm_id: 100 for arm_id in PRIMARY_ARMS},
            "control_ids": [
                "best_single",
                "all_primary_rrf60",
                "top_two_rrf60",
                "top_three_rrf60",
                "commercial_only_fixed_union",
            ],
            "commercial_only_fixed_union_arm_ids": ["ARM-04", "ARM-05"],
            "aggregate_only": True,
            "fixed_union_sha256": "",
        },
        "fixed_union_sha256",
    )


def _harness_batch(runtime_bindings_sha256: str) -> dict[str, object]:
    roles = (
        "quality_exploit",
        "cost_latency_ablation",
        "routing_hypothesis",
        "diversity_profile",
    )
    candidate_ids = [f"a3-i01-c{index}" for index in range(1, 5)]
    candidates: list[dict[str, object]] = []
    for index, (candidate_id, role) in enumerate(zip(candidate_ids, roles, strict=True)):
        configuration = _self_hash(
            {
                "schema_version": "myis.armindex-harness.v2",
                "harness_id": f"a3-harness-{index + 1}",
                "profile": "BALANCED",
                "frozen_bindings_sha256": runtime_bindings_sha256,
                "arm_ids": list(PRIMARY_ARMS),
                "invocation_order": list(PRIMARY_ARMS),
                "execution_mode": "parallel",
                "initial_depth_by_arm": {arm_id: 100 for arm_id in PRIMARY_ARMS},
                "maximum_depth_by_arm": {arm_id: 100 for arm_id in PRIMARY_ARMS},
                "fusion": {
                    "method": "rrf",
                    "rrf_k": 60,
                    "weights": {arm_id: 1.0 for arm_id in PRIMARY_ARMS},
                },
                "routing": [],
                "early_stop": {
                    "max_escalations": 2,
                    "score_margin": 0.1,
                    "rank_stability": 0.9,
                },
                "cache_policy": "frozen_read_only",
                "latency_profile": "balanced",
                "runtime_features": [],
                "config_sha256": "",
            },
            "config_sha256",
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "role": role,
                "hypothesis": f"bounded A3 fixture {index + 1}",
                "matched_ablation_id": (
                    candidate_ids[1] if index == 0 else candidate_ids[0] if index == 1 else None
                ),
                "scientific_payload_sha256": str(index + 1) * 64,
                "configuration": configuration,
                "verifier_status": "accepted",
            }
        )
    return _self_hash(
        {
            "schema_version": "myis.armindex-harness-batch.v1",
            "batch_id": "a3-i01",
            "iteration": 1,
            "frozen_bindings_sha256": runtime_bindings_sha256,
            "status": "frozen_before_evaluation",
            "candidates": candidates,
            "batch_sha256": "",
        },
        "batch_sha256",
    )


def test_post_admission_contract_is_exact_three_primary_and_aggregate_safe() -> None:
    bindings = _runtime_bindings()
    fixed_union = _fixed_union(bindings["runtime_bindings_sha256"])
    batch = _harness_batch(bindings["runtime_bindings_sha256"])
    contract = build_three_primary_execution_contract(bindings, fixed_union, [batch])

    assert contract["status"] == "READY_FOR_POST_ADMISSION_EXECUTION"
    assert len(contract["transfer_matrix"]) == 9
    assert sum(row["source_arm_id"] != row["target_arm_id"] for row in contract["transfer_matrix"]) == 6
    assert contract["harness_batch_sha256s"] == [batch["batch_sha256"]]
    assert contract["provider_contact_performed"] is False
    assert contract["remote_execution_performed"] is False
    assert contract["selection_permitted"] is False
    assert contract["final_permitted"] is False
    assert validate_fixed_union_contract(
        fixed_union, runtime_bindings_sha256=bindings["runtime_bindings_sha256"]
    ) == fixed_union

    with pytest.raises(A3ThreePrimaryExecutionError, match="requires one to three"):
        build_three_primary_execution_contract(bindings, fixed_union, [])


def test_complete_harnessopt_batch_is_required_to_remain_three_primary() -> None:
    bindings = _runtime_bindings()
    fixed_union = _fixed_union(bindings["runtime_bindings_sha256"])
    batch = _harness_batch(bindings["runtime_bindings_sha256"])
    contract = build_three_primary_execution_contract(bindings, fixed_union, [batch])
    assert contract["harness_batch_sha256s"] == [batch["batch_sha256"]]

    invalid = deepcopy(batch)
    config = invalid["candidates"][0]["configuration"]
    config["arm_ids"] = ["ARM-01"]
    config["invocation_order"] = ["ARM-01"]
    config["initial_depth_by_arm"] = {"ARM-01": 100}
    config["maximum_depth_by_arm"] = {"ARM-01": 100}
    config["fusion"]["weights"] = {"ARM-01": 1.0}
    config["config_sha256"] = canonical_sha256(
        {key: item for key, item in config.items() if key != "config_sha256"}
    )
    invalid["batch_sha256"] = canonical_sha256(
        {key: item for key, item in invalid.items() if key != "batch_sha256"}
    )
    with pytest.raises(A3ThreePrimaryExecutionError, match="diagnostic arms"):
        build_three_primary_execution_contract(bindings, fixed_union, [invalid])


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.__setitem__("status", "PENDING_A3_ADMISSION"), "passing fresh admission"),
        (lambda value: value.__setitem__("quote_age_seconds", 901), "quote age"),
        (lambda value: value.__setitem__("a3_projected_total_usd", "35.01"), "A3 projected total"),
    ],
)
def test_admission_fails_closed_on_missing_or_over_cap_evidence(mutate, message: str) -> None:
    budget, authority, manifest = _static_inputs()
    admission = _admission(budget, authority, manifest)
    mutate(admission)
    with pytest.raises(A3ThreePrimaryExecutionError, match=message):
        validate_three_primary_admission(
            admission, budget=budget, authority=authority, manifest=manifest
        )


def test_runtime_contract_rejects_diagnostic_arm_and_unequal_union_depth() -> None:
    bindings = _runtime_bindings()
    bad_bindings = deepcopy(bindings)
    bad_bindings["winner_bindings"]["ARM-01"] = bad_bindings["winner_bindings"].pop("ARM-03")
    with pytest.raises(A3ThreePrimaryExecutionError, match="three primary arms"):
        build_three_primary_execution_contract(
            bad_bindings,
            _fixed_union(bindings["runtime_bindings_sha256"]),
            [_harness_batch(bindings["runtime_bindings_sha256"])],
        )

    bad_union = _fixed_union(bindings["runtime_bindings_sha256"])
    bad_union["evaluation_depth_by_arm"]["ARM-05"] = 99
    with pytest.raises(A3ThreePrimaryExecutionError, match="equal depth"):
        validate_fixed_union_contract(
            bad_union, runtime_bindings_sha256=bindings["runtime_bindings_sha256"]
        )
