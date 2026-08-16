"""Aggregate-only, post-A2 descriptive Train-250 headroom diagnostic."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite
from pathlib import Path
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
AUTHORITY_STATE = "PENDING_A2_CLOSEOUT"
AUTHORITY_ID = "A3.1_TRAIN_HEADROOM_POST_A2"
AUTHORITY_FILE_SHA256 = (
    "7b89ac70f944869206ebc6d2646a730820c22ab6e8666a04c92451d4c9164610"
)
FROZEN_A2_BINDINGS = {
    "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
    "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
    "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
}
SPLIT_DECISION_SHA256 = (
    "87efd2ef78400b6025b5cfe153ff5e8b165ea4fad784d0a99979e514e6bb2202"
)
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_METRIC_NAME = "recall_at_100_out"


class TrainHeadroomError(ValueError):
    """Raised when the descriptive diagnostic lacks compatible aggregate evidence."""


def validate_train_headroom_inputs(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate only safe, complete, hash-bound post-closeout aggregate inputs."""

    payload = deepcopy(dict(value))
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise TrainHeadroomError(str(error)) from error
    _require_exact_keys(
        payload,
        {
            "schema_version",
            "authority_id",
            "authority_file_sha256",
            "authority_state",
            "a2_closeout",
            "a1_incumbent_aggregate",
            "winners",
        },
        "diagnostic input",
    )
    if payload["schema_version"] != "myis.armindex-a3-train-headroom-input.v1":
        raise TrainHeadroomError("unsupported Train-250 headroom input schema")
    if payload["authority_state"] != AUTHORITY_STATE:
        raise TrainHeadroomError(
            "Train-250 headroom diagnostic remains PENDING_A2_CLOSEOUT"
        )
    if (
        payload["authority_id"] != AUTHORITY_ID
        or payload["authority_file_sha256"] != AUTHORITY_FILE_SHA256
    ):
        raise TrainHeadroomError(
            "runtime input is not bound to the current static A3.1 authority file"
        )

    _validate_a2_closeout(payload["a2_closeout"])
    incumbent = _validate_a1_incumbent_aggregate(payload["a1_incumbent_aggregate"])
    _validate_winners(payload["winners"], incumbent, payload["a1_incumbent_aggregate"])
    if set(payload["a2_closeout"]["arm_winner_receipt_sha256s"].values()) != {
        winner["winner_selection_receipt_sha256"] for winner in payload["winners"]
    }:
        raise TrainHeadroomError(
            "A2 closeout winner receipt hashes do not bind the supplied frozen winners"
        )
    return payload


def build_train_headroom_diagnostic(value: Mapping[str, Any]) -> dict[str, Any]:
    """Produce an aggregate-only, non-promotional winner-minus-incumbent report."""

    payload = validate_train_headroom_inputs(value)
    incumbent_metrics = _validate_a1_incumbent_aggregate(
        payload["a1_incumbent_aggregate"]
    )
    rows = []
    bindings = []
    for winner in sorted(payload["winners"], key=lambda row: row["arm_id"]):
        receipt = winner["train_aggregate_receipt"]
        metric = float(receipt["metric"]["metric_value"])
        arm_id = winner["arm_id"]
        rows.append(
            {
                "arm_id": arm_id,
                "metric_name": _METRIC_NAME,
                "a1_incumbent_value": incumbent_metrics[arm_id]["metric_value"],
                "a2_winner_train_value": metric,
                "winner_minus_incumbent": metric
                - incumbent_metrics[arm_id]["metric_value"],
            }
        )
        bindings.append(
            {
                "arm_id": arm_id,
                "winner_program_sha256": winner["winner_program_sha256"],
                "train_aggregate_receipt_sha256": receipt["receipt_sha256"],
            }
        )

    diagnostic: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-train-headroom-diagnostic.v1",
        "status": "DESCRIPTIVE_ONLY",
        "authority_state": AUTHORITY_STATE,
        "scope": "Train-250",
        "bindings": {
            "authority_id": AUTHORITY_ID,
            "authority_file_sha256": AUTHORITY_FILE_SHA256,
            "a2_closeout_receipt_sha256": payload["a2_closeout"]["receipt_sha256"],
            "a1_incumbent_aggregate_receipt_sha256": payload["a1_incumbent_aggregate"][
                "receipt_sha256"
            ],
            "winner_receipts": bindings,
        },
        "headroom_by_arm": rows,
        "safety": {
            "aggregate_only": True,
            "candidate_mutation_permitted": False,
            "retrieval_permitted": False,
            "rep_dev_permitted": False,
            "harness_dev_permitted": False,
            "selection_permitted": False,
            "final_permitted": False,
            "spend_permitted": False,
        },
    }
    diagnostic["diagnostic_sha256"] = canonical_sha256(diagnostic)
    return diagnostic


