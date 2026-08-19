"""Owner-local aggregate evaluation contracts for ArmIndex A4.

The remote worker only produces retrieval packages.  This module is the
owner-local bridge: a caller may provide a protected evaluator callback, but
all records emitted here are aggregate-only and hash bound.  Legal transfer is
represented as a separate diagnostic receipt and never enters ArmIndex scores.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import math
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only

_HASH = re.compile(r"^[a-f0-9]{64}$")
_PROFILES = ("FAST", "BALANCED", "DEEP")
_METRICS = ("recall_at_100", "ndcg_at_100", "ndcg_at_10")


class A4OwnerEvaluatorError(ValueError):
    """Raised when an A4 aggregate boundary or coverage invariant fails."""


def evaluate_a4_profile_owner_local(
    profile: Mapping[str, Any],
    ranking_package: Mapping[str, Any],
    *,
    evaluator_binding_sha256: str,
    hdev_commitment_sha256: str,
    metric_evaluator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    expected_query_count: int = 100,
) -> dict[str, Any]:
    """Evaluate one A4 package without exporting protected evaluator inputs.

    ``metric_evaluator`` runs inside the Owner Store and receives the transient
    ranking mapping.  Its return value must contain aggregate metrics only.
    """

    checked_profile = _profile(profile)
    package = _aggregate(ranking_package, "ranking package")
    if package.get("schema_version") != "myis.armindex-a4-remote-ranking-package.v1":
        raise A4OwnerEvaluatorError("ranking package schema is invalid")
    if package.get("status") != "PASS_A4_REMOTE_RANKING_PACKAGE":
        raise A4OwnerEvaluatorError("ranking package is not complete")
    attempt_id = checked_profile.get("attempt_id", package.get("attempt_id"))
    if not isinstance(attempt_id, str) or not attempt_id.startswith("a4-goal001-"):
        raise A4OwnerEvaluatorError("profile attempt is invalid")
    coverage = package.get("coverage")
    if not isinstance(coverage, Mapping) or coverage.get("expected_units") != expected_query_count or coverage.get("completed_units") != expected_query_count:
        raise A4OwnerEvaluatorError("A4 profile coverage is incomplete")
    rankings = package.get("rankings")
    if not isinstance(rankings, Mapping) or len(rankings) != expected_query_count:
        raise A4OwnerEvaluatorError("ranking package does not cover HDEV-100")
    _hash(evaluator_binding_sha256, "evaluator_binding_sha256")
    _hash(hdev_commitment_sha256, "hdev_commitment_sha256")
    try:
        metrics = _metrics(metric_evaluator(rankings))
    except (TypeError, ValueError, KeyError) as error:
        raise A4OwnerEvaluatorError("Owner-local metric evaluation failed closed") from error
    latency = _latency(package.get("latency"))
    resource = _resource(package.get("resource"))
    body = {
        "schema_version": "myis.armindex-a4-profile-aggregate-result.v1",
        "status": "PASS_A4_OWNER_LOCAL_AGGREGATE_EVALUATION",
        "profile_id": checked_profile["profile_id"],
        "attempt_id": attempt_id,
        "request_sha256": _hash(package.get("request_sha256"), "request_sha256"),
        "ranking_sha256": _hash(package.get("ranking_sha256"), "ranking_sha256"),
        "evaluator_binding_sha256": evaluator_binding_sha256,
        "hdev_commitment_sha256": hdev_commitment_sha256,
        "metrics": metrics,
        "latency": latency,
        "resource": resource,
        "coverage": {"expected_units": expected_query_count, "completed_units": expected_query_count},
        "determinism": bool(package.get("determinism", True)),
        "failures": int(package.get("failures", 0)),
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def validate_a4_profile_result(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an aggregate profile result before projection or Selection."""

    item = _aggregate(value, "profile result")
    required = {
        "schema_version", "status", "profile_id", "attempt_id", "request_sha256", "ranking_sha256",
        "evaluator_binding_sha256", "hdev_commitment_sha256", "metrics", "latency", "resource",
        "coverage", "determinism", "failures", "protected_payload_included", "per_query_outcomes_included", "receipt_sha256",
    }
    if set(item) != required or item["schema_version"] != "myis.armindex-a4-profile-aggregate-result.v1" or item["status"] != "PASS_A4_OWNER_LOCAL_AGGREGATE_EVALUATION":
        raise A4OwnerEvaluatorError("profile result schema is invalid")
    if item["profile_id"] not in _PROFILES and item["profile_id"] != "ARM-03_RESEARCH_REFERENCE":
        raise A4OwnerEvaluatorError("profile result identity is invalid")
    for field in ("request_sha256", "ranking_sha256", "evaluator_binding_sha256", "hdev_commitment_sha256"):
        _hash(item[field], field)
    _metrics(item["metrics"])
    _latency(item["latency"])
    _resource(item["resource"])
    coverage = item["coverage"]
    if not isinstance(coverage, Mapping) or coverage.get("expected_units") != 100 or coverage.get("completed_units") != 100:
        raise A4OwnerEvaluatorError("profile result coverage is incomplete")
    if item["protected_payload_included"] is not False or item["per_query_outcomes_included"] is not False:
        raise A4OwnerEvaluatorError("profile result crossed protected boundary")
    if isinstance(item["failures"], bool) or not isinstance(item["failures"], int) or item["failures"] < 0:
        raise A4OwnerEvaluatorError("failure count is invalid")
    _self_hash(item, "receipt_sha256", "profile result")
    return item


