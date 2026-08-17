"""Remote-only ranking contract for post-admission three-primary A3 units.

Rankings emitted here are transient protected Owner-local inputs.  They must
not be written to a repository-visible receipt or safe-return artifact.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
import math
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .a3_three_primary_execution import PRIMARY_ARMS


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]+$")
_REQUEST_KEYS = {
    "schema_version",
    "status",
    "operation_id",
    "operation_kind",
    "runtime_bindings_sha256",
    "execution_contract_sha256",
    "source_arm_id",
    "target_arm_id",
    "fixed_union_control_id",
    "retrieval_arm_ids",
    "output_depth_by_arm",
    "remote_asset_sha256s",
    "request_sha256",
}
_RESULT_KEYS = {
    "schema_version",
    "status",
    "operation_id",
    "operation_kind",
    "request_sha256",
    "ranking_sha256",
    "rankings",
    "coverage",
    "latency",
    "qrels_opened",
    "membership_opened",
    "receipt_sha256",
}
_UNION_ARMS = {
    "best_single": None,
    "all_primary_rrf60": set(PRIMARY_ARMS),
    "top_two_rrf60": None,
    "top_three_rrf60": set(PRIMARY_ARMS),
    "commercial_only_fixed_union": {"ARM-04", "ARM-05"},
}


class A3ThreePrimaryRemoteRetrieverError(ValueError):
    """Raised when a remote-only A3 ranking boundary is invalid."""


def build_remote_cell_request(
    execution_contract: Mapping[str, Any],
    *,
    operation_id: str,
    operation_kind: str,
    source_arm_id: str | None,
    target_arm_id: str | None,
    fixed_union_control_id: str | None,
    retrieval_arm_ids: list[str],
    output_depth_by_arm: Mapping[str, int],
    remote_asset_sha256s: Mapping[str, str],
) -> dict[str, Any]:
    """Build one remote ranking request after a validated A3 execution contract.

    The request contains no qrels, membership, evaluator binding, rankings, or
    query/family outcome.  Concrete remote paths are intentionally supplied by
    an Owner-local launcher and are not part of this portable contract.
    """

    contract = _validate_execution_contract(execution_contract)
    _validate_operation(
        contract,
        operation_kind=operation_kind,
        source_arm_id=source_arm_id,
        target_arm_id=target_arm_id,
        fixed_union_control_id=fixed_union_control_id,
        retrieval_arm_ids=retrieval_arm_ids,
        output_depth_by_arm=output_depth_by_arm,
    )
    assets = _validate_remote_assets(remote_asset_sha256s)
    if not _STABLE_ID.fullmatch(operation_id):
        raise A3ThreePrimaryRemoteRetrieverError("remote operation_id is invalid")
    body = {
        "schema_version": "myis.armindex-a3-three-primary-remote-cell-request.v1",
        "status": "READY_REMOTE_RETRIEVAL_ONLY",
        "operation_id": operation_id,
        "operation_kind": operation_kind,
        "runtime_bindings_sha256": contract["runtime_bindings_sha256"],
        "execution_contract_sha256": contract["execution_contract_sha256"],
        "source_arm_id": source_arm_id,
        "target_arm_id": target_arm_id,
        "fixed_union_control_id": fixed_union_control_id,
        "retrieval_arm_ids": list(retrieval_arm_ids),
        "output_depth_by_arm": dict(output_depth_by_arm),
        "remote_asset_sha256s": assets,
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def run_remote_retrieval_cell(
    request: Mapping[str, Any],
    *,
    ranker: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Run one injected remote ranker and retain rankings for Owner-local use.

    The ranker implementation is provided only by a post-admission remote
    launcher.  This function performs neither file transfer nor network I/O.
    """

    checked = validate_remote_cell_request(request)
    raw = dict(ranker(checked))
    rankings = _validate_rankings(raw.get("rankings"), depth_by_arm=checked["output_depth_by_arm"])
    coverage = _validate_coverage(raw.get("coverage"), expected=len(rankings))
    latency = _validate_latency(raw.get("latency"))
    body = {
        "schema_version": "myis.armindex-a3-three-primary-remote-ranking-package.v1",
        "status": "PASS_A3_REMOTE_RETRIEVAL",
        "operation_id": checked["operation_id"],
        "operation_kind": checked["operation_kind"],
        "request_sha256": checked["request_sha256"],
        "ranking_sha256": canonical_sha256(rankings),
        "rankings": rankings,
        "coverage": coverage,
        "latency": latency,
        "qrels_opened": False,
        "membership_opened": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def validate_remote_cell_request(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a serializable, protected-data-free remote request."""

    request = _aggregate_copy(value, role="remote request")
    if set(request) != _REQUEST_KEYS:
        raise A3ThreePrimaryRemoteRetrieverError("remote request fields are incomplete")
    if (
        request["schema_version"] != "myis.armindex-a3-three-primary-remote-cell-request.v1"
        or request["status"] != "READY_REMOTE_RETRIEVAL_ONLY"
    ):
        raise A3ThreePrimaryRemoteRetrieverError("remote request identity is invalid")
    for field in ("runtime_bindings_sha256", "execution_contract_sha256"):
        _require_sha256(request[field], field)
    _validate_request_shape(request)
    _validate_remote_assets(request["remote_asset_sha256s"])
    _self_hash(request, "request_sha256", role="remote request")
    return request


def validate_remote_ranking_package(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a transient ranking package before Owner-local evaluation."""

    package = deepcopy(dict(value))
    if set(package) != _RESULT_KEYS:
        raise A3ThreePrimaryRemoteRetrieverError("remote ranking package fields are incomplete")
    if (
        package["schema_version"] != "myis.armindex-a3-three-primary-remote-ranking-package.v1"
        or package["status"] != "PASS_A3_REMOTE_RETRIEVAL"
        or package["qrels_opened"] is not False
        or package["membership_opened"] is not False
    ):
        raise A3ThreePrimaryRemoteRetrieverError("remote ranking package boundary drift")
    for field in ("request_sha256", "ranking_sha256"):
        _require_sha256(package[field], field)
    if not _STABLE_ID.fullmatch(str(package["operation_id"])):
        raise A3ThreePrimaryRemoteRetrieverError("remote ranking operation identity is invalid")
    depths = _ranking_depths(package["rankings"])
    rankings = _validate_rankings(package["rankings"], depth_by_arm=depths)
    if package["ranking_sha256"] != canonical_sha256(rankings):
        raise A3ThreePrimaryRemoteRetrieverError("remote ranking commitment drift")
    _validate_coverage(package["coverage"], expected=len(rankings))
    _validate_latency(package["latency"])
    _self_hash(package, "receipt_sha256", role="remote ranking package")
    return package


def _validate_execution_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    contract = _aggregate_copy(value, role="A3 execution contract")
    required = {
        "schema_version", "status", "runtime_bindings_sha256", "transfer_matrix",
        "fixed_union_sha256", "harness_batch_sha256s", "execution_order",
        "selection_permitted", "final_permitted", "provider_contact_performed",
        "remote_execution_performed", "execution_contract_sha256",
    }
    if set(contract) != required or (
        contract["schema_version"] != "myis.armindex-a3-three-primary-execution-contract.v1"
        or contract["status"] != "READY_FOR_POST_ADMISSION_EXECUTION"
        or contract["selection_permitted"] is not False
        or contract["final_permitted"] is not False
        or contract["provider_contact_performed"] is not False
        or contract["remote_execution_performed"] is not False
    ):
        raise A3ThreePrimaryRemoteRetrieverError("A3 execution contract is not launch-safe")
    _require_sha256(contract["runtime_bindings_sha256"], "runtime_bindings_sha256")
    _require_sha256(contract["fixed_union_sha256"], "fixed_union_sha256")
    rows = contract["transfer_matrix"]
    expected_pairs = {(source, target) for source in PRIMARY_ARMS for target in PRIMARY_ARMS}
    pairs = {
        (row.get("source_arm_id"), row.get("target_arm_id"))
        for row in rows
        if isinstance(row, Mapping)
    } if isinstance(rows, list) else set()
    if len(rows) != 9 or pairs != expected_pairs:
        raise A3ThreePrimaryRemoteRetrieverError("A3 execution contract does not contain the exact 3x3 matrix")
    batches = contract["harness_batch_sha256s"]
    if not isinstance(batches, list) or not 1 <= len(batches) <= 3:
        raise A3ThreePrimaryRemoteRetrieverError(
            "A3 Extended requires one to three complete HarnessOpt batches"
        )
    for digest in batches:
        _require_sha256(digest, "harness_batch_sha256s")
    if len(set(batches)) != len(batches):
        raise A3ThreePrimaryRemoteRetrieverError("A3 HarnessOpt batch commitments are duplicated")
    _self_hash(contract, "execution_contract_sha256", role="A3 execution contract")
    return contract


def _validate_operation(
    contract: Mapping[str, Any],
    *,
    operation_kind: str,
    source_arm_id: str | None,
    target_arm_id: str | None,
    fixed_union_control_id: str | None,
    retrieval_arm_ids: list[str],
    output_depth_by_arm: Mapping[str, int],
) -> None:
    if operation_kind == "transfer_cell":
        if (
            source_arm_id not in PRIMARY_ARMS
            or target_arm_id not in PRIMARY_ARMS
            or fixed_union_control_id is not None
            or retrieval_arm_ids != [target_arm_id]
        ):
            raise A3ThreePrimaryRemoteRetrieverError("transfer cell identity is invalid")
        pairs = {
            (row.get("source_arm_id"), row.get("target_arm_id"))
            for row in contract["transfer_matrix"]
            if isinstance(row, Mapping)
        }
        if (source_arm_id, target_arm_id) not in pairs:
            raise A3ThreePrimaryRemoteRetrieverError("transfer cell is outside the exact 3x3 matrix")
    elif operation_kind == "fixed_union":
        if source_arm_id is not None or target_arm_id is not None or fixed_union_control_id not in _UNION_ARMS:
            raise A3ThreePrimaryRemoteRetrieverError("fixed union identity is invalid")
        expected = _UNION_ARMS[fixed_union_control_id]
        if expected is not None and set(retrieval_arm_ids) != expected:
            raise A3ThreePrimaryRemoteRetrieverError("fixed union arm set drifted from the preregistration")
        if fixed_union_control_id == "best_single" and len(retrieval_arm_ids) != 1:
            raise A3ThreePrimaryRemoteRetrieverError("best single requires exactly one primary arm")
        if fixed_union_control_id == "top_two_rrf60" and len(retrieval_arm_ids) != 2:
            raise A3ThreePrimaryRemoteRetrieverError("top-two union requires exactly two primary arms")
    else:
        raise A3ThreePrimaryRemoteRetrieverError("remote operation kind is unsupported")
    if not retrieval_arm_ids or len(retrieval_arm_ids) != len(set(retrieval_arm_ids)) or not set(retrieval_arm_ids) <= set(PRIMARY_ARMS):
        raise A3ThreePrimaryRemoteRetrieverError("remote operation must use unique primary arms")
    if not isinstance(output_depth_by_arm, Mapping) or set(output_depth_by_arm) != set(retrieval_arm_ids):
        raise A3ThreePrimaryRemoteRetrieverError("remote output depth must cover each retrieval arm")
    depths = list(output_depth_by_arm.values())
    if any(isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= 2000 for depth in depths):
        raise A3ThreePrimaryRemoteRetrieverError("remote output depth is invalid")
    if operation_kind == "fixed_union" and len(set(depths)) != 1:
        raise A3ThreePrimaryRemoteRetrieverError("fixed union requires equal retrieval depth")


def _validate_request_shape(request: Mapping[str, Any]) -> None:
    kind = request["operation_kind"]
    source, target = request["source_arm_id"], request["target_arm_id"]
    control = request["fixed_union_control_id"]
    arms = request["retrieval_arm_ids"]
    depths = request["output_depth_by_arm"]
    if kind == "transfer_cell":
        if source not in PRIMARY_ARMS or target not in PRIMARY_ARMS or control is not None or arms != [target]:
            raise A3ThreePrimaryRemoteRetrieverError("transfer cell identity is invalid")
    elif kind == "fixed_union":
        if source is not None or target is not None or control not in _UNION_ARMS:
            raise A3ThreePrimaryRemoteRetrieverError("fixed union identity is invalid")
        expected = _UNION_ARMS[control]
        if expected is not None and set(arms) != expected:
            raise A3ThreePrimaryRemoteRetrieverError("fixed union arm set drifted from the preregistration")
        if control == "best_single" and len(arms) != 1:
            raise A3ThreePrimaryRemoteRetrieverError("best single requires exactly one primary arm")
        if control == "top_two_rrf60" and len(arms) != 2:
            raise A3ThreePrimaryRemoteRetrieverError("top-two union requires exactly two primary arms")
    else:
        raise A3ThreePrimaryRemoteRetrieverError("remote operation kind is unsupported")
    if not isinstance(arms, list) or not arms or len(arms) != len(set(arms)) or not set(arms) <= set(PRIMARY_ARMS):
        raise A3ThreePrimaryRemoteRetrieverError("remote operation must use unique primary arms")
    if not isinstance(depths, Mapping) or set(depths) != set(arms):
        raise A3ThreePrimaryRemoteRetrieverError("remote output depth must cover each retrieval arm")
    values = list(depths.values())
    if any(isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= 2000 for depth in values):
        raise A3ThreePrimaryRemoteRetrieverError("remote output depth is invalid")
    if kind == "fixed_union" and len(set(values)) != 1:
        raise A3ThreePrimaryRemoteRetrieverError("fixed union requires equal retrieval depth")


def _validate_remote_assets(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"corpus_sha256", "queries_sha256", "model_sha256s"}:
        raise A3ThreePrimaryRemoteRetrieverError("remote assets must bind corpus, queries, and models")
    _require_sha256(value["corpus_sha256"], "corpus_sha256")
    _require_sha256(value["queries_sha256"], "queries_sha256")
    models = value["model_sha256s"]
    if not isinstance(models, Mapping) or set(models) != set(PRIMARY_ARMS):
        raise A3ThreePrimaryRemoteRetrieverError("remote model assets must cover the three primary arms")
    for arm_id, digest in models.items():
        _require_sha256(digest, f"model_sha256s.{arm_id}")
    return {
        "corpus_sha256": str(value["corpus_sha256"]),
        "queries_sha256": str(value["queries_sha256"]),
        "model_sha256s": {str(arm): str(digest) for arm, digest in models.items()},
    }


def _validate_rankings(value: Any, *, depth_by_arm: Mapping[str, int]) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(value, Mapping) or not value:
        raise A3ThreePrimaryRemoteRetrieverError("remote rankings are invalid")
    expected_depth = max(depth_by_arm.values())
    result: dict[str, list[dict[str, Any]]] = {}
    for query_token, rows in value.items():
        if not isinstance(query_token, str) or not query_token or not isinstance(rows, list) or len(rows) != expected_depth:
            raise A3ThreePrimaryRemoteRetrieverError("remote ranking coverage is invalid")
        checked_rows: list[dict[str, Any]] = []
        families: set[str] = set()
        for rank, row in enumerate(rows, start=1):
            if not isinstance(row, Mapping) or set(row) != {"family_token", "rank", "score"}:
                raise A3ThreePrimaryRemoteRetrieverError("remote ranking row is invalid")
            family, score = row["family_token"], row["score"]
            if (
                not isinstance(family, str)
                or not family
                or family in families
                or row["rank"] != rank
                or isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(float(score))
            ):
                raise A3ThreePrimaryRemoteRetrieverError("remote ranking row is invalid")
            families.add(family)
            checked_rows.append({"family_token": family, "rank": rank, "score": float(score)})
        result[query_token] = checked_rows
    return result


def _ranking_depths(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping) or not value:
        raise A3ThreePrimaryRemoteRetrieverError("remote rankings are invalid")
    lengths = {len(rows) for rows in value.values() if isinstance(rows, list)}
    if len(lengths) != 1:
        raise A3ThreePrimaryRemoteRetrieverError("remote ranking depth is inconsistent")
    return {"ARM-03": next(iter(lengths))}


def _validate_coverage(value: Any, *, expected: int) -> dict[str, int]:
    if not isinstance(value, Mapping) or value != {"expected_units": expected, "completed_units": expected}:
        raise A3ThreePrimaryRemoteRetrieverError("remote retrieval coverage is incomplete")
    return dict(value)


def _validate_latency(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping) or set(value) != {"wall_seconds", "search_p95_seconds"}:
        raise A3ThreePrimaryRemoteRetrieverError("remote retrieval latency is invalid")
    result = {key: float(item) for key, item in value.items()}
    if any(not math.isfinite(item) or item < 0 for item in result.values()):
        raise A3ThreePrimaryRemoteRetrieverError("remote retrieval latency is invalid")
    return result


def _aggregate_copy(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A3ThreePrimaryRemoteRetrieverError(f"{role}: {error}") from error
    return result


def _require_sha256(value: Any, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise A3ThreePrimaryRemoteRetrieverError(f"{field} must be SHA-256")


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    _require_sha256(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A3ThreePrimaryRemoteRetrieverError(f"{role} self-hash does not bind its contents")


__all__ = [
    "A3ThreePrimaryRemoteRetrieverError",
    "build_remote_cell_request",
    "run_remote_retrieval_cell",
    "validate_remote_cell_request",
    "validate_remote_ranking_package",
]