def authorize_harness_dev_headroom(value: Mapping[str, Any]) -> dict[str, Any]:
    """Bind valid A2 closeout evidence before any separate HDEV-100 evaluation."""

    payload = validate_train_headroom_inputs(value)
    incumbents = _validate_a1_incumbent_aggregate(payload["a1_incumbent_aggregate"])
    authorization: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-harness-dev-headroom-authorization.v1",
        "status": "POST_A2_CLOSEOUT_HDEV100_AUTHORIZED",
        "authority_state": AUTHORITY_STATE,
        "closeout_state": "A2_CLOSEOUT_BOUND",
        "scope": "HARNESS-DEV-100",
        "bindings": {
            "authority_id": AUTHORITY_ID,
            "authority_file_sha256": AUTHORITY_FILE_SHA256,
            "a2_closeout_receipt_sha256": payload["a2_closeout"]["receipt_sha256"],
            "a1_incumbent_aggregate_receipt_sha256": payload["a1_incumbent_aggregate"][
                "receipt_sha256"
            ],
            "arms": [
                {
                    "arm_id": winner["arm_id"],
                    "winner_program_sha256": winner["winner_program_sha256"],
                    "a1_incumbent_program_sha256": incumbents[winner["arm_id"]][
                        "incumbent_program_sha256"
                    ],
                }
                for winner in sorted(payload["winners"], key=lambda row: row["arm_id"])
            ],
        },
        "safety": {
            "aggregate_only_return": True,
            "non_adaptive": True,
            "candidate_mutation_permitted": False,
            "selection_permitted": False,
            "final_permitted": False,
            "provider_permitted": False,
            "gpu_permitted": False,
            "spend_permitted": False,
            "repository_execution_permitted": False,
        },
    }
    authorization["authorization_sha256"] = canonical_sha256(authorization)
    return authorization


