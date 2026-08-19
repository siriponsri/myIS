"""One-shot, aggregate-safe A4 Selection analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .a4_execution import freeze_selection_registry

_HASH = re.compile(r"^[a-f0-9]{64}$")


class A4SelectionError(ValueError):
    """Raised when Selection is incomplete, duplicated, or exposed twice."""


def consume_selection_once(
    registry: Mapping[str, Any],
    comparisons: Sequence[Mapping[str, Any]],
    *,
    selection_accesses: int = 0,
    bootstrap_resamples: int = 10_000,
    correction_rule: str = "holm_bonferroni_preregistered_family",
) -> dict[str, Any]:
    """Consume the single Selection access and emit aggregate paired evidence.

    Comparisons are pre-aggregated by the protected Owner-local evaluator.  No
    per-query deltas are accepted here.
    """

    checked = _aggregate(registry, "Selection registry")
    if checked.get("status") != "FROZEN_BEFORE_SELECTION" or not isinstance(checked.get("finalists"), list):
        raise A4SelectionError("Selection registry is not frozen")
    _hash(checked.get("registry_sha256"), "registry_sha256")
    if checked["registry_sha256"] != canonical_sha256({key: item for key, item in checked.items() if key != "registry_sha256"}):
        raise A4SelectionError("Selection registry self-hash drift")
    if checked.get("selection_accesses") != 0 or checked.get("final_accesses") != 0:
        raise A4SelectionError("Selection registry access counters are not fresh")
    if selection_accesses != 0:
        raise A4SelectionError("Selection has already been consumed")
    if bootstrap_resamples != 10_000:
        raise A4SelectionError("Selection requires exactly 10,000 paired bootstrap resamples")
    if not comparisons:
        raise A4SelectionError("Selection requires comparator evidence")
    rows = [_comparison(item) for item in comparisons]
    finalist_systems = {row.get("system_sha256") for row in checked["finalists"] if isinstance(row, Mapping)}
    if any(row["left_system_sha256"] not in finalist_systems or row["right_system_sha256"] not in finalist_systems for row in rows):
        raise A4SelectionError("Selection comparison is outside the frozen finalist registry")
    body = {
        "schema_version": "myis.armindex-a4-selection-receipt.v1",
        "status": "PASS_A4_SELECTION_EXPOSED_ONCE",
        "registry_sha256": checked["registry_sha256"],
        "comparison_count": len(rows),
        "comparisons": rows,
        "bootstrap": {"paired_resamples": bootstrap_resamples, "confidence_level": 0.95},
        "correction_rule": correction_rule,
        "selection_accesses": 1,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def build_selection_frontier(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize a non-dominated profile frontier from validated aggregates."""

    rows = [_aggregate(row, "frontier result") for row in results]
    if not rows:
        raise A4SelectionError("frontier requires results")
    required = {"system_sha256", "profile_id", "metrics", "latency", "resource"}
    if any(set(row) != required for row in rows):
        raise A4SelectionError("frontier row schema is invalid")
    for row in rows:
        _hash(row["system_sha256"], "system_sha256")
        metrics = row["metrics"]
        recall = float(metrics.get("recall_at_100", metrics.get("recall_at_100_out", -1)))
        latency = float(row["latency"].get("p95_ms", row["latency"].get("p95", -1)))
        cost = float(row["resource"].get("cost_usd", row["resource"].get("cost", -1)))
        if not 0 <= recall <= 1 or latency < 0 or cost < 0:
            raise A4SelectionError("frontier dimensions are invalid")
    nondominated: list[str] = []
    for candidate in rows:
        cr = float(candidate["metrics"].get("recall_at_100", candidate["metrics"].get("recall_at_100_out")))
        cl = float(candidate["latency"].get("p95_ms", candidate["latency"].get("p95")))
        cc = float(candidate["resource"].get("cost_usd", candidate["resource"].get("cost")))
        dominated = False
        for other in rows:
            if other is candidate:
                continue
            orc = float(other["metrics"].get("recall_at_100", other["metrics"].get("recall_at_100_out")))
            orl = float(other["latency"].get("p95_ms", other["latency"].get("p95")))
            orcst = float(other["resource"].get("cost_usd", other["resource"].get("cost")))
            if orc >= cr and orl <= cl and orcst <= cc and (orc > cr or orl < cl or orcst < cc):
                dominated = True
                break
        if not dominated:
            nondominated.append(candidate["system_sha256"])
    body = {
        "schema_version": "myis.armindex-a4-commercial-frontier.v1",
        "status": "PASS_A4_NON_DOMINATED_FRONTIER",
        "candidate_count": len(rows),
        "nondominated_system_sha256s": sorted(nondominated),
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _comparison(value: Mapping[str, Any]) -> dict[str, Any]:
    item = _aggregate(value, "Selection comparison")
    required = {"comparison_id", "left_system_sha256", "right_system_sha256", "decision", "paired_effect", "win_tie_loss"}
    if set(item) != required:
        raise A4SelectionError("Selection comparison fields are incomplete")
    _hash(item["left_system_sha256"], "left_system_sha256")
    _hash(item["right_system_sha256"], "right_system_sha256")
    if item["left_system_sha256"] == item["right_system_sha256"]:
        raise A4SelectionError("Selection comparison cannot compare a system with itself")
    if item["decision"] not in {"LEFT", "RIGHT", "TIE", "UNSUPPORTED"}:
        raise A4SelectionError("Selection decision is invalid")
    if not isinstance(item["paired_effect"], Mapping) or not isinstance(item["win_tie_loss"], Mapping):
        raise A4SelectionError("Selection aggregate statistics are invalid")
    return item


def _aggregate(value: Mapping[str, Any], role: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A4SelectionError(f"{role} must be an object")
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A4SelectionError(f"{role} contains protected payload") from error
    return result


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise A4SelectionError(f"{field} must be SHA-256")
    return value


__all__ = ["A4SelectionError", "build_selection_frontier", "consume_selection_once", "freeze_selection_registry"]
