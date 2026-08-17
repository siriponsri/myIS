from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.armindex.a3_three_primary_train_headroom import (
    ALL_ARM_IDS,
    AUTHORITY_FILE_SHA256,
    AUTHORITY_ID,
    AUTHORITY_STATE,
    FROZEN_A2_BINDINGS,
    PRIMARY_ARM_IDS,
    SPLIT_DECISION_SHA256,
    ThreePrimaryTrainHeadroomError,
    build_three_primary_train_headroom_diagnostic,
    validate_three_primary_train_headroom_inputs,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def _self_hashed(value: dict[str, object], field: str = "receipt_sha256") -> dict[str, object]:
    value[field] = canonical_sha256(value)
    return value


def _metric(arm_id: str, value: float) -> dict[str, object]:
    return {"arm_id": arm_id, "metric_name": "recall_at_100_out", "metric_value": value}


def _incumbent_metric(arm_id: str, value: float) -> dict[str, object]:
    return {
        "arm_id": arm_id,
        "incumbent_program_sha256": canonical_sha256({"incumbent": arm_id}),
        "metric_name": "recall_at_100_out",
        "metric_value": value,
    }


def _payload() -> dict[str, object]:
    primary_receipts = {
        arm_id: canonical_sha256({"winner_selection": arm_id})
        for arm_id in PRIMARY_ARM_IDS
    }
    closeout = _self_hashed(
        {
            "schema_version": "myis.armindex-a2-execution-closeout-receipt.v2",
            "status": "PASS_A2_EXECUTION_CLOSEOUT",
            "evidence_class": "measured_development_aggregate",
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
            "measured_candidate_count": 44,
            "dormant_conditional_reserve_count": 8,
            "failed_candidate_count": 0,
            "primary_winner_receipt_sha256s": primary_receipts,
            "diagnostic_no_winner_receipt_sha256s": {
                arm_id: canonical_sha256({"diagnostic_no_winner": arm_id})
                for arm_id in ("ARM-01", "ARM-02")
            },
            "amendment_sha256": canonical_sha256({"three_primary": True}),
            "candidate_result_set_sha256": canonical_sha256({"candidate_results": 52}),
            "safe_return_receipt_sha256": canonical_sha256({"safe_return": True}),
            "terminal_checkpoint_sha256": canonical_sha256({"terminal_checkpoint": True}),
            "freeze_bindings": dict(FROZEN_A2_BINDINGS),
        }
    )
    audit = _self_hashed(
        {
            "schema_version": "myis.armindex-a2-result-integrity-audit.v2",
            "status": "PASS_A2_RESULT_AUDIT",
            "closeout": {"receipt_sha256": closeout["receipt_sha256"]},
            "coverage": {"receipt_sha256": canonical_sha256({"coverage": 52})},
            "protection": {"aggregate_only_scan_passed": True},
            "safe_return": {"receipt_sha256": closeout["safe_return_receipt_sha256"]},
            "terminal_checkpoint": {
                "receipt_sha256": closeout["terminal_checkpoint_sha256"]
            },
        },
        "audit_sha256",
    )
    incumbent = _self_hashed(
        {
            "schema_version": "myis.armindex-a1-incumbent-aggregate-receipt.v1",
            "status": "PASS",
            "evidence_class": "measured_development_aggregate",
            "scientific_authority": True,
            "frozen": True,
            "scope": "Train-250",
            "train_query_count": 250,
            "split_id": "Train-250",
            "split_decision_sha256": SPLIT_DECISION_SHA256,
            "evaluator_sha256": canonical_sha256({"evaluator": "train"}),
            "metric_name": "recall_at_100_out",
            "metric_denominator": "eligible_relevant_family_query_pairs",
            "arm_metrics": [
                _incumbent_metric(arm_id, 0.20 + index / 100)
                for index, arm_id in enumerate(ALL_ARM_IDS)
            ],
        }
    )
    winners = []
    for index, arm_id in enumerate(PRIMARY_ARM_IDS):
        train_receipt = _self_hashed(
            {
                "schema_version": "myis.armindex-a3-owner-local-fixed-diagnostic-receipt.v1",
                "status": "PASS",
                "evidence_class": "measured_post_a2_fixed_diagnostic_aggregate",
                "scientific_authority": True,
                "scope": "Train-250",
                "train_query_count": 250,
                "split_id": "Train-250",
                "split_decision_sha256": SPLIT_DECISION_SHA256,
                "evaluator_sha256": incumbent["evaluator_sha256"],
                "membership_commitment_sha256": canonical_sha256({"membership": "train-250"}),
                "qrels_commitment_sha256": canonical_sha256({"qrels": "train-250"}),
                "model_runtime_sha256": canonical_sha256({"runtime": arm_id}),
                "metric_denominator": incumbent["metric_denominator"],
                "freeze_bindings": dict(FROZEN_A2_BINDINGS),
                "winner_selection_receipt_sha256": primary_receipts[arm_id],
                "selection_accessed": False,
                "final_accessed": False,
                "metric": _metric(arm_id, 0.25 + index / 100),
            }
        )
        winners.append(
            {
                "arm_id": arm_id,
                "winner_program_sha256": canonical_sha256({"winner": arm_id}),
                "winner_selection_receipt_sha256": primary_receipts[arm_id],
                "candidate_frozen": True,
                "train_aggregate_receipt": train_receipt,
            }
        )
    return {
        "schema_version": "myis.armindex-a3-three-primary-train-headroom-input.v1",
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": AUTHORITY_FILE_SHA256,
        "authority_state": AUTHORITY_STATE,
        "a2_closeout": closeout,
        "a2_result_integrity_audit": audit,
        "a1_incumbent_aggregate": incumbent,
        "winners": winners,
    }


def _schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / "schemas" / "armindex" / name).read_text(encoding="utf-8"))


