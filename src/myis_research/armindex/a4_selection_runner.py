"""Owner-local aggregate runner for the single A4 Selection exposure.

The input is intentionally a protected Owner Store artifact containing paired
unit scores.  The runner never writes those scores to the repository or to the
receipt; only aggregate statistics and hash-bound decisions leave the Owner
Store.  Synthetic fixtures are the only inputs used by repository tests.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from pathlib import Path
import random
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..p2.measured_state import AdvisoryFileLock, atomic_write_json
from ..protection import assert_aggregate_only
from .a4_selection import consume_selection_once


BOOTSTRAP_RESAMPLES = 10_000
CONFIDENCE_LEVEL = 0.95
RECALL_TOLERANCE = 0.005
NDCG100_TOLERANCE = 0.002
METRICS = ("recall_at_100", "ndcg_at_100", "ndcg_at_10")


class A4SelectionRunnerError(ValueError):
    """Raised when the protected Selection handoff is incomplete or unsafe."""


def run_selection_owner_local(
    registry: Mapping[str, Any],
    protected_input: Mapping[str, Any],
    *,
    preflight_counter: Mapping[str, Any],
    selection_output_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate frozen finalists once and emit an aggregate-only receipt.

    ``protected_input`` must remain in the Owner Store.  It may contain paired
    metric vectors and operational summaries, but it is never returned.  A
    preflight counter with ``preflight_count == 1`` is required and a pre-
    existing output path is rejected, making a second exposure fail closed.
    """

    checked_registry = _safe_copy(registry, "Selection registry")
    _validate_registry(checked_registry)
    counter = _safe_copy(preflight_counter, "Selection preflight counter")
    _validate_counter(counter, checked_registry["registry_sha256"])
    source = _protected_input(protected_input, role="Selection input")
    if source.get("selection_query_count") != 125:
        raise A4SelectionRunnerError("Selection is frozen at exactly 125 queries")
    if source.get("selection_population") != "OUT":
        raise A4SelectionRunnerError("Selection primary population must be OUT")
    _validate_selection_input_hashes(source)
    rows = source.get("comparisons")
    if not isinstance(rows, list) or not rows:
        raise A4SelectionRunnerError("Selection input requires comparisons")
    results = [_evaluate_comparison(row, source) for row in rows]
    comparisons = [result[0] for result in results]
    receipt = consume_selection_once(checked_registry, comparisons)
    body = {
        **receipt,
        "schema_version": "myis.armindex-a4-selection-owner-local-receipt.v1",
        "selection_input_sha256": _hash(source.get("selection_input_sha256"), "selection_input_sha256"),
        "preflight_counter_sha256": _hash(counter.get("counter_sha256"), "counter_sha256"),
        "comparison_family_id": _text(source.get("comparison_family_id"), "comparison_family_id"),
        "selection_query_count": 125,
        "selection_population": "OUT",
        "paired_out_vectors_sha256": source["paired_out_vectors_sha256"],
        "evaluator_handoff_sha256": source["evaluator_handoff_sha256"],
        "claim_boundary": "One aggregate-only A4 Selection exposure; no Final result and no protected payload exported.",
        "protected_payload_included": False,
    }
    # consume_selection_once hashes its own schema; re-hash after the runner
    # adds the Owner-local provenance fields.
    body.pop("receipt_sha256", None)
    assert_aggregate_only(body)
    output = {**body, "receipt_sha256": canonical_sha256(body)}
    if selection_output_path is not None:
        _write_once(Path(selection_output_path), output)
    return output


