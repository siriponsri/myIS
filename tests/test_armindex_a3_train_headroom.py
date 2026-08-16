from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.armindex.a3_train_headroom import (
    AUTHORITY_FILE_SHA256,
    AUTHORITY_ID,
    AUTHORITY_STATE,
    FROZEN_A2_BINDINGS,
    SPLIT_DECISION_SHA256,
    TrainHeadroomError,
    authorize_harness_dev_headroom,
    build_harness_dev_headroom_diagnostic,
    build_train_headroom_diagnostic,
    validate_train_headroom_inputs,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")


def _receipt(value: dict[str, object]) -> dict[str, object]:
    value["receipt_sha256"] = canonical_sha256(value)
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
    closeout = _receipt(
        {
            "schema_version": "myis.armindex-a2-execution-closeout-receipt.v1",
            "receipt_id": "a2-goal004-20260816-005-execution-closeout-v1",
            "attempt_id": "a2-goal004-20260816-005",
            "status": "PASS_A2_EXECUTION_CLOSEOUT",
            "evidence_class": "measured_development_aggregate",
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
            "arm_winner_receipt_sha256s": {
                arm_id: canonical_sha256({"winner_selection": arm_id})
                for arm_id in ARM_IDS
            },
            "candidate_result_set_sha256": canonical_sha256({"candidate_results": 52}),
            "safe_return_receipt_sha256": canonical_sha256({"safe_return": True}),
            "terminal_checkpoint_sha256": canonical_sha256(
                {"terminal_checkpoint": True}
            ),
            "workers_reaped": True,
            "protected_scan_passed": True,
            "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
            "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
            "claim_evidence_pointers": [
                "campaigns/armindex-multiretriever-v2/evidence/a2-closeout.json"
            ],
            "freeze_bindings": dict(FROZEN_A2_BINDINGS),
        }
    )
    incumbent = _receipt(
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
                for index, arm_id in enumerate(ARM_IDS)
            ],
        }
    )
    winners = []
    for index, arm_id in enumerate(ARM_IDS):
        train_receipt = _receipt(
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
                "membership_commitment_sha256": canonical_sha256(
                    {"membership": "train-250"}
                ),
                "qrels_commitment_sha256": canonical_sha256({"qrels": "train-250"}),
                "model_runtime_sha256": canonical_sha256({"runtime": arm_id}),
                "metric_denominator": incumbent["metric_denominator"],
                "freeze_bindings": dict(FROZEN_A2_BINDINGS),
                "winner_selection_receipt_sha256": canonical_sha256(
                    {"winner_selection": arm_id}
                ),
                "selection_accessed": False,
                "final_accessed": False,
                "metric": _metric(arm_id, 0.24 + index / 100),
            }
        )
        winners.append(
            {
                "arm_id": arm_id,
                "winner_program_sha256": canonical_sha256({"winner": arm_id}),
                "winner_selection_receipt_sha256": canonical_sha256(
                    {"winner_selection": arm_id}
                ),
                "candidate_frozen": True,
                "train_aggregate_receipt": train_receipt,
            }
        )
    return {
        "schema_version": "myis.armindex-a3-train-headroom-input.v1",
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": AUTHORITY_FILE_SHA256,
        "authority_state": AUTHORITY_STATE,
        "a2_closeout": closeout,
        "a1_incumbent_aggregate": incumbent,
        "winners": winners,
    }


def _schema(name: str) -> dict[str, object]:
    return json.loads(
        (ROOT / "schemas" / "armindex" / name).read_text(encoding="utf-8")
    )


def _hdev_payload() -> dict[str, object]:
    authorization = authorize_harness_dev_headroom(_payload())
    arm_results = []
    for index, arm in enumerate(authorization["bindings"]["arms"]):
        arm_results.append(
            _receipt(
                {
                    "schema_version": "myis.armindex-a3-harness-dev-aggregate-receipt.v1",
                    "status": "PASS",
                    "evidence_class": "measured_harness_dev_aggregate",
                    "scientific_authority": True,
                    "scope": "HARNESS-DEV-100",
                    "harness_dev_query_count": 100,
                    "arm_id": arm["arm_id"],
                    "winner_program_sha256": arm["winner_program_sha256"],
                    "incumbent_program_sha256": arm["a1_incumbent_program_sha256"],
                    "authorization_sha256": authorization["authorization_sha256"],
                    "selection_accessed": False,
                    "final_accessed": False,
                    "comparison": {
                        "metric_name": "recall_at_100_out",
                        "winner_value": 0.25 + index / 100,
                        "incumbent_value": 0.20 + index / 100,
                    },
                }
            )
        )
    return {
        "schema_version": "myis.armindex-a3-harness-dev-headroom-input.v1",
        "authorization": authorization,
        "arm_results": arm_results,
    }