def test_three_primary_train_headroom_validates_and_emits_aggregate_report() -> None:
    payload = _payload()
    input_schema = _schema("a3-three-primary-train-headroom-input.v1.json")
    output_schema = _schema("a3-three-primary-train-headroom-diagnostic.v1.json")
    Draft202012Validator.check_schema(input_schema)
    Draft202012Validator.check_schema(output_schema)
    assert not list(Draft202012Validator(input_schema).iter_errors(payload))
    assert validate_three_primary_train_headroom_inputs(payload) == payload

    report = build_three_primary_train_headroom_diagnostic(payload)
    assert not list(Draft202012Validator(output_schema).iter_errors(report))
    assert [row["arm_id"] for row in report["headroom_by_arm"]] == list(PRIMARY_ARM_IDS)
    assert [row["winner_minus_incumbent"] for row in report["headroom_by_arm"]] == pytest.approx(
        [0.03, 0.03, 0.03]
    )
    assert report["safety"]["aggregate_only"] is True
    assert report["safety"]["harness_dev_permitted"] is False
    assert report["diagnostic_sha256"] == canonical_sha256(
        {key: value for key, value in report.items() if key != "diagnostic_sha256"}
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["winners"].pop(), "exactly three"),
        (lambda value: value["winners"][0].update({"arm_id": "ARM-01"}), "diagnostic arms"),
        (
            lambda value: value["a2_closeout"].update({"measured_candidate_count": 43}),
            "A2 amended closeout",
        ),
        (
            lambda value: value["a2_result_integrity_audit"]["protection"].update(
                {"aggregate_only_scan_passed": False}
            ),
            "result-integrity audit",
        ),
        (
            lambda value: value["winners"][0]["train_aggregate_receipt"].update(
                {"scope": "REP-DEV"}
            ),
            "Train-250 receipt",
        ),
    ],
)
def test_three_primary_headroom_rejects_invalid_amended_inputs(mutate, message: str) -> None:
    payload = _payload()
    mutate(payload)
    with pytest.raises(ThreePrimaryTrainHeadroomError, match=message):
        build_three_primary_train_headroom_diagnostic(payload)


def test_three_primary_headroom_rejects_protected_payload() -> None:
    payload = _payload()
    payload["a1_incumbent_aggregate"]["query_ids"] = ["forbidden"]
    with pytest.raises(ThreePrimaryTrainHeadroomError, match="protected payload key"):
        build_three_primary_train_headroom_diagnostic(payload)


def test_three_primary_authority_and_manifest_are_pending_and_hash_bound() -> None:
    authority_path = ROOT / "control" / "armindex" / "a3" / "a3.1-three-primary-train-headroom-authority.v1.json"
    manifest_path = ROOT / "control" / "armindex" / "a3" / "a3.1-three-primary-train-headroom-bundle-manifest.v1.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    authority_schema = _schema("a3-three-primary-train-headroom-authority.v1.json")
    manifest_schema = _schema("a3-three-primary-train-headroom-bundle-manifest.v1.json")
    Draft202012Validator.check_schema(authority_schema)
    Draft202012Validator.check_schema(manifest_schema)
    assert not list(Draft202012Validator(authority_schema).iter_errors(authority))
    assert not list(Draft202012Validator(manifest_schema).iter_errors(manifest))
    assert hashlib.sha256(authority_path.read_bytes()).hexdigest() == AUTHORITY_FILE_SHA256
    assert authority["primary_advancement_arms"] == list(PRIMARY_ARM_IDS)
    assert authority["execution_permitted"] is False
    assert authority["authority_sha256"] == canonical_sha256(
        {key: value for key, value in authority.items() if key != "authority_sha256"}
    )
    assert manifest["authority_file_sha256"] == AUTHORITY_FILE_SHA256
    assert [row["arm_id"] for row in manifest["primary_advancement_arms"]] == list(PRIMARY_ARM_IDS)
    assert manifest["manifest_sha256"] == canonical_sha256(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
