"""Owner-local evaluator for the hash-bound A4 Selection-125 exposure.

This module is intentionally separate from the HDEV-100 evaluator.  Ranking
packages are opaque and transient; qrels and OUT membership are opened only
inside Owner Store.  The only durable handoff is an aggregate-safe contract
whose vectors remain under a fresh Owner-Store root for the one-shot runner.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import math
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_measured_executor_v16 import FamilyRank
from .a2_owner_local_engine import _metrics


SELECTION_QUERY_COUNT = 125
SELECTION_POPULATION = "OUT"
METRICS = ("recall_at_100", "ndcg_at_100", "ndcg_at_10")
PACKAGE_SCHEMA = "myis.armindex-a4-remote-ranking-package.v1"
PACKAGE_STATUS = "PASS_A4_REMOTE_RANKING_PACKAGE"


class A4SelectionEvaluatorError(ValueError):
    """Raised when Selection package or protected evaluator coverage is invalid."""


def build_selection_handoff(
    *,
    selection_input_root: Path,
    evaluator_input_root: Path,
    packages: Mapping[str, Mapping[str, Any]],
    systems: Mapping[str, str],
    output_root: Path,
    attempt_id: str,
    evaluator_handoff_sha256: str,
    comparison_family_id: str = "a4-selection-frozen-finalists-v1",
    bootstrap_seed: int = 42,
    expected_selection_scope_sha256: str | None = None,
) -> dict[str, Any]:
    """Evaluate packages and write a protected vector handoff below Owner Store.

    ``packages`` maps comparison labels to returned package objects.  Each
    package must cover all 125 opaque work tokens.  ``systems`` maps the same
    labels to frozen finalist system hashes; labels are never emitted in
    protected query rows or metrics.
    """

    if not attempt_id.startswith("a4-goal001-"):
        raise A4SelectionEvaluatorError("attempt identity is invalid")
    _hash(evaluator_handoff_sha256, "evaluator_handoff_sha256")
    if not isinstance(comparison_family_id, str) or not comparison_family_id.strip():
        raise A4SelectionEvaluatorError("comparison family is invalid")
    if isinstance(bootstrap_seed, bool) or not isinstance(bootstrap_seed, int) or bootstrap_seed < 0:
        raise A4SelectionEvaluatorError("bootstrap seed is invalid")
    selection_root = _directory(selection_input_root, "Selection input")
    evaluator_root = _directory(evaluator_input_root, "Selection evaluator input")
    selection_receipt = _json(selection_root / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json")
    scope = _json(selection_root / "A4_SELECTION_SCOPE.json")
    evaluator_receipt = _json(evaluator_root / "A4_SELECTION_EVALUATOR_INPUTS_RECEIPT.json")
    if selection_receipt.get("scope") != "Selection-125" or selection_receipt.get("selection_query_count") != SELECTION_QUERY_COUNT:
        raise A4SelectionEvaluatorError("Selection input receipt is not Selection-125")
    scope_hash = _hash(scope.get("scope_sha256"), "selection_scope_sha256")
    if expected_selection_scope_sha256 is not None and scope_hash != expected_selection_scope_sha256:
        raise A4SelectionEvaluatorError("Selection scope hash mismatch")
    if evaluator_receipt.get("scope") != "Selection-125" or evaluator_receipt.get("judged_query_count") != SELECTION_QUERY_COUNT:
        raise A4SelectionEvaluatorError("Selection evaluator receipt coverage is invalid")
    qrel_rows = _jsonl(evaluator_root / "protected" / "selection-125-qrels.jsonl")
    membership_rows = _jsonl(evaluator_root / "protected" / "selection-125-membership.jsonl")
    qrels = _qrels(qrel_rows)
    membership = _membership(membership_rows)
    tokens = set(qrels)
    if tokens != set(membership) or len(tokens) != SELECTION_QUERY_COUNT:
        raise A4SelectionEvaluatorError("Selection qrels/membership coverage is incomplete")
    eligible = {token for token, value in membership.items() if value}
    if len(eligible) != int(evaluator_receipt.get("out_query_count", -1)):
        raise A4SelectionEvaluatorError("OUT membership count does not match evaluator receipt")
    if not isinstance(packages, Mapping) or not packages:
        raise A4SelectionEvaluatorError("Selection packages are empty")
    if not isinstance(systems, Mapping) or set(systems) != set(packages):
        raise A4SelectionEvaluatorError("finalist system bindings are incomplete")
    for label, system in systems.items():
        if not isinstance(label, str) or not label.strip():
            raise A4SelectionEvaluatorError("comparison label is invalid")
        _hash(system, f"{label}.system_sha256")

    rankings_by_label: dict[str, dict[str, list[FamilyRank]]] = {}
    package_refs: dict[str, dict[str, Any]] = {}
    for label, package in packages.items():
        checked = _validate_package(package, expected_scope_hash=scope_hash, attempt_id=attempt_id)
        raw = checked["rankings"]
        typed = {
            token: tuple(FamilyRank(row["family_token"], int(row["rank"]), float(row["score"])) for row in rows)
            for token, rows in raw.items()
        }
        rankings_by_label[label] = typed
        package_refs[label] = {
            "request_sha256": checked["request_sha256"],
            "ranking_sha256": checked["ranking_sha256"],
            "profile_id": checked.get("profile_id", label),
            "latency": _aggregate_latency(checked.get("latency")),
            "resource": _aggregate_resource(checked.get("resource")),
        }
        if set(typed) != tokens:
            raise A4SelectionEvaluatorError("ranking package tokens do not match Selection evaluator coverage")

    labels = sorted(rankings_by_label)
    comparisons: list[dict[str, Any]] = []
    for left_label in labels:
        for right_label in labels:
            if labels.index(left_label) >= labels.index(right_label):
                continue
            left = rankings_by_label[left_label]
            right = rankings_by_label[right_label]
            vectors: dict[str, dict[str, list[float]]] = {}
            for metric_index, metric in enumerate(METRICS):
                left_vector = _per_query_metric(left, qrels, eligible, metric_index)
                right_vector = _per_query_metric(right, qrels, eligible, metric_index)
                vectors[metric] = {"left": left_vector, "right": right_vector}
            comparisons.append({
                "comparison_id": f"{left_label}-vs-{right_label}",
                "left_system_sha256": systems[left_label],
                "right_system_sha256": systems[right_label],
                "metrics": vectors,
                "operational": {
                    "left": {**package_refs[left_label]["latency"], **package_refs[left_label]["resource"]},
                    "right": {**package_refs[right_label]["latency"], **package_refs[right_label]["resource"]},
                },
            })
    if not comparisons:
        raise A4SelectionEvaluatorError("at least two distinct finalists are required")
    vector_payload = {"comparisons": [
        {key: row[key] for key in ("comparison_id", "left_system_sha256", "right_system_sha256", "metrics")}
        for row in comparisons
    ]}
    paired_hash = canonical_sha256(vector_payload)
    source = {
        "selection_input_sha256": "",
        "paired_out_vectors_sha256": paired_hash,
        "evaluator_handoff_sha256": evaluator_handoff_sha256,
        "selection_query_count": SELECTION_QUERY_COUNT,
        "selection_evaluated_query_count": len(eligible),
        "selection_population": SELECTION_POPULATION,
        "comparison_family_id": comparison_family_id,
        "bootstrap_seed": bootstrap_seed,
        "comparisons": comparisons,
    }
    source["selection_input_sha256"] = canonical_sha256({key: value for key, value in source.items() if key != "selection_input_sha256"})
    try:
        assert_aggregate_only({key: value for key, value in source.items() if key != "comparisons"})
    except ValueError as error:
        raise A4SelectionEvaluatorError("aggregate handoff contains protected fields") from error
    destination = _fresh_directory(output_root)
    protected_path = destination / "protected" / "selection-125-paired-out-vectors.json"
    protected_path.parent.mkdir(parents=True, exist_ok=False)
    protected_path.write_text(canonical_json(source) + "\n", encoding="utf-8")
    receipt_body = {
        "schema_version": "myis.armindex-a4-selection-evaluator-handoff.v1",
        "status": "PASS_A4_SELECTION_PAIRED_VECTORS",
        "attempt_id": attempt_id,
        "selection_scope_sha256": scope_hash,
        "selection_query_count": SELECTION_QUERY_COUNT,
        "selection_population": SELECTION_POPULATION,
        "out_query_count": len(eligible),
        "selection_input_sha256": source["selection_input_sha256"],
        "paired_out_vectors_sha256": paired_hash,
        "evaluator_handoff_sha256": evaluator_handoff_sha256,
        "protected_vector_file_sha256": file_sha256(protected_path),
        "comparison_count": len(comparisons),
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    (destination / "A4_SELECTION_EVALUATOR_HANDOFF_RECEIPT.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    return receipt


def load_handoff(path: Path) -> dict[str, Any]:
    """Load and validate the protected vector handoff for the one-shot runner."""
    root = _directory(path, "Selection handoff")
    receipt = _json(root / "A4_SELECTION_EVALUATOR_HANDOFF_RECEIPT.json")
    source = _json(root / "protected" / "selection-125-paired-out-vectors.json")
    if receipt.get("status") != "PASS_A4_SELECTION_PAIRED_VECTORS" or receipt.get("selection_query_count") != SELECTION_QUERY_COUNT:
        raise A4SelectionEvaluatorError("Selection handoff receipt is invalid")
    if receipt.get("protected_vector_file_sha256") != file_sha256(root / "protected" / "selection-125-paired-out-vectors.json"):
        raise A4SelectionEvaluatorError("Selection vector file hash drift")
    if source.get("selection_input_sha256") != receipt.get("selection_input_sha256"):
        raise A4SelectionEvaluatorError("Selection input hash drift")
    return source


def _validate_package(value: Mapping[str, Any], *, expected_scope_hash: str, attempt_id: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A4SelectionEvaluatorError("ranking package is invalid")
    item = dict(value)
    if item.get("schema_version") != PACKAGE_SCHEMA or item.get("status") != PACKAGE_STATUS:
        raise A4SelectionEvaluatorError("ranking package schema/status is invalid")
    if item.get("attempt_id") != attempt_id or item.get("selection_scope_sha256") != expected_scope_hash or item.get("selection_query_count") != SELECTION_QUERY_COUNT:
        raise A4SelectionEvaluatorError("ranking package Selection binding is invalid")
    required_hashes = ("request_sha256", "ranking_sha256")
    for field in required_hashes:
        _hash(item.get(field), field)
    rankings = item.get("rankings")
    if not isinstance(rankings, Mapping) or len(rankings) != SELECTION_QUERY_COUNT:
        raise A4SelectionEvaluatorError("ranking package coverage is not 125")
    normalized: dict[str, list[dict[str, Any]]] = {}
    for token, rows in rankings.items():
        if not isinstance(token, str) or not token.startswith("Q-") or not isinstance(rows, list) or len(rows) != 100:
            raise A4SelectionEvaluatorError("ranking package top-100 rows are invalid")
        checked_rows = []
        for rank, row in enumerate(rows, 1):
            if not isinstance(row, Mapping) or set(row) != {"family_token", "rank", "score"} or row.get("rank") != rank:
                raise A4SelectionEvaluatorError("ranking row schema is invalid")
            family, score = row.get("family_token"), row.get("score")
            if not isinstance(family, str) or not family or isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(float(score)):
                raise A4SelectionEvaluatorError("ranking row value is invalid")
            checked_rows.append({"family_token": family, "rank": rank, "score": float(score)})
        normalized[token] = checked_rows
    if item.get("ranking_sha256") != canonical_sha256(normalized):
        raise A4SelectionEvaluatorError("ranking package hash drift")
    return {**item, "rankings": normalized}


def _per_query_metric(rankings: Mapping[str, Sequence[FamilyRank]], qrels: Mapping[str, Mapping[str, int]], eligible: set[str], metric_index: int) -> list[float]:
    # The scientific population is OUT, so vectors contain the 90 eligible
    # units while the enclosing Selection scope remains hash-bound to 125.
    values: list[float] = []
    for token in sorted(eligible):
        values.append(float(_metrics({token: tuple(rankings[token])}, qrels, {token})[metric_index]))
    return values


def _qrels(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        token, relevance = row.get("work_token"), row.get("relevance")
        if not isinstance(token, str) or token in result or not isinstance(relevance, Mapping) or not relevance:
            raise A4SelectionEvaluatorError("qrels rows are malformed")
        result[token] = {str(family): int(grade) for family, grade in relevance.items()}
    return result


def _membership(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for row in rows:
        token, eligible = row.get("work_token"), row.get("eligible_out")
        if not isinstance(token, str) or token in result or not isinstance(eligible, bool):
            raise A4SelectionEvaluatorError("membership rows are malformed")
        result[token] = eligible
    return result


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A4SelectionEvaluatorError(f"invalid JSON: {path.name}") from error
    if not isinstance(value, dict):
        raise A4SelectionEvaluatorError(f"JSON object required: {path.name}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A4SelectionEvaluatorError(f"invalid JSONL: {path.name}") from error
    if any(not isinstance(row, dict) for row in rows):
        raise A4SelectionEvaluatorError(f"JSONL objects required: {path.name}")
    return rows


def _aggregate_latency(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise A4SelectionEvaluatorError("package latency is invalid")
    result = {key: float(value[key]) for key in ("p50_ms", "p95_ms", "p99_ms", "throughput_qps") if key in value}
    if len(result) != 4 or any(not math.isfinite(number) or number < 0 for number in result.values()):
        raise A4SelectionEvaluatorError("package latency is incomplete")
    return result


def _aggregate_resource(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise A4SelectionEvaluatorError("package resource is invalid")
    result = {key: float(value[key]) for key in ("cost_usd", "ram_gib", "vram_gib", "index_size_bytes") if key in value}
    if len(result) != 4 or any(not math.isfinite(number) or number < 0 for number in result.values()):
        raise A4SelectionEvaluatorError("package resource is incomplete")
    return result


def _directory(path: Path, role: str) -> Path:
    value = path.resolve(strict=True)
    if not value.is_dir() or value.is_symlink():
        raise A4SelectionEvaluatorError(f"{role} must be a real directory")
    return value


def _fresh_directory(path: Path) -> Path:
    value = path.resolve()
    if value.exists() or value.is_symlink():
        raise A4SelectionEvaluatorError("handoff output root must be fresh")
    value.mkdir(parents=True)
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise A4SelectionEvaluatorError(f"{field} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise A4SelectionEvaluatorError(f"{field} must be SHA-256") from error
    return value


__all__ = ["A4SelectionEvaluatorError", "SELECTION_QUERY_COUNT", "build_selection_handoff", "load_handoff"]
