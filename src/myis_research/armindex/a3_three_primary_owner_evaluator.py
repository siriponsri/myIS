"""Owner-local aggregate evaluation and safe-return contracts for A3 ranks."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .a3_three_primary_remote_retriever import (
    A3ThreePrimaryRemoteRetrieverError,
    validate_remote_cell_request,
    validate_remote_ranking_package,
)


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_METRIC_NAMES = ("recall_at_100/out", "ndcg_at_100/out", "ndcg_at_10/out")
_RESULT_KEYS = {
    "schema_version",
    "status",
    "operation_id",
    "operation_kind",
    "request_sha256",
    "ranking_sha256",
    "evaluator_binding_sha256",
    "evaluator_input_sha256",
    "metrics",
    "latency",
    "coverage",
    "protected_payload_included",
    "per_query_outcomes_included",
    "receipt_sha256",
}


class A3ThreePrimaryOwnerEvaluatorError(ValueError):
    """Raised when protected local evaluation cannot emit an aggregate receipt."""


def evaluate_remote_ranking_owner_local(
    request: Mapping[str, Any],
    ranking_package: Mapping[str, Any],
    *,
    evaluator_binding_sha256: str,
    evaluator_input_sha256: str,
    metric_evaluator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate transient rankings inside Owner-local storage.

    ``metric_evaluator`` is the only component allowed to open the protected
    qrels/membership surface.  It receives rankings only and must return the
    three aggregate metrics; this module never serializes protected inputs.
    """

    checked_request = validate_remote_cell_request(request)
    try:
        package = validate_remote_ranking_package(ranking_package)
    except A3ThreePrimaryRemoteRetrieverError as error:
        raise A3ThreePrimaryOwnerEvaluatorError("remote ranking package is invalid") from error
    if (
        package["operation_id"] != checked_request["operation_id"]
        or package["operation_kind"] != checked_request["operation_kind"]
        or package["request_sha256"] != checked_request["request_sha256"]
    ):
        raise A3ThreePrimaryOwnerEvaluatorError("remote ranking package is not bound to its request")
    expected_depth = max(checked_request["output_depth_by_arm"].values())
    if any(len(rows) != expected_depth for rows in package["rankings"].values()):
        raise A3ThreePrimaryOwnerEvaluatorError("remote ranking depth does not match its request")
    _require_sha256(evaluator_binding_sha256, "evaluator_binding_sha256")
    _require_sha256(evaluator_input_sha256, "evaluator_input_sha256")
    try:
        metrics = _validate_metrics(metric_evaluator(package["rankings"]))
    except (ValueError, TypeError) as error:
        raise A3ThreePrimaryOwnerEvaluatorError("Owner-local metric evaluation failed closed") from error
    body = {
        "schema_version": "myis.armindex-a3-three-primary-aggregate-result.v1",
        "status": "PASS_A3_OWNER_LOCAL_AGGREGATE_EVALUATION",
        "operation_id": checked_request["operation_id"],
        "operation_kind": checked_request["operation_kind"],
        "request_sha256": checked_request["request_sha256"],
        "ranking_sha256": package["ranking_sha256"],
        "evaluator_binding_sha256": evaluator_binding_sha256,
        "evaluator_input_sha256": evaluator_input_sha256,
        "metrics": metrics,
        "latency": package["latency"],
        "coverage": package["coverage"],
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def build_aggregate_safe_return_receipt(
    aggregate_results: Sequence[Mapping[str, Any]], *, runtime_bindings_sha256: str
) -> dict[str, Any]:
    """Build a safe-return receipt that contains hashes/counts but no rankings."""

    _require_sha256(runtime_bindings_sha256, "runtime_bindings_sha256")
    if not aggregate_results:
        raise A3ThreePrimaryOwnerEvaluatorError("safe return requires aggregate results")
    results = [validate_aggregate_result(result) for result in aggregate_results]
    operation_ids = [result["operation_id"] for result in results]
    if len(operation_ids) != len(set(operation_ids)):
        raise A3ThreePrimaryOwnerEvaluatorError("safe return cannot contain duplicate operation results")
    body = {
        "schema_version": "myis.armindex-a3-three-primary-safe-return-receipt.v1",
        "status": "PASS_A3_AGGREGATE_SAFE_RETURN",
        "runtime_bindings_sha256": runtime_bindings_sha256,
        "aggregate_result_count": len(results),
        "aggregate_result_receipt_sha256s": {
            result["operation_id"]: result["receipt_sha256"] for result in sorted(results, key=lambda item: item["operation_id"])
        },
        "rankings_returned": False,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def validate_aggregate_result(value: Mapping[str, Any]) -> dict[str, Any]:
    """Reject ranking/per-query content before it can enter a safe artifact."""

    result = _aggregate_copy(value, role="aggregate result")
    if set(result) != _RESULT_KEYS:
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate result fields are incomplete")
    if (
        result["schema_version"] != "myis.armindex-a3-three-primary-aggregate-result.v1"
        or result["status"] != "PASS_A3_OWNER_LOCAL_AGGREGATE_EVALUATION"
        or result["protected_payload_included"] is not False
        or result["per_query_outcomes_included"] is not False
    ):
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate result boundary drift")
    if not isinstance(result["operation_id"], str) or not result["operation_id"]:
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate result operation identity is invalid")
    for field in (
        "request_sha256",
        "ranking_sha256",
        "evaluator_binding_sha256",
        "evaluator_input_sha256",
    ):
        _require_sha256(result[field], field)
    _validate_metrics(result["metrics"])
    _validate_latency(result["latency"])
    _validate_coverage(result["coverage"])
    _self_hash(result, "receipt_sha256", role="aggregate result")
    return result


def _validate_metrics(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(_METRIC_NAMES):
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate metric set is invalid")
    result: dict[str, str] = {}
    for name in _METRIC_NAMES:
        try:
            metric = Decimal(str(value[name]))
        except (InvalidOperation, ValueError) as error:
            raise A3ThreePrimaryOwnerEvaluatorError("aggregate metric is invalid") from error
        if not metric.is_finite() or not Decimal("0") <= metric <= Decimal("1"):
            raise A3ThreePrimaryOwnerEvaluatorError("aggregate metric is outside [0, 1]")
        result[name] = format(metric, "f")
    return result


def _validate_latency(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping) or set(value) != {"wall_seconds", "search_p95_seconds"}:
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate latency is invalid")
    result = {key: float(item) for key, item in value.items()}
    if any(item < 0 for item in result.values()):
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate latency is invalid")
    return result


def _validate_coverage(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping) or set(value) != {"expected_units", "completed_units"}:
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate coverage is invalid")
    result = {key: int(item) for key, item in value.items()}
    if any(isinstance(item, bool) or item < 0 for item in value.values()) or result["expected_units"] != result["completed_units"]:
        raise A3ThreePrimaryOwnerEvaluatorError("aggregate coverage is incomplete")
    return result


def _aggregate_copy(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A3ThreePrimaryOwnerEvaluatorError(f"{role}: {error}") from error
    return result


def _require_sha256(value: Any, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise A3ThreePrimaryOwnerEvaluatorError(f"{field} must be SHA-256")


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    _require_sha256(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A3ThreePrimaryOwnerEvaluatorError(f"{role} self-hash does not bind its contents")


__all__ = [
    "A3ThreePrimaryOwnerEvaluatorError",
    "build_aggregate_safe_return_receipt",
    "evaluate_remote_ranking_owner_local",
    "validate_aggregate_result",
]