def _evaluate_comparison(value: Mapping[str, Any], source: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    item = _protected_input(value, role="Selection comparison")
    required = {"comparison_id", "left_system_sha256", "right_system_sha256", "metrics"}
    if set(item) - (required | {"operational"}) or not required.issubset(item):
        raise A4SelectionRunnerError("Selection comparison fields are invalid")
    left = _hash(item["left_system_sha256"], "left_system_sha256")
    right = _hash(item["right_system_sha256"], "right_system_sha256")
    if left == right:
        raise A4SelectionRunnerError("Selection comparison cannot compare a system with itself")
    metrics = item["metrics"]
    if not isinstance(metrics, Mapping) or set(metrics) != set(METRICS):
        raise A4SelectionRunnerError("Selection metric vectors are incomplete")
    aggregates: dict[str, dict[str, float]] = {}
    primary_vector: tuple[list[float], list[float]] | None = None
    for metric in METRICS:
        vectors = metrics[metric]
        if not isinstance(vectors, Mapping) or set(vectors) != {"left", "right"}:
            raise A4SelectionRunnerError(f"{metric} vectors are invalid")
        # Selection is a 125-query scope, but this handoff evaluates the
        # frozen OUT population only (90 judged queries).  Legacy fixtures that
        # omit an explicit population count continue to use 125 vectors.
        expected_count = int(source.get("selection_evaluated_query_count", source["selection_query_count"]))
        if expected_count <= 0 or expected_count > source["selection_query_count"]:
            raise A4SelectionRunnerError("Selection evaluated query count is invalid")
        lv = _vector(vectors["left"], metric, expected_count=expected_count)
        rv = _vector(vectors["right"], metric, expected_count=expected_count)
        if len(lv) != len(rv) or not lv:
            raise A4SelectionRunnerError(f"{metric} paired coverage is invalid")
        if primary_vector is None:
            primary_vector = (lv, rv)
        delta = [a - b for a, b in zip(lv, rv)]
        ci_low, ci_high = _bootstrap_ci(delta, int(source.get("bootstrap_seed", 0)))
        aggregates[metric] = {
            "left_mean": _mean(lv),
            "right_mean": _mean(rv),
            "paired_delta": _mean(delta),
            "ci_lower": ci_low,
            "ci_upper": ci_high,
            "unit_count": len(delta),
        }
    assert primary_vector is not None
    operational = _operational(item.get("operational", {}))
    decision = _lexicographic_decision(aggregates, operational)
    primary_delta = [a - b for a, b in zip(*primary_vector)]
    wins = sum(value > 0 for value in primary_delta)
    ties = sum(value == 0 for value in primary_delta)
    losses = len(primary_delta) - wins - ties
    paired_effect = {
        "comparison_family_id": _text(source.get("comparison_family_id"), "comparison_family_id"),
        "metric": "recall_at_100",
        "left_mean": aggregates["recall_at_100"]["left_mean"],
        "right_mean": aggregates["recall_at_100"]["right_mean"],
        "paired_delta": aggregates["recall_at_100"]["paired_delta"],
        "ci_lower": aggregates["recall_at_100"]["ci_lower"],
        "ci_upper": aggregates["recall_at_100"]["ci_upper"],
        "rank_biserial_effect": (wins - losses) / len(primary_delta),
        "unit_count": len(primary_delta),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": int(source.get("bootstrap_seed", 0)),
    }
    comparison = {
        "comparison_id": _text(item["comparison_id"], "comparison_id"),
        "left_system_sha256": left,
        "right_system_sha256": right,
        "decision": decision,
        "paired_effect": paired_effect,
        "win_tie_loss": {"wins": wins, "ties": ties, "losses": losses},
    }
    return comparison, aggregates


def _lexicographic_decision(aggregates: Mapping[str, Mapping[str, float]], operational: Mapping[str, Mapping[str, float]]) -> str:
    differences = {metric: float(row["left_mean"]) - float(row["right_mean"]) for metric, row in aggregates.items()}
    if abs(differences["recall_at_100"]) >= RECALL_TOLERANCE:
        return "LEFT" if differences["recall_at_100"] > 0 else "RIGHT"
    if abs(differences["ndcg_at_100"]) >= NDCG100_TOLERANCE:
        return "LEFT" if differences["ndcg_at_100"] > 0 else "RIGHT"
    if differences["ndcg_at_10"] != 0:
        return "LEFT" if differences["ndcg_at_10"] > 0 else "RIGHT"
    for key in ("p95_latency_ms", "cost_usd", "index_size_bytes"):
        if key in operational["left"] and key in operational["right"] and operational["left"][key] != operational["right"][key]:
            return "LEFT" if operational["left"][key] < operational["right"][key] else "RIGHT"
    return "TIE"


def _bootstrap_ci(values: Sequence[float], seed: int) -> tuple[float, float]:
    if isinstance(seed, bool) or seed < 0:
        raise A4SelectionRunnerError("bootstrap_seed must be a non-negative integer")
    rng = random.Random(seed)
    n = len(values)
    samples = sorted(sum(values[index] for index in (rng.randrange(n) for _ in range(n))) / n for _ in range(BOOTSTRAP_RESAMPLES))
    return _percentile(samples, 0.025), _percentile(samples, 0.975)


def _percentile(values: Sequence[float], fraction: float) -> float:
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    return float(values[lower] + (values[upper] - values[lower]) * (position - lower))


def _validate_registry(value: Mapping[str, Any]) -> None:
    if value.get("status") != "FROZEN_BEFORE_SELECTION" or value.get("selection_accesses") != 0 or value.get("final_accesses") != 0:
        raise A4SelectionRunnerError("Selection registry is not fresh and frozen")
    finalists = value.get("finalists")
    if not isinstance(finalists, list) or not finalists:
        raise A4SelectionRunnerError("Selection registry has no finalists")
    systems = {_hash(row.get("system_sha256"), "system_sha256") for row in finalists if isinstance(row, Mapping)}
    if len(systems) != len(finalists):
        raise A4SelectionRunnerError("Selection registry systems are duplicated")
    if value.get("registry_sha256") != canonical_sha256({key: item for key, item in value.items() if key != "registry_sha256"}):
        raise A4SelectionRunnerError("Selection registry self-hash drift")


def _validate_counter(value: Mapping[str, Any], registry_sha256: str) -> None:
    if value.get("schema_version") != "myis.armindex-a4-selection-preflight-counter.v1" or value.get("preflight_count") != 1:
        raise A4SelectionRunnerError("Selection preflight counter is not consumed exactly once")
    if value.get("selection_accesses") != 0 or value.get("final_accesses") != 0 or value.get("frozen_bindings_sha256") != registry_sha256:
        raise A4SelectionRunnerError("Selection preflight counter binding is invalid")
    checks = value.get("checks")
    if not isinstance(checks, Mapping) or any(item is not True for item in checks.values()):
        raise A4SelectionRunnerError("Selection preflight checks are incomplete")


def _protected_input(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A4SelectionRunnerError(f"{role} must be an object")
    item = deepcopy(dict(value))
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4SelectionRunnerError(f"{role} contains protected payload") from error
    return item


def _safe_copy(value: Mapping[str, Any], role: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A4SelectionRunnerError(f"{role} must be an object")
    item = deepcopy(dict(value))
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4SelectionRunnerError(f"{role} contains protected payload") from error
    return item


def _vector(value: Any, metric: str, *, expected_count: int) -> list[float]:
    if not isinstance(value, list):
        raise A4SelectionRunnerError(f"{metric} vector must be a list")
    result = [float(item) for item in value]
    if len(result) != expected_count or any(not math.isfinite(item) or item < 0 or item > 1 for item in result):
        raise A4SelectionRunnerError(f"{metric} vector has invalid values")
    return result


def _operational(value: Any) -> dict[str, dict[str, float]]:
    if not isinstance(value, Mapping):
        raise A4SelectionRunnerError("operational summaries are invalid")
    result: dict[str, dict[str, float]] = {}
    for side in ("left", "right"):
        raw = value.get(side, {})
        if not isinstance(raw, Mapping):
            raise A4SelectionRunnerError("operational summaries are invalid")
        result[side] = {}
        for key in ("p95_latency_ms", "cost_usd", "index_size_bytes"):
            if key in raw:
                number = float(raw[key])
                if not math.isfinite(number) or number < 0:
                    raise A4SelectionRunnerError("operational summary value is invalid")
                result[side][key] = number
    return result


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    path = path.resolve()
    lock = AdvisoryFileLock(path.with_name(path.name + ".lock"))
    with lock:
        if path.exists() or path.is_symlink():
            raise A4SelectionRunnerError("Selection output already exists")
        atomic_write_json(path, value)


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise A4SelectionRunnerError(f"{field} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise A4SelectionRunnerError(f"{field} must be SHA-256") from error
    return value


def _validate_selection_input_hashes(source: Mapping[str, Any]) -> None:
    required = {
        "selection_input_sha256",
        "paired_out_vectors_sha256",
        "evaluator_handoff_sha256",
        "selection_query_count",
        "selection_population",
        "comparison_family_id",
        "bootstrap_seed",
        "comparisons",
    }
    if set(source) not in (required, required | {"selection_evaluated_query_count"}):
        raise A4SelectionRunnerError("Selection handoff fields are incomplete or unexpected")
    _hash(source["selection_input_sha256"], "selection_input_sha256")
    _hash(source["paired_out_vectors_sha256"], "paired_out_vectors_sha256")
    _hash(source["evaluator_handoff_sha256"], "evaluator_handoff_sha256")
    if source["selection_input_sha256"] != canonical_sha256(
        {key: value for key, value in source.items() if key != "selection_input_sha256"}
    ):
        raise A4SelectionRunnerError("Selection input hash drifted")
    if source["paired_out_vectors_sha256"] != canonical_sha256(_vector_payload(source)):
        raise A4SelectionRunnerError("paired OUT vector hash drifted")
    if "selection_evaluated_query_count" in source:
        count = source["selection_evaluated_query_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0 or count > source["selection_query_count"]:
            raise A4SelectionRunnerError("Selection evaluated query count is invalid")


def _vector_payload(source: Mapping[str, Any]) -> dict[str, Any]:
    rows = source.get("comparisons")
    if not isinstance(rows, list):
        raise A4SelectionRunnerError("Selection comparisons are invalid")
    payload = []
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise A4SelectionRunnerError("Selection comparison is invalid")
        metrics = raw.get("metrics")
        if not isinstance(metrics, Mapping):
            raise A4SelectionRunnerError("Selection metric vectors are invalid")
        payload.append(
            {
                "comparison_id": raw.get("comparison_id"),
                "left_system_sha256": raw.get("left_system_sha256"),
                "right_system_sha256": raw.get("right_system_sha256"),
                "metrics": metrics,
            }
        )
    return {"comparisons": payload}


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise A4SelectionRunnerError(f"{field} must be non-empty text")
    return value


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values))


__all__ = ["A4SelectionRunnerError", "run_selection_owner_local"]
