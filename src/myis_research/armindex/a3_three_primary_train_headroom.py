"""Aggregate-only Train-250 diagnostics for the amended three-primary A3 route."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


PRIMARY_ARM_IDS = ("ARM-03", "ARM-05", "ARM-04")
ALL_ARM_IDS = ("ARM-01", "ARM-02", *PRIMARY_ARM_IDS)
AUTHORITY_ID = "A3.1_THREE_PRIMARY_TRAIN_HEADROOM_POST_A2"
AUTHORITY_STATE = "PENDING_A2_CLOSEOUT"
AUTHORITY_FILE_SHA256 = "8d3da844dddbfd6e49bc4bac0f41b1860d96c0af23e1dc25ec7ab50da334e56c"
FROZEN_A2_BINDINGS = {
    "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
    "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
    "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
}
SPLIT_DECISION_SHA256 = "87efd2ef78400b6025b5cfe153ff5e8b165ea4fad784d0a99979e514e6bb2202"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_METRIC_NAME = "recall_at_100_out"


class ThreePrimaryTrainHeadroomError(ValueError):
    """Raised when the three-primary diagnostic lacks compatible evidence."""


def validate_three_primary_train_headroom_inputs(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate only complete, aggregate-safe post-amendment A2 inputs."""

    payload = deepcopy(dict(value))
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise ThreePrimaryTrainHeadroomError(str(error)) from error
    _require_exact_keys(
        payload,
        {
            "schema_version",
            "authority_id",
            "authority_file_sha256",
            "authority_state",
            "a2_closeout",
            "a2_result_integrity_audit",
            "a1_incumbent_aggregate",
            "winners",
        },
        "three-primary diagnostic input",
    )
    if payload["schema_version"] != "myis.armindex-a3-three-primary-train-headroom-input.v1":
        raise ThreePrimaryTrainHeadroomError("unsupported three-primary input schema")
    if (
        payload["authority_id"] != AUTHORITY_ID
        or payload["authority_file_sha256"] != AUTHORITY_FILE_SHA256
        or payload["authority_state"] != AUTHORITY_STATE
    ):
        raise ThreePrimaryTrainHeadroomError("input is not bound to the three-primary authority")

    closeout = _validate_amended_a2_closeout(payload["a2_closeout"])
    _validate_a2_result_integrity_audit(payload["a2_result_integrity_audit"], closeout)
    incumbent = _validate_a1_incumbent_aggregate(payload["a1_incumbent_aggregate"])
    _validate_primary_winners(payload["winners"], closeout, incumbent, payload["a1_incumbent_aggregate"])
    return payload


