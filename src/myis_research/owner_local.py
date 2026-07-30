"""Pure validation for owner-local P1 requests and aggregate receipts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .protection import assert_aggregate_only, assert_hash_only_mapping


OWNER_LOCAL_REQUEST_SCHEMA = "myis.owner-local-request.v2"
OWNER_LOCAL_RECEIPT_SCHEMA = "myis.owner-local-receipt.v2"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GIT = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
_REQUEST_KEYS = frozenset({"schema_version", "request_id", "decision_id", "phase_id", "stage", "scope", "git_commit", "input_hashes"})
_RECEIPT_KEYS = frozenset({
    "schema_version", "request_sha256", "request_id", "decision_id", "phase_id", "stage", "scope_sha256",
    "aggregate_counts", "aggregate_hashes", "metrics", "cost", "latency_seconds", "lineage_hashes",
    "historical_exposure", "status", "blockers", "receipt_sha256",
})
_FORBIDDEN_KEY_PARTS = ("query_id", "query_ids", "qid", "qids", "qrel", "per_query", "membership", "raw_payload", "credential", "secret", "password")
_P1_ARMS = ("R0", "R0-W")
_P1_SPLITS = ("train", "selection")
_P1_SCOPES = ("ALL", "IN", "OUT")
_P1_LINEAGE_KEYS = frozenset({"dataset_sha256", "corpus_sha256", "query_sha256", "qrels_sha256", "split_sha256", "index_sha256", "evaluator_sha256"})
_P1_ACCEPTED_METRIC_KEYS = frozenset({"arm", "name", "value", "n", "retrieved_relevant", "relevant_total", "scope", "split", "direction", "denominator", "evidence_role"})
_P1_BLOCKED_METRIC_KEYS = frozenset({"name", "value", "n", "hits", "scope", "split", "direction", "denominator", "evidence_role"})
_METRIC_ALLOWED_KEYS = _P1_ACCEPTED_METRIC_KEYS | {"hits"}


class OwnerLocalContractError(ValueError):
    """Raised when a request or receipt violates the protected boundary."""


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_mapping(payload, _REQUEST_KEYS, "request")
    if payload["schema_version"] != OWNER_LOCAL_REQUEST_SCHEMA:
        raise OwnerLocalContractError("unsupported owner-local request schema")
    decision = str(payload["decision_id"])
    phase = str(payload["phase_id"])
    stage = str(payload["stage"])
    expected = {
        "P1_CPU_EXECUTION_ENVELOPE": ("P1_CPU_BASELINE", "train_selection"),
        "D2_OPEN_FINAL": ("P3_FINAL", "final"),
        "D3_SUBMIT_RELEASE": ("P4_PUBLICATION", "report"),
    }
    if decision not in expected or (phase, stage) != expected[decision]:
        raise OwnerLocalContractError("decision is not valid for the declared phase/stage")
    if not isinstance(payload["request_id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", payload["request_id"]):
        raise OwnerLocalContractError("request_id is invalid")
    if not isinstance(payload["git_commit"], str) or not _GIT.fullmatch(payload["git_commit"]):
        raise OwnerLocalContractError("git_commit must be a lowercase commit hash")
    if not isinstance(payload["scope"], Mapping) or not payload["scope"]:
        raise OwnerLocalContractError("scope must be a non-empty hash mapping")
    if not isinstance(payload["input_hashes"], Mapping) or not payload["input_hashes"]:
        raise OwnerLocalContractError("input_hashes must be a non-empty hash mapping")
    _reject_lists(payload, "request")
    _reject_forbidden_keys(payload)
    assert_aggregate_only(payload)
    assert_hash_only_mapping({str(k): str(v) for k, v in payload["scope"].items()}, name="scope")
    assert_hash_only_mapping({str(k): str(v) for k, v in payload["input_hashes"].items()}, name="input_hashes")
    return dict(payload)


def build_receipt(
    request: Mapping[str, Any],
    *,
    aggregate_counts: Mapping[str, int],
    aggregate_hashes: Mapping[str, str],
    metrics: Sequence[Mapping[str, Any]],
    cost_usd: float,
    latency_seconds: float,
    lineage_hashes: Mapping[str, str],
    historical_exposure: Mapping[str, Any] | None = None,
    status: str = "accepted",
    blockers: Sequence[str] = (),
) -> dict[str, Any]:
    validated = validate_request(request)
    if status not in {"accepted", "blocked"}:
        raise OwnerLocalContractError("receipt status must be accepted or blocked")
    _validate_counts(aggregate_counts)
    assert_hash_only_mapping({str(k): str(v) for k, v in aggregate_hashes.items()}, name="aggregate_hashes")
    assert_hash_only_mapping({str(k): str(v) for k, v in lineage_hashes.items()}, name="lineage_hashes")
    if isinstance(cost_usd, bool) or not isinstance(cost_usd, (int, float)) or cost_usd < 0:
        raise OwnerLocalContractError("cost_usd must be non-negative")
    if isinstance(latency_seconds, bool) or not isinstance(latency_seconds, (int, float)) or latency_seconds < 0:
        raise OwnerLocalContractError("latency_seconds must be non-negative")
    metric_rows = [dict(row) for row in metrics]
    if not metric_rows:
        raise OwnerLocalContractError("receipt must contain aggregate metric values")
    _validate_metric_rows(metric_rows, decision_id=validated["decision_id"], status=status, aggregate_counts=aggregate_counts)
    body: dict[str, Any] = {
        "schema_version": OWNER_LOCAL_RECEIPT_SCHEMA,
        "request_sha256": canonical_sha256(validated),
        "request_id": validated["request_id"],
        "decision_id": validated["decision_id"],
        "phase_id": validated["phase_id"],
        "stage": validated["stage"],
        "scope_sha256": canonical_sha256(validated["scope"]),
        "aggregate_counts": dict(sorted(aggregate_counts.items())),
        "aggregate_hashes": dict(sorted(aggregate_hashes.items())),
        "metrics": metric_rows,
        "cost": {"currency": "USD", "value": float(cost_usd)},
        "latency_seconds": float(latency_seconds),
        "lineage_hashes": dict(sorted(lineage_hashes.items())),
        "historical_exposure": dict(historical_exposure or {}),
        "status": status,
        "blockers": [str(item) for item in blockers],
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return validate_receipt(body)


def validate_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_mapping(payload, _RECEIPT_KEYS, "receipt")
    if payload["schema_version"] != OWNER_LOCAL_RECEIPT_SCHEMA or payload["status"] not in {"accepted", "blocked"}:
        raise OwnerLocalContractError("receipt schema or status is invalid")
    if payload["decision_id"] not in {"P1_CPU_EXECUTION_ENVELOPE", "D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"}:
        raise OwnerLocalContractError("receipt decision is invalid")
    expected = {"P1_CPU_EXECUTION_ENVELOPE": ("P1_CPU_BASELINE", "train_selection"), "D2_OPEN_FINAL": ("P3_FINAL", "final"), "D3_SUBMIT_RELEASE": ("P4_PUBLICATION", "report")}
    if (payload["phase_id"], payload["stage"]) != expected[payload["decision_id"]]:
        raise OwnerLocalContractError("receipt decision phase/stage mismatch")
    for key in ("request_sha256", "scope_sha256", "receipt_sha256"):
        if not isinstance(payload[key], str) or not _SHA256.fullmatch(payload[key]):
            raise OwnerLocalContractError(f"{key} must be SHA-256")
    _validate_counts(payload["aggregate_counts"])
    assert_hash_only_mapping({str(k): str(v) for k, v in payload["aggregate_hashes"].items()}, name="aggregate_hashes")
    assert_hash_only_mapping({str(k): str(v) for k, v in payload["lineage_hashes"].items()}, name="lineage_hashes")
    _validate_metric_rows(payload["metrics"], decision_id=payload["decision_id"], status=payload["status"], aggregate_counts=payload["aggregate_counts"])
    _validate_receipt_semantics(payload)
    _reject_forbidden_keys(payload)
    assert_aggregate_only(payload)
    unsigned = {key: value for key, value in payload.items() if key != "receipt_sha256"}
    if canonical_sha256(unsigned) != payload["receipt_sha256"]:
        raise OwnerLocalContractError("receipt_sha256 does not match canonical receipt")
    return dict(payload)


def _validate_counts(values: Mapping[str, Any]) -> None:
    if not isinstance(values, Mapping) or any(not isinstance(key, str) or not key.strip() for key in values):
        raise OwnerLocalContractError("aggregate counts must be a named mapping")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values.values()):
        raise OwnerLocalContractError("aggregate counts must be non-negative integers")


def _validate_metric_rows(
    rows: Any,
    *,
    decision_id: str,
    status: str,
    aggregate_counts: Mapping[str, Any],
) -> None:
    if not isinstance(rows, list) or not rows:
        raise OwnerLocalContractError("receipt must contain aggregate metric values")
    for row in rows:
        if not isinstance(row, Mapping) or set(row) - _METRIC_ALLOWED_KEYS:
            raise OwnerLocalContractError("metric contains an unsupported field")
        required = {"name", "value", "n", "scope", "split", "direction", "denominator", "evidence_role"}
        if not required <= set(row):
            raise OwnerLocalContractError("metric is missing required aggregate fields")
        if row["name"] != "recall_at_100" or row["scope"] not in _P1_SCOPES or not isinstance(row["split"], str) or not row["split"]:
            raise OwnerLocalContractError("metric name, scope, or split is invalid")
        if row["direction"] != "maximize" or row["denominator"] not in {"macro_mean_per_query_relevant_families", "queries_with_positive_family_relevance"}:
            raise OwnerLocalContractError("metric direction or denominator is invalid")
        if not isinstance(row["evidence_role"], str) or not row["evidence_role"]:
            raise OwnerLocalContractError("metric evidence_role is invalid")
        _validate_nonnegative_int(row["n"], "metric n")
        for key in ("hits", "retrieved_relevant", "relevant_total"):
            if key in row:
                _validate_nonnegative_int(row[key], f"metric {key}")
        value = row["value"]
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0.0 <= float(value) <= 1.0):
            raise OwnerLocalContractError("metric value must be a finite value in [0, 1] or null")

    if decision_id == "P1_CPU_EXECUTION_ENVELOPE":
        _validate_p1_metric_matrix(rows, status=status, aggregate_counts=aggregate_counts)


def _validate_p1_metric_matrix(rows: list[Mapping[str, Any]], *, status: str, aggregate_counts: Mapping[str, Any]) -> None:
    if status == "blocked":
        expected = {(scope, "train_selection") for scope in _P1_SCOPES}
        observed = {(str(row.get("scope")), str(row.get("split"))) for row in rows}
        if len(rows) != 3 or observed != expected:
            raise OwnerLocalContractError("blocked P1 receipt must contain exactly ALL/IN/OUT aggregate rows")
        for row in rows:
            if set(row) != _P1_BLOCKED_METRIC_KEYS or row["value"] is not None or row["n"] != 0 or row["hits"] != 0 or row["evidence_role"] != "blocked":
                raise OwnerLocalContractError("blocked P1 metric rows are semantically invalid")
        return

    expected = {(arm, split, scope) for arm in _P1_ARMS for split in _P1_SPLITS for scope in _P1_SCOPES}
    observed = {(str(row.get("arm")), str(row.get("split")), str(row.get("scope"))) for row in rows}
    if len(rows) != len(expected) or observed != expected:
        raise OwnerLocalContractError("accepted P1 receipt must contain the exact R0/R0-W train/selection ALL/IN/OUT matrix")
    for row in rows:
        if set(row) != _P1_ACCEPTED_METRIC_KEYS:
            raise OwnerLocalContractError("accepted P1 metric fields do not match the aggregate contract")
        if row["denominator"] != "macro_mean_per_query_relevant_families":
            raise OwnerLocalContractError("accepted P1 metric denominator is invalid")
        expected_role = "primary" if row["scope"] == "OUT" else "secondary"
        if row["evidence_role"] != expected_role:
            raise OwnerLocalContractError("accepted P1 metric evidence_role is invalid")
        if row["retrieved_relevant"] > row["relevant_total"]:
            raise OwnerLocalContractError("retrieved relevant families cannot exceed relevant total")
        if row["n"] == 0:
            if row["value"] is not None or row["retrieved_relevant"] != 0 or row["relevant_total"] != 0:
                raise OwnerLocalContractError("zero-denominator P1 metric must be null with zero aggregate relevance")
        else:
            if row["value"] is None or row["relevant_total"] < row["n"]:
                raise OwnerLocalContractError("positive-denominator P1 metric is semantically invalid")
            query_count = aggregate_counts.get(f"{row['split']}_queries")
            if isinstance(query_count, int) and row["n"] > query_count:
                raise OwnerLocalContractError("P1 metric denominator exceeds the split query count")


def _validate_receipt_semantics(payload: Mapping[str, Any]) -> None:
    blockers = payload["blockers"]
    if not isinstance(blockers, list) or not all(isinstance(item, str) and item for item in blockers):
        raise OwnerLocalContractError("receipt blockers must be non-empty strings")
    if payload["status"] == "accepted" and blockers:
        raise OwnerLocalContractError("accepted receipt cannot contain blockers")
    if payload["status"] == "blocked" and not blockers:
        raise OwnerLocalContractError("blocked receipt must contain at least one blocker")
    if payload["decision_id"] != "P1_CPU_EXECUTION_ENVELOPE" or payload["status"] != "accepted":
        return
    if not _P1_LINEAGE_KEYS <= set(payload["lineage_hashes"]):
        raise OwnerLocalContractError("accepted P1 receipt is missing required lineage hashes")
    required_metric_hashes = {f"{arm.lower()}_{split}_metrics" for arm in _P1_ARMS for split in _P1_SPLITS}
    if not required_metric_hashes <= set(payload["aggregate_hashes"]):
        raise OwnerLocalContractError("accepted P1 receipt is missing matrix metric hashes")
    if not {"train_queries", "selection_queries"} <= set(payload["aggregate_counts"]):
        raise OwnerLocalContractError("accepted P1 receipt is missing split aggregate counts")


def _validate_nonnegative_int(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OwnerLocalContractError(f"{label} must be a non-negative integer")


def _validate_mapping(payload: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise OwnerLocalContractError(f"{label} fields do not match the contract")


def _reject_lists(value: Any, path: str) -> None:
    if isinstance(value, (list, tuple)):
        raise OwnerLocalContractError(f"lists are forbidden in owner-local {path}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_lists(item, f"{path}.{key}")


def _reject_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).casefold()
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS) and not normalized.endswith("_sha256"):
                raise OwnerLocalContractError(f"forbidden owner-local field: {key}")
            _reject_forbidden_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_forbidden_keys(item)