def build_a4_coverage_receipt(results: Sequence[Mapping[str, Any]], *, attempt_id: str, hdev_commitment_sha256: str) -> dict[str, Any]:
    """Require complete commercial profile coverage and preserve research reference separately."""

    _hash(hdev_commitment_sha256, "hdev_commitment_sha256")
    checked = [validate_a4_profile_result(row) for row in results]
    if any(row["attempt_id"] != attempt_id for row in checked):
        raise A4OwnerEvaluatorError("profile attempts are mixed")
    commercial = [row for row in checked if row["profile_id"] in _PROFILES]
    if {row["profile_id"] for row in commercial} != set(_PROFILES) or len(commercial) != 3:
        raise A4OwnerEvaluatorError("FAST/BALANCED/DEEP coverage is incomplete")
    research = [row for row in checked if row["profile_id"] == "ARM-03_RESEARCH_REFERENCE"]
    if len(research) > 1:
        raise A4OwnerEvaluatorError("research reference is duplicated")
    body = {
        "schema_version": "myis.armindex-a4-coverage-receipt.v1",
        "status": "PASS_A4_COMPLETE_PROFILE_COVERAGE",
        "attempt_id": attempt_id,
        "hdev_commitment_sha256": hdev_commitment_sha256,
        "commercial_profiles": sorted((_receipt_ref(row) for row in commercial), key=lambda row: row["profile_id"]),
        "research_reference": None if not research else _receipt_ref(research[0]),
        "commercial_profile_count": 3,
        "research_reference_count": len(research),
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def build_legal_transfer_receipt(
    *,
    attempt_id: str,
    mini_status: str,
    mini_metrics: Mapping[str, Any],
    full_status: str = "NOT_RUN",
    full_metrics: Mapping[str, Any] | None = None,
    isolation_sha256: str,
    a5_reserve_intact: bool,
) -> dict[str, Any]:
    """Record an isolated legal-transfer diagnostic without patent feedback."""

    if mini_status not in {"PASS", "FAIL", "UNSUPPORTED", "STOPPED_WITH_EVIDENCE"}:
        raise A4OwnerEvaluatorError("legal mini status is invalid")
    if full_status not in {"PASS", "FAIL", "UNSUPPORTED", "STOPPED_WITH_EVIDENCE", "NOT_RUN"}:
        raise A4OwnerEvaluatorError("legal full status is invalid")
    if full_status != "NOT_RUN" and mini_status != "PASS":
        raise A4OwnerEvaluatorError("full legal transfer requires a valid mini diagnostic")
    if full_status != "NOT_RUN" and not a5_reserve_intact:
        raise A4OwnerEvaluatorError("full legal transfer requires the A5 reserve")
    _hash(isolation_sha256, "isolation_sha256")
    mini = _legal_metrics(mini_metrics)
    full = None if full_metrics is None else _legal_metrics(full_metrics)
    body = {
        "schema_version": "myis.armindex-a4-legal-transfer-receipt.v1",
        "status": "PASS_A4_LEGAL_TRANSFER_ISOLATED",
        "attempt_id": attempt_id,
        "mini": {"status": mini_status, "metrics": mini},
        "full": {"status": full_status, "metrics": full},
        "isolation_sha256": isolation_sha256,
        "patent_retuning": False,
        "protected_payload_included": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "a5_reserve_intact": bool(a5_reserve_intact),
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _profile(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not isinstance(value.get("profile_id"), str):
        raise A4OwnerEvaluatorError("profile is invalid")
    if value["profile_id"] not in _PROFILES and value["profile_id"] != "ARM-03_RESEARCH_REFERENCE":
        raise A4OwnerEvaluatorError("profile identity is invalid")
    if "attempt_id" in value and (not isinstance(value.get("attempt_id"), str) or not value["attempt_id"].startswith("a4-goal001-")):
        raise A4OwnerEvaluatorError("profile attempt is invalid")
    return dict(value)


def _metrics(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise A4OwnerEvaluatorError("metrics are invalid")
    aliases = {"recall_at_100_out": "recall_at_100", "ndcg_at_100_out": "ndcg_at_100", "ndcg_at_10_out": "ndcg_at_10"}
    source = {aliases.get(key, key): val for key, val in value.items()}
    if set(source) != set(_METRICS):
        raise A4OwnerEvaluatorError("metric set is invalid")
    result: dict[str, str] = {}
    for key in _METRICS:
        try:
            number = Decimal(str(source[key]))
        except (InvalidOperation, ValueError) as error:
            raise A4OwnerEvaluatorError("metric is invalid") from error
        if not number.is_finite() or number < 0 or number > 1:
            raise A4OwnerEvaluatorError("metric is outside [0, 1]")
        result[key] = format(number, "f")
    return result


def _latency(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise A4OwnerEvaluatorError("latency is invalid")
    source = {"p50_ms": value.get("p50_ms", value.get("p50")), "p95_ms": value.get("p95_ms", value.get("p95")), "p99_ms": value.get("p99_ms", value.get("p99")), "throughput_qps": value.get("throughput_qps", value.get("qps"))}
    if any(item is None for item in source.values()):
        raise A4OwnerEvaluatorError("latency fields are incomplete")
    result = {key: float(item) for key, item in source.items()}
    if any(not math.isfinite(item) or item < 0 for item in result.values()):
        raise A4OwnerEvaluatorError("latency values are invalid")
    return result


def _resource(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise A4OwnerEvaluatorError("resource is invalid")
    source = {"cost_usd": value.get("cost_usd", value.get("cost")), "ram_gib": value.get("ram_gib", value.get("ram")), "vram_gib": value.get("vram_gib", value.get("vram")), "index_size_bytes": value.get("index_size_bytes", value.get("index_size"))}
    if any(item is None for item in source.values()):
        raise A4OwnerEvaluatorError("resource fields are incomplete")
    result = {key: float(item) for key, item in source.items()}
    if any(not math.isfinite(item) or item < 0 for item in result.values()):
        raise A4OwnerEvaluatorError("resource values are invalid")
    return result


def _legal_metrics(value: Mapping[str, Any]) -> dict[str, Any]:
    item = _aggregate(value, "legal metrics")
    return dict(item)


def _aggregate(value: Mapping[str, Any], role: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A4OwnerEvaluatorError(f"{role} must be an object")
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A4OwnerEvaluatorError(f"{role} contains protected payload") from error
    return result


def _receipt_ref(value: Mapping[str, Any]) -> dict[str, str]:
    return {"profile_id": value["profile_id"], "receipt_sha256": value["receipt_sha256"]}


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise A4OwnerEvaluatorError(f"{field} must be SHA-256")
    return value


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    _hash(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4OwnerEvaluatorError(f"{role} self-hash mismatch")


__all__ = [
    "A4OwnerEvaluatorError",
    "build_a4_coverage_receipt",
    "build_legal_transfer_receipt",
    "evaluate_a4_profile_owner_local",
    "validate_a4_profile_result",
]