def test_train_headroom_validates_and_emits_descriptive_aggregate_report() -> None:
    payload = _payload()
    input_schema = _schema("a3-train-headroom-input.v1.json")
    output_schema = _schema("a3-train-headroom-diagnostic.v1.json")
    Draft202012Validator.check_schema(input_schema)
    Draft202012Validator.check_schema(output_schema)
    assert not list(Draft202012Validator(input_schema).iter_errors(payload))
    a2_closeout_schema = _schema("a2-execution-closeout-receipt.v1.json")
    assert not list(
        Draft202012Validator(a2_closeout_schema).iter_errors(payload["a2_closeout"])
    )

    assert validate_train_headroom_inputs(payload) == payload
    report = build_train_headroom_diagnostic(payload)

    assert not list(Draft202012Validator(output_schema).iter_errors(report))
    assert report["status"] == "DESCRIPTIVE_ONLY"
    assert report["authority_state"] == "PENDING_A2_CLOSEOUT"
    assert [
        row["winner_minus_incumbent"] for row in report["headroom_by_arm"]
    ] == pytest.approx([0.04] * 5)
    assert report["safety"] == {
        "aggregate_only": True,
        "candidate_mutation_permitted": False,
        "retrieval_permitted": False,
        "rep_dev_permitted": False,
        "harness_dev_permitted": False,
        "selection_permitted": False,
        "final_permitted": False,
        "spend_permitted": False,
    }
    unsigned = {
        key: value for key, value in report.items() if key != "diagnostic_sha256"
    }
    assert report["diagnostic_sha256"] == canonical_sha256(unsigned)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["a2_closeout"].update(
                {"evidence_class": "synthetic_fixture"}
            ),
            "A2 closeout",
        ),
        (lambda value: value["winners"].pop(), "exactly five"),
        (
            lambda value: value["winners"][0].update({"arm_id": "ARM-02"}),
            "does not match",
        ),
        (
            lambda value: value["winners"][0]["train_aggregate_receipt"].update(
                {"scope": "REP-DEV"}
            ),
            "Train-250",
        ),
        (
            lambda value: value["a2_closeout"].update({"matched_candidate_count": 39}),
            "valid measured aggregate PASS receipt",
        ),
        (
            lambda value: value["a2_closeout"]["freeze_bindings"].update(
                {"lock_sha256": canonical_sha256({"wrong": "lock"})}
            ),
            "frozen A2 manifest",
        ),
        (
            lambda value: value["winners"][0]["train_aggregate_receipt"].update(
                {"evaluator_sha256": canonical_sha256({"wrong": "evaluator"})}
            ),
            "outside the allowed scope",
        ),
    ],
)
def test_train_headroom_rejects_synthetic_incomplete_or_incompatible_inputs(
    mutate, message: str
) -> None:
    payload = _payload()
    mutate(payload)

    with pytest.raises(TrainHeadroomError, match=message):
        build_train_headroom_diagnostic(payload)


def test_train_headroom_rejects_protected_payload_before_any_report() -> None:
    payload = _payload()
    payload["a1_incumbent_aggregate"]["query_ids"] = ["forbidden"]

    with pytest.raises(TrainHeadroomError, match="protected payload key"):
        build_train_headroom_diagnostic(payload)


def test_hdev_authorization_and_primary_diagnostic_bind_all_frozen_arms() -> None:
    authorization_schema = _schema("a3-harness-dev-headroom-authorization.v1.json")
    input_schema = _schema("a3-harness-dev-headroom-input.v1.json")
    diagnostic_schema = _schema("a3-harness-dev-headroom-diagnostic.v1.json")
    Draft202012Validator.check_schema(authorization_schema)
    Draft202012Validator.check_schema(input_schema)
    Draft202012Validator.check_schema(diagnostic_schema)

    authorization = authorize_harness_dev_headroom(_payload())
    assert not list(
        Draft202012Validator(authorization_schema).iter_errors(authorization)
    )
    assert authorization["status"] == "POST_A2_CLOSEOUT_HDEV100_AUTHORIZED"
    assert authorization["closeout_state"] == "A2_CLOSEOUT_BOUND"
    assert authorization["bindings"]["authority_id"] == AUTHORITY_ID
    assert authorization["bindings"]["authority_file_sha256"] == AUTHORITY_FILE_SHA256
    assert authorization["safety"]["repository_execution_permitted"] is False

    hdev_payload = _hdev_payload()
    assert not list(Draft202012Validator(input_schema).iter_errors(hdev_payload))
    report = build_harness_dev_headroom_diagnostic(hdev_payload)
    assert not list(Draft202012Validator(diagnostic_schema).iter_errors(report))
    assert report["status"] == "PRIMARY_HARNESS_DEV_DIAGNOSTIC"
    assert report["scope"] == "HARNESS-DEV-100"
    assert [
        row["winner_minus_incumbent"] for row in report["headroom_by_arm"]
    ] == pytest.approx([0.05] * 5)


def test_hdev_diagnostic_rejects_non_hdev_or_unbound_aggregate_results() -> None:
    payload = _hdev_payload()
    payload["arm_results"][0]["scope"] = "Train-250"

    with pytest.raises(TrainHeadroomError, match="outside the authorized scope"):
        build_harness_dev_headroom_diagnostic(payload)


def test_train_headroom_authority_stays_pending_and_non_executable() -> None:
    authority_path = (
        ROOT / "control" / "armindex" / "a3" / "a3.1-train-headroom-authority.v1.json"
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority_schema = _schema("a3-train-headroom-authority.v1.json")
    Draft202012Validator.check_schema(authority_schema)
    assert not list(Draft202012Validator(authority_schema).iter_errors(authority))

    assert authority["authority_state"] == "PENDING_A2_CLOSEOUT"
    assert authority["authority_id"] == AUTHORITY_ID
    assert (
        hashlib.sha256(authority_path.read_bytes()).hexdigest() == AUTHORITY_FILE_SHA256
    )
    assert authority["frozen_a2_bindings"] == FROZEN_A2_BINDINGS
    assert authority["execution_permitted"] is False
    authority_unsigned = {
        key: value for key, value in authority.items() if key != "authority_sha256"
    }
    assert authority["authority_sha256"] == canonical_sha256(authority_unsigned)
    assert set(authority["pre_closeout_forbidden_actions"]) == {
        "candidate_mutation",
        "retrieval",
        "REP-DEV",
        "HDEV-100",
        "Selection",
        "Final",
        "provider_contact",
        "remote_execution",
        "spend",
    }