def build_harness_dev_headroom_diagnostic(value: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize same-scope HDEV-100 winner-versus-incumbent aggregate deltas."""

    payload = deepcopy(dict(value))
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise TrainHeadroomError(str(error)) from error
    _require_exact_keys(
        payload,
        {"schema_version", "authorization", "arm_results"},
        "HARNESS-DEV headroom input",
    )
    if payload["schema_version"] != "myis.armindex-a3-harness-dev-headroom-input.v1":
        raise TrainHeadroomError("unsupported HARNESS-DEV headroom input schema")
    authorization = _validate_harness_dev_authorization(payload["authorization"])
    results = _validate_harness_dev_results(payload["arm_results"], authorization)
    report: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-harness-dev-headroom-diagnostic.v1",
        "status": "PRIMARY_HARNESS_DEV_DIAGNOSTIC",
        "scope": "HARNESS-DEV-100",
        "bindings": {
            "authorization_sha256": authorization["authorization_sha256"],
            "a2_closeout_receipt_sha256": authorization["bindings"][
                "a2_closeout_receipt_sha256"
            ],
            "result_receipt_sha256s": [result["receipt_sha256"] for result in results],
        },
        "headroom_by_arm": [
            {
                "arm_id": result["arm_id"],
                "metric_name": _METRIC_NAME,
                "a1_incumbent_value": result["comparison"]["incumbent_value"],
                "a2_winner_value": result["comparison"]["winner_value"],
                "winner_minus_incumbent": result["comparison"]["winner_value"]
                - result["comparison"]["incumbent_value"],
            }
            for result in results
        ],
        "safety": {
            "aggregate_only": True,
            "non_adaptive": True,
            "candidate_mutation_permitted": False,
            "selection_permitted": False,
            "final_permitted": False,
            "spend_permitted": False,
        },
    }
    report["diagnostic_sha256"] = canonical_sha256(report)
    return report


def _validate_a2_closeout(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise TrainHeadroomError("A2 closeout must be an aggregate receipt mapping")
    _require_exact_keys(
        value,
        {
            "schema_version",
            "receipt_id",
            "attempt_id",
            "status",
            "evidence_class",
            "candidate_count",
            "matched_candidate_count",
            "conditional_reserve_candidate_count",
            "arm_winner_receipt_sha256s",
            "candidate_result_set_sha256",
            "safe_return_receipt_sha256",
            "terminal_checkpoint_sha256",
            "workers_reaped",
            "protected_scan_passed",
            "diagnostic_non_advancing_arms",
            "primary_advancement_arms",
            "claim_evidence_pointers",
            "freeze_bindings",
            "receipt_sha256",
        },
        "A2 closeout",
    )
    if (
        value["schema_version"] != "myis.armindex-a2-execution-closeout-receipt.v1"
        or value["status"] != "PASS_A2_EXECUTION_CLOSEOUT"
        or value["evidence_class"] != "measured_development_aggregate"
        or value["candidate_count"] != 52
        or value["matched_candidate_count"] != 40
        or value["conditional_reserve_candidate_count"] != 12
        or value["workers_reaped"] is not True
        or value["protected_scan_passed"] is not True
    ):
        raise TrainHeadroomError(
            "A2 closeout is not a valid measured aggregate PASS receipt"
        )
    winner_receipts = value["arm_winner_receipt_sha256s"]
    if (
        not isinstance(winner_receipts, Mapping)
        or set(winner_receipts) != set(ARM_IDS)
        or len(set(winner_receipts.values())) != len(ARM_IDS)
    ):
        raise TrainHeadroomError(
            "A2 closeout must bind five distinct arm winner receipt hashes"
        )
    for arm_id, receipt_sha256 in winner_receipts.items():
        _require_sha256(receipt_sha256, f"{arm_id} arm_winner_receipt_sha256")
    for field in (
        "candidate_result_set_sha256",
        "safe_return_receipt_sha256",
        "terminal_checkpoint_sha256",
    ):
        _require_sha256(value[field], field)
    if value["diagnostic_non_advancing_arms"] != ["ARM-01", "ARM-02"] or value[
        "primary_advancement_arms"
    ] != ["ARM-03", "ARM-05", "ARM-04"]:
        raise TrainHeadroomError(
            "A2 closeout advancement and diagnostic arm bindings are incompatible"
        )
    claim_pointers = value["claim_evidence_pointers"]
    if (
        not isinstance(claim_pointers, list)
        or not claim_pointers
        or any(
            not isinstance(pointer, str)
            or not pointer.strip()
            or Path(pointer).is_absolute()
            or ".." in Path(pointer).parts
            for pointer in claim_pointers
        )
    ):
        raise TrainHeadroomError("A2 closeout must bind aggregate-safe claim pointers")
    if value["freeze_bindings"] != FROZEN_A2_BINDINGS:
        raise TrainHeadroomError(
            "A2 closeout does not bind the frozen A2 manifest, receipt, and lock tuple"
        )
    _require_receipt_hash(value, "A2 closeout")


def _validate_a1_incumbent_aggregate(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        raise TrainHeadroomError("A1 incumbent aggregate must be a receipt mapping")
    _require_exact_keys(
        value,
        {
            "schema_version",
            "status",
            "evidence_class",
            "scientific_authority",
            "frozen",
            "scope",
            "train_query_count",
            "split_id",
            "split_decision_sha256",
            "evaluator_sha256",
            "metric_name",
            "metric_denominator",
            "arm_metrics",
            "receipt_sha256",
        },
        "A1 incumbent aggregate",
    )
    if (
        value["schema_version"] != "myis.armindex-a1-incumbent-aggregate-receipt.v1"
        or value["status"] != "PASS"
        or value["evidence_class"] != "measured_development_aggregate"
        or value["scientific_authority"] is not True
        or value["frozen"] is not True
        or value["scope"] != "Train-250"
        or value["train_query_count"] != 250
        or value["split_id"] != "Train-250"
        or value["split_decision_sha256"] != SPLIT_DECISION_SHA256
        or value["metric_name"] != _METRIC_NAME
        or not isinstance(value["metric_denominator"], str)
        or not value["metric_denominator"].strip()
    ):
        raise TrainHeadroomError(
            "A1 incumbent aggregate is not a valid frozen measured receipt"
        )
    _require_sha256(value["evaluator_sha256"], "A1 incumbent evaluator_sha256")
    metrics = _validate_a1_metric_rows(value["arm_metrics"])
    _require_receipt_hash(value, "A1 incumbent aggregate")
    return metrics


def _validate_winners(
    value: Any,
    incumbent: Mapping[str, Mapping[str, Any]],
    a1_receipt: Mapping[str, Any],
) -> None:
    if not isinstance(value, list) or len(value) != len(ARM_IDS):
        raise TrainHeadroomError("exactly five A2 winner bindings are required")
    arms: list[str] = []
    hashes: list[str] = []
    for winner in value:
        if not isinstance(winner, Mapping):
            raise TrainHeadroomError("winner binding must be a mapping")
        _require_exact_keys(
            winner,
            {
                "arm_id",
                "winner_program_sha256",
                "winner_selection_receipt_sha256",
                "candidate_frozen",
                "train_aggregate_receipt",
            },
            "winner binding",
        )
        arm_id = winner["arm_id"]
        if arm_id not in ARM_IDS or winner["candidate_frozen"] is not True:
            raise TrainHeadroomError("winner must be a frozen active-arm binding")
        _require_sha256(winner["winner_program_sha256"], "winner_program_sha256")
        _require_sha256(
            winner["winner_selection_receipt_sha256"],
            "winner_selection_receipt_sha256",
        )
        receipt = winner["train_aggregate_receipt"]
        _validate_train_receipt(receipt, arm_id, a1_receipt)
        if (
            receipt["winner_selection_receipt_sha256"]
            != winner["winner_selection_receipt_sha256"]
        ):
            raise TrainHeadroomError(
                "Train-250 diagnostic receipt is not bound to its frozen winner-selection receipt"
            )
        arms.append(arm_id)
        hashes.append(winner["winner_program_sha256"])
    if set(arms) != set(ARM_IDS) or len(arms) != len(set(arms)):
        raise TrainHeadroomError(
            "winner bindings must cover each active arm exactly once"
        )
    if len(hashes) != len(set(hashes)):
        raise TrainHeadroomError("winner program hashes must be distinct")
    if set(incumbent) != set(arms):
        raise TrainHeadroomError("A1 incumbents and A2 winners are incompatible")


def _validate_train_receipt(
    value: Any, arm_id: str, a1_receipt: Mapping[str, Any]
) -> None:
    if not isinstance(value, Mapping):
        raise TrainHeadroomError("Train-250 receipt must be a mapping")
    _require_exact_keys(
        value,
        {
            "schema_version",
            "status",
            "evidence_class",
            "scientific_authority",
            "scope",
            "train_query_count",
            "split_id",
            "split_decision_sha256",
            "evaluator_sha256",
            "membership_commitment_sha256",
            "qrels_commitment_sha256",
            "model_runtime_sha256",
            "metric_denominator",
            "freeze_bindings",
            "winner_selection_receipt_sha256",
            "selection_accessed",
            "final_accessed",
            "metric",
            "receipt_sha256",
        },
        "Train-250 receipt",
    )
    if (
        value["schema_version"]
        != "myis.armindex-a3-owner-local-fixed-diagnostic-receipt.v1"
        or value["status"] != "PASS"
        or value["evidence_class"] != "measured_post_a2_fixed_diagnostic_aggregate"
        or value["scientific_authority"] is not True
        or value["scope"] != "Train-250"
        or value["train_query_count"] != 250
        or value["split_id"] != a1_receipt["split_id"]
        or value["split_decision_sha256"] != SPLIT_DECISION_SHA256
        or value["evaluator_sha256"] != a1_receipt["evaluator_sha256"]
        or value["metric_denominator"] != a1_receipt["metric_denominator"]
        or value["freeze_bindings"] != FROZEN_A2_BINDINGS
        or value["selection_accessed"] is not False
        or value["final_accessed"] is not False
    ):
        raise TrainHeadroomError(
            "Train-250 receipt is incomplete, synthetic, or outside the allowed scope"
        )
    metrics = _validate_metric_rows([value["metric"]], "Train-250 receipt")
    if set(metrics) != {arm_id}:
        raise TrainHeadroomError(
            "Train-250 receipt arm does not match its winner binding"
        )
    for field in (
        "split_decision_sha256",
        "evaluator_sha256",
        "membership_commitment_sha256",
        "qrels_commitment_sha256",
        "model_runtime_sha256",
        "winner_selection_receipt_sha256",
    ):
        _require_sha256(value[field], field)
    _require_receipt_hash(value, "Train-250 receipt")


def _validate_metric_rows(value: Any, name: str) -> dict[str, float]:
    if (
        not isinstance(value, list)
        or len(value) != len(ARM_IDS)
        and name.startswith("A1")
    ):
        raise TrainHeadroomError(f"{name} must provide complete aggregate metric rows")
    metrics: dict[str, float] = {}
    for row in value:
        if not isinstance(row, Mapping):
            raise TrainHeadroomError(f"{name} metric must be a mapping")
        _require_exact_keys(
            row, {"arm_id", "metric_name", "metric_value"}, f"{name} metric"
        )
        arm_id = row["arm_id"]
        if arm_id not in ARM_IDS or row["metric_name"] != _METRIC_NAME:
            raise TrainHeadroomError(f"{name} metric identity is invalid")
        numeric = row["metric_value"]
        if (
            isinstance(numeric, bool)
            or not isinstance(numeric, (int, float))
            or not isfinite(numeric)
            or not 0 <= numeric <= 1
        ):
            raise TrainHeadroomError(f"{name} metric value must be a finite rate")
        if arm_id in metrics:
            raise TrainHeadroomError(f"{name} cannot repeat an arm metric")
        metrics[arm_id] = float(numeric)
    if name.startswith("A1") and set(metrics) != set(ARM_IDS):
        raise TrainHeadroomError("A1 incumbent aggregate must cover all active arms")
    return metrics


def _validate_a1_metric_rows(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(ARM_IDS):
        raise TrainHeadroomError(
            "A1 incumbent aggregate must provide complete aggregate metric rows"
        )
    metrics: dict[str, dict[str, Any]] = {}
    for row in value:
        if not isinstance(row, Mapping):
            raise TrainHeadroomError("A1 incumbent aggregate metric must be a mapping")
        _require_exact_keys(
            row,
            {"arm_id", "incumbent_program_sha256", "metric_name", "metric_value"},
            "A1 incumbent aggregate metric",
        )
        arm_id = row["arm_id"]
        if arm_id not in ARM_IDS or row["metric_name"] != _METRIC_NAME:
            raise TrainHeadroomError(
                "A1 incumbent aggregate metric identity is invalid"
            )
        _require_sha256(row["incumbent_program_sha256"], "incumbent_program_sha256")
        numeric = row["metric_value"]
        if (
            isinstance(numeric, bool)
            or not isinstance(numeric, (int, float))
            or not isfinite(numeric)
            or not 0 <= numeric <= 1
        ):
            raise TrainHeadroomError(
                "A1 incumbent aggregate metric value must be a finite rate"
            )
        if arm_id in metrics:
            raise TrainHeadroomError(
                "A1 incumbent aggregate cannot repeat an arm metric"
            )
        metrics[arm_id] = {
            "incumbent_program_sha256": row["incumbent_program_sha256"],
            "metric_value": float(numeric),
        }
    if set(metrics) != set(ARM_IDS):
        raise TrainHeadroomError("A1 incumbent aggregate must cover all active arms")
    return metrics


def _validate_harness_dev_authorization(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TrainHeadroomError("HARNESS-DEV authorization must be a mapping")
    _require_exact_keys(
        value,
        {
            "schema_version",
            "status",
            "authority_state",
            "closeout_state",
            "scope",
            "bindings",
            "safety",
            "authorization_sha256",
        },
        "HARNESS-DEV authorization",
    )
    if (
        value["schema_version"]
        != "myis.armindex-a3-harness-dev-headroom-authorization.v1"
        or value["status"] != "POST_A2_CLOSEOUT_HDEV100_AUTHORIZED"
        or value["authority_state"] != AUTHORITY_STATE
        or value["closeout_state"] != "A2_CLOSEOUT_BOUND"
        or value["scope"] != "HARNESS-DEV-100"
    ):
        raise TrainHeadroomError("HARNESS-DEV authorization is not post-A2-closeout")
    bindings = value["bindings"]
    if not isinstance(bindings, Mapping) or set(bindings) != {
        "authority_id",
        "authority_file_sha256",
        "a2_closeout_receipt_sha256",
        "a1_incumbent_aggregate_receipt_sha256",
        "arms",
    }:
        raise TrainHeadroomError("HARNESS-DEV authorization bindings are incomplete")
    if (
        bindings["authority_id"] != AUTHORITY_ID
        or bindings["authority_file_sha256"] != AUTHORITY_FILE_SHA256
    ):
        raise TrainHeadroomError(
            "HARNESS-DEV authorization is not bound to the current static A3.1 authority file"
        )
    _require_sha256(bindings["a2_closeout_receipt_sha256"], "A2 closeout receipt")
    _require_sha256(
        bindings["a1_incumbent_aggregate_receipt_sha256"], "A1 aggregate receipt"
    )
    if not isinstance(bindings["arms"], list) or len(bindings["arms"]) != len(ARM_IDS):
        raise TrainHeadroomError("HARNESS-DEV authorization must bind five arms")
    for arm in bindings["arms"]:
        if not isinstance(arm, Mapping):
            raise TrainHeadroomError("HARNESS-DEV arm binding must be a mapping")
        _require_exact_keys(
            arm,
            {"arm_id", "winner_program_sha256", "a1_incumbent_program_sha256"},
            "HARNESS-DEV arm binding",
        )
        if arm["arm_id"] not in ARM_IDS:
            raise TrainHeadroomError("HARNESS-DEV arm binding is invalid")
        _require_sha256(arm["winner_program_sha256"], "winner_program_sha256")
        _require_sha256(
            arm["a1_incumbent_program_sha256"], "a1_incumbent_program_sha256"
        )
    if {arm["arm_id"] for arm in bindings["arms"]} != set(ARM_IDS):
        raise TrainHeadroomError(
            "HARNESS-DEV authorization arm bindings are incomplete"
        )
    expected_safety = {
        "aggregate_only_return": True,
        "non_adaptive": True,
        "candidate_mutation_permitted": False,
        "selection_permitted": False,
        "final_permitted": False,
        "provider_permitted": False,
        "gpu_permitted": False,
        "spend_permitted": False,
        "repository_execution_permitted": False,
    }
    if value["safety"] != expected_safety:
        raise TrainHeadroomError(
            "HARNESS-DEV authorization safety declaration is invalid"
        )
    authorization_sha256 = value["authorization_sha256"]
    _require_sha256(authorization_sha256, "authorization_sha256")
    unsigned = {
        key: item for key, item in value.items() if key != "authorization_sha256"
    }
    if authorization_sha256 != canonical_sha256(unsigned):
        raise TrainHeadroomError("HARNESS-DEV authorization self-hash is invalid")
    return dict(value)


def _validate_harness_dev_results(
    value: Any, authorization: Mapping[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(ARM_IDS):
        raise TrainHeadroomError(
            "HARNESS-DEV diagnostic requires five aggregate arm results"
        )
    expected = {arm["arm_id"]: arm for arm in authorization["bindings"]["arms"]}
    results: list[dict[str, Any]] = []
    for result in value:
        if not isinstance(result, Mapping):
            raise TrainHeadroomError("HARNESS-DEV aggregate result must be a mapping")
        _require_exact_keys(
            result,
            {
                "schema_version",
                "status",
                "evidence_class",
                "scientific_authority",
                "scope",
                "harness_dev_query_count",
                "arm_id",
                "winner_program_sha256",
                "incumbent_program_sha256",
                "authorization_sha256",
                "selection_accessed",
                "final_accessed",
                "comparison",
                "receipt_sha256",
            },
            "HARNESS-DEV aggregate result",
        )
        arm_id = result["arm_id"]
        if (
            arm_id not in expected
            or result["winner_program_sha256"]
            != expected[arm_id]["winner_program_sha256"]
            or result["incumbent_program_sha256"]
            != expected[arm_id]["a1_incumbent_program_sha256"]
        ):
            raise TrainHeadroomError(
                "HARNESS-DEV aggregate result is incompatible with its frozen authorization"
            )
        if (
            result["schema_version"]
            != "myis.armindex-a3-harness-dev-aggregate-receipt.v1"
            or result["status"] != "PASS"
            or result["evidence_class"] != "measured_harness_dev_aggregate"
            or result["scientific_authority"] is not True
            or result["scope"] != "HARNESS-DEV-100"
            or result["harness_dev_query_count"] != 100
            or result["authorization_sha256"] != authorization["authorization_sha256"]
            or result["selection_accessed"] is not False
            or result["final_accessed"] is not False
        ):
            raise TrainHeadroomError(
                "HARNESS-DEV aggregate result is incomplete or outside the authorized scope"
            )
        comparison = result["comparison"]
        if (
            not isinstance(comparison, Mapping)
            or set(comparison) != {"metric_name", "winner_value", "incumbent_value"}
            or comparison["metric_name"] != _METRIC_NAME
        ):
            raise TrainHeadroomError("HARNESS-DEV comparison fields are invalid")
        for metric_value in (comparison["winner_value"], comparison["incumbent_value"]):
            if (
                isinstance(metric_value, bool)
                or not isinstance(metric_value, (int, float))
                or not isfinite(metric_value)
                or not 0 <= metric_value <= 1
            ):
                raise TrainHeadroomError(
                    "HARNESS-DEV comparison values must be finite rates"
                )
        _require_receipt_hash(result, "HARNESS-DEV aggregate result")
        results.append(dict(result))
    if {result["arm_id"] for result in results} != set(ARM_IDS) or len(
        {result["arm_id"] for result in results}
    ) != len(ARM_IDS):
        raise TrainHeadroomError(
            "HARNESS-DEV aggregate results must cover every active arm once"
        )
    return sorted(results, key=lambda result: result["arm_id"])


def _require_exact_keys(
    value: Mapping[str, Any], required: set[str], name: str
) -> None:
    if set(value) != required:
        raise TrainHeadroomError(f"{name} fields do not match the frozen contract")


def _require_arm_set(value: Any, name: str) -> None:
    if (
        not isinstance(value, list)
        or len(value) != len(ARM_IDS)
        or set(value) != set(ARM_IDS)
    ):
        raise TrainHeadroomError(f"{name} must contain every active arm exactly once")


def _require_receipt_hash(value: Mapping[str, Any], name: str) -> None:
    receipt_sha256 = value.get("receipt_sha256")
    _require_sha256(receipt_sha256, f"{name} receipt_sha256")
    unsigned = {key: item for key, item in value.items() if key != "receipt_sha256"}
    if receipt_sha256 != canonical_sha256(unsigned):
        raise TrainHeadroomError(
            f"{name} receipt_sha256 does not bind its aggregate payload"
        )


def _require_sha256(value: Any, name: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise TrainHeadroomError(f"{name} must be a SHA-256")


__all__ = [
    "ARM_IDS",
    "AUTHORITY_STATE",
    "TrainHeadroomError",
    "authorize_harness_dev_headroom",
    "build_harness_dev_headroom_diagnostic",
    "build_train_headroom_diagnostic",
    "validate_train_headroom_inputs",
]