def build_three_primary_train_headroom_diagnostic(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Emit an aggregate-only descriptive A2-winner-minus-A1-incumbent report."""

    payload = validate_three_primary_train_headroom_inputs(value)
    incumbents = _validate_a1_incumbent_aggregate(payload["a1_incumbent_aggregate"])
    rows: list[dict[str, Any]] = []
    bindings: list[dict[str, str]] = []
    winners_by_arm = {winner["arm_id"]: winner for winner in payload["winners"]}
    for arm_id in PRIMARY_ARM_IDS:
        winner = winners_by_arm[arm_id]
        receipt = winner["train_aggregate_receipt"]
        metric = float(receipt["metric"]["metric_value"])
        rows.append(
            {
                "arm_id": arm_id,
                "metric_name": _METRIC_NAME,
                "a1_incumbent_value": incumbents[arm_id]["metric_value"],
                "a2_winner_train_value": metric,
                "winner_minus_incumbent": metric - incumbents[arm_id]["metric_value"],
            }
        )
        bindings.append(
            {
                "arm_id": arm_id,
                "winner_program_sha256": winner["winner_program_sha256"],
                "winner_selection_receipt_sha256": winner[
                    "winner_selection_receipt_sha256"
                ],
                "train_aggregate_receipt_sha256": receipt["receipt_sha256"],
            }
        )

    audit = payload["a2_result_integrity_audit"]
    diagnostic: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-three-primary-train-headroom-diagnostic.v1",
        "status": "DESCRIPTIVE_ONLY",
        "authority_state": AUTHORITY_STATE,
        "scope": "Train-250",
        "bindings": {
            "authority_id": AUTHORITY_ID,
            "authority_file_sha256": AUTHORITY_FILE_SHA256,
            "a2_closeout_receipt_sha256": payload["a2_closeout"]["receipt_sha256"],
            "a2_result_integrity_audit_sha256": audit["audit_sha256"],
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
    return {**diagnostic, "diagnostic_sha256": canonical_sha256(diagnostic)}


def _validate_amended_a2_closeout(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ThreePrimaryTrainHeadroomError("A2 amended closeout must be a mapping")
    required = {
        "schema_version",
        "status",
        "evidence_class",
        "candidate_count",
        "matched_candidate_count",
        "conditional_reserve_candidate_count",
        "measured_candidate_count",
        "dormant_conditional_reserve_count",
        "failed_candidate_count",
        "primary_winner_receipt_sha256s",
        "diagnostic_no_winner_receipt_sha256s",
        "amendment_sha256",
        "candidate_result_set_sha256",
        "safe_return_receipt_sha256",
        "terminal_checkpoint_sha256",
        "freeze_bindings",
        "receipt_sha256",
    }
    if not required.issubset(value):
        raise ThreePrimaryTrainHeadroomError("A2 amended closeout fields are incomplete")
    if (
        value["schema_version"] != "myis.armindex-a2-execution-closeout-receipt.v2"
        or value["status"] != "PASS_A2_EXECUTION_CLOSEOUT"
        or value["evidence_class"] != "measured_development_aggregate"
        or (
            value["candidate_count"],
            value["matched_candidate_count"],
            value["conditional_reserve_candidate_count"],
            value["measured_candidate_count"],
            value["dormant_conditional_reserve_count"],
            value["failed_candidate_count"],
        )
        != (52, 40, 12, 44, 8, 0)
        or value["freeze_bindings"] != FROZEN_A2_BINDINGS
    ):
        raise ThreePrimaryTrainHeadroomError("A2 amended closeout is incompatible")
    _validate_hash_map(value["primary_winner_receipt_sha256s"], PRIMARY_ARM_IDS, "primary winner")
    _validate_hash_map(
        value["diagnostic_no_winner_receipt_sha256s"],
        ("ARM-01", "ARM-02"),
        "diagnostic no-winner",
    )
    for field in (
        "amendment_sha256",
        "candidate_result_set_sha256",
        "safe_return_receipt_sha256",
        "terminal_checkpoint_sha256",
    ):
        _require_hash(value[field], field)
    _require_self_hash(value, "receipt_sha256", "A2 amended closeout")
    return dict(value)


def _validate_a2_result_integrity_audit(audit: Any, closeout: Mapping[str, Any]) -> None:
    if not isinstance(audit, Mapping):
        raise ThreePrimaryTrainHeadroomError("A2 result-integrity audit must be a mapping")
    required = {
        "schema_version",
        "status",
        "closeout",
        "coverage",
        "protection",
        "safe_return",
        "terminal_checkpoint",
        "audit_sha256",
    }
    if not required.issubset(audit):
        raise ThreePrimaryTrainHeadroomError("A2 result-integrity audit fields are incomplete")
    if (
        audit["schema_version"] != "myis.armindex-a2-result-integrity-audit.v2"
        or audit["status"] != "PASS_A2_RESULT_AUDIT"
        or not isinstance(audit["protection"], Mapping)
        or audit["protection"].get("aggregate_only_scan_passed") is not True
    ):
        raise ThreePrimaryTrainHeadroomError("A2 result-integrity audit is incompatible")
    expected_hashes = {
        "closeout": closeout["receipt_sha256"],
        "safe_return": closeout["safe_return_receipt_sha256"],
        "terminal_checkpoint": closeout["terminal_checkpoint_sha256"],
    }
    for section, expected_hash in expected_hashes.items():
        item = audit[section]
        if not isinstance(item, Mapping) or item.get("receipt_sha256") != expected_hash:
            raise ThreePrimaryTrainHeadroomError("A2 result-integrity audit binding drift")
    coverage = audit["coverage"]
    if not isinstance(coverage, Mapping):
        raise ThreePrimaryTrainHeadroomError("A2 result-integrity coverage is invalid")
    _require_hash(coverage.get("receipt_sha256"), "A2 result-integrity coverage receipt")
    _require_self_hash(audit, "audit_sha256", "A2 result-integrity audit")


def _validate_a1_incumbent_aggregate(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        raise ThreePrimaryTrainHeadroomError("A1 incumbent aggregate must be a mapping")
    required = {
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
    }
    if not required.issubset(value):
        raise ThreePrimaryTrainHeadroomError("A1 incumbent aggregate fields are incomplete")
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
    ):
        raise ThreePrimaryTrainHeadroomError("A1 incumbent aggregate is incompatible")
    _require_hash(value["evaluator_sha256"], "A1 evaluator")
    _require_self_hash(value, "receipt_sha256", "A1 incumbent aggregate")
    rows = value["arm_metrics"]
    if not isinstance(rows, list) or len(rows) != len(ALL_ARM_IDS):
        raise ThreePrimaryTrainHeadroomError("A1 incumbent aggregate must retain five arms")
    metrics: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "arm_id",
            "incumbent_program_sha256",
            "metric_name",
            "metric_value",
        }:
            raise ThreePrimaryTrainHeadroomError("A1 incumbent metric row is invalid")
        arm_id = row["arm_id"]
        if arm_id not in ALL_ARM_IDS or row["metric_name"] != _METRIC_NAME:
            raise ThreePrimaryTrainHeadroomError("A1 incumbent metric identity is invalid")
        _require_hash(row["incumbent_program_sha256"], "A1 incumbent program")
        _require_rate(row["metric_value"], "A1 incumbent metric")
        if arm_id in metrics:
            raise ThreePrimaryTrainHeadroomError("A1 incumbent metric arm is repeated")
        metrics[arm_id] = {
            "incumbent_program_sha256": row["incumbent_program_sha256"],
            "metric_value": float(row["metric_value"]),
        }
    if set(metrics) != set(ALL_ARM_IDS):
        raise ThreePrimaryTrainHeadroomError("A1 incumbent aggregate arm coverage is incomplete")
    return metrics


def _validate_primary_winners(
    winners: Any,
    closeout: Mapping[str, Any],
    incumbents: Mapping[str, Mapping[str, Any]],
    a1_receipt: Mapping[str, Any],
) -> None:
    if not isinstance(winners, list) or len(winners) != len(PRIMARY_ARM_IDS):
        raise ThreePrimaryTrainHeadroomError("exactly three primary winner bindings are required")
    by_arm: dict[str, Mapping[str, Any]] = {}
    for winner in winners:
        if not isinstance(winner, Mapping) or set(winner) != {
            "arm_id",
            "winner_program_sha256",
            "winner_selection_receipt_sha256",
            "candidate_frozen",
            "train_aggregate_receipt",
        }:
            raise ThreePrimaryTrainHeadroomError("primary winner binding is invalid")
        arm_id = winner["arm_id"]
        if arm_id not in PRIMARY_ARM_IDS or winner["candidate_frozen"] is not True:
            raise ThreePrimaryTrainHeadroomError("diagnostic arms cannot enter three-primary headroom")
        _require_hash(winner["winner_program_sha256"], "winner program")
        winner_receipt = winner["winner_selection_receipt_sha256"]
        if winner_receipt != closeout["primary_winner_receipt_sha256s"].get(arm_id):
            raise ThreePrimaryTrainHeadroomError("primary winner receipt does not match amended A2 closeout")
        _require_hash(winner_receipt, "winner selection receipt")
        _validate_train_receipt(winner["train_aggregate_receipt"], arm_id, a1_receipt, winner_receipt)
        if arm_id in by_arm:
            raise ThreePrimaryTrainHeadroomError("primary winner arm is repeated")
        by_arm[arm_id] = winner
    if set(by_arm) != set(PRIMARY_ARM_IDS) or not set(PRIMARY_ARM_IDS).issubset(incumbents):
        raise ThreePrimaryTrainHeadroomError("three-primary winner bindings are incomplete")


def _validate_train_receipt(
    receipt: Any,
    arm_id: str,
    a1_receipt: Mapping[str, Any],
    winner_receipt_sha256: str,
) -> None:
    if not isinstance(receipt, Mapping):
        raise ThreePrimaryTrainHeadroomError("Train-250 receipt must be a mapping")
    required = {
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
    }
    if not required.issubset(receipt):
        raise ThreePrimaryTrainHeadroomError("Train-250 receipt fields are incomplete")
    if (
        receipt["schema_version"] != "myis.armindex-a3-owner-local-fixed-diagnostic-receipt.v1"
        or receipt["status"] != "PASS"
        or receipt["evidence_class"] != "measured_post_a2_fixed_diagnostic_aggregate"
        or receipt["scientific_authority"] is not True
        or receipt["scope"] != "Train-250"
        or receipt["train_query_count"] != 250
        or receipt["split_id"] != a1_receipt["split_id"]
        or receipt["split_decision_sha256"] != SPLIT_DECISION_SHA256
        or receipt["evaluator_sha256"] != a1_receipt["evaluator_sha256"]
        or receipt["metric_denominator"] != a1_receipt["metric_denominator"]
        or receipt["freeze_bindings"] != FROZEN_A2_BINDINGS
        or receipt["winner_selection_receipt_sha256"] != winner_receipt_sha256
        or receipt["selection_accessed"] is not False
        or receipt["final_accessed"] is not False
    ):
        raise ThreePrimaryTrainHeadroomError("Train-250 receipt is outside the allowed scope")
    for field in (
        "membership_commitment_sha256",
        "qrels_commitment_sha256",
        "model_runtime_sha256",
    ):
        _require_hash(receipt[field], field)
    metric = receipt["metric"]
    if not isinstance(metric, Mapping) or set(metric) != {
        "arm_id",
        "metric_name",
        "metric_value",
    }:
        raise ThreePrimaryTrainHeadroomError("Train-250 metric is invalid")
    if metric["arm_id"] != arm_id or metric["metric_name"] != _METRIC_NAME:
        raise ThreePrimaryTrainHeadroomError("Train-250 metric arm binding is invalid")
    _require_rate(metric["metric_value"], "Train-250 metric")
    _require_self_hash(receipt, "receipt_sha256", "Train-250 receipt")


def _validate_hash_map(value: Any, arms: tuple[str, ...], name: str) -> None:
    if not isinstance(value, Mapping) or set(value) != set(arms):
        raise ThreePrimaryTrainHeadroomError(f"{name} arm coverage is incomplete")
    for arm_id in arms:
        _require_hash(value[arm_id], f"{arm_id} {name}")


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], name: str) -> None:
    if set(value) != keys:
        raise ThreePrimaryTrainHeadroomError(f"{name} fields do not match the frozen contract")


def _require_hash(value: Any, name: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise ThreePrimaryTrainHeadroomError(f"{name} must be a SHA-256")


def _require_rate(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ThreePrimaryTrainHeadroomError(f"{name} must be a finite rate")
    if not 0 <= value <= 1:
        raise ThreePrimaryTrainHeadroomError(f"{name} must be within [0, 1]")


def _require_self_hash(value: Mapping[str, Any], field: str, name: str) -> None:
    supplied = value.get(field)
    _require_hash(supplied, f"{name} {field}")
    unsigned = {key: item for key, item in value.items() if key != field}
    if supplied != canonical_sha256(unsigned):
        raise ThreePrimaryTrainHeadroomError(f"{name} self-hash is invalid")


__all__ = [
    "ALL_ARM_IDS",
    "AUTHORITY_FILE_SHA256",
    "AUTHORITY_ID",
    "AUTHORITY_STATE",
    "FROZEN_A2_BINDINGS",
    "PRIMARY_ARM_IDS",
    "SPLIT_DECISION_SHA256",
    "ThreePrimaryTrainHeadroomError",
    "build_three_primary_train_headroom_diagnostic",
    "validate_three_primary_train_headroom_inputs",
]
