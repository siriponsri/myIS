"""Owner-local protected qrels/membership handoff for Selection-125."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from ..dapfam_p1 import iter_arrow_rows
from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .a4_selection_materializer import (
    A3_TRAIN250_OPAQUE_SCOPE,
    PARENT_SPLIT_SHA256,
    SELECTION_COUNT,
    validate_selection_input_materialization,
)


class A4SelectionEvaluatorInputError(ValueError):
    """Raised when protected Selection evaluator coverage is incomplete."""


def materialize_selection_evaluator_inputs(
    *,
    selection_input_root: Path,
    protected_split_path: Path,
    evaluator_relations_path: Path,
    output_root: Path,
    owner_store_root: Path,
    attempt_id: str,
) -> dict[str, Any]:
    """Derive opaque Selection qrels and OUT membership from frozen relations."""

    selection_receipt = validate_selection_input_materialization(selection_input_root, expected_attempt_id=attempt_id)
    if selection_receipt["parent_split_sha256"] != PARENT_SPLIT_SHA256:
        raise A4SelectionEvaluatorInputError("Selection input parent split commitment drift")
    store = _directory(owner_store_root, "Owner Store")
    split = _object(protected_split_path, "protected parent split")
    relation_path = _file(evaluator_relations_path, "evaluator relations")
    destination = _fresh(output_root, store)
    if file_sha256(relation_path) != selection_receipt["evaluator_relations_sha256"]:
        raise A4SelectionEvaluatorInputError("evaluator relation hash is not bound to Selection input")
    selection_ids = _selection_ids(split)
    qrels: dict[str, dict[str, int]] = {_token(query_id): {} for query_id in selection_ids}
    eligible: dict[str, bool] = {_token(query_id): False for query_id in selection_ids}
    for row in iter_arrow_rows((relation_path,), ("query_id", "relevant_id", "relevance_score", "domain_rel")):
        query_id = str(row.get("query_id") or "")
        if query_id not in selection_ids:
            continue
        score = row.get("relevance_score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or score <= 0:
            continue
        token = _token(query_id)
        family = _family_token(str(row.get("relevant_id") or ""))
        if not family:
            raise A4SelectionEvaluatorInputError("Selection relation family identity is invalid")
        qrels[token][family] = 1
        if str(row.get("domain_rel")) == "OUT":
            eligible[token] = True
    if any(not values for values in qrels.values()):
        raise A4SelectionEvaluatorInputError("Selection qrels coverage is incomplete")
    if not any(eligible.values()):
        raise A4SelectionEvaluatorInputError("Selection OUT membership is empty")
    destination.mkdir(parents=True, exist_ok=False)
    protected = destination / "protected"
    protected.mkdir()
    qrels_path = protected / "selection-125-qrels.jsonl"
    membership_path = protected / "selection-125-membership.jsonl"
    _write_jsonl(qrels_path, [{"work_token": token, "relevance": qrels[token]} for token in sorted(qrels)])
    _write_jsonl(membership_path, [{"work_token": token, "eligible_out": eligible[token]} for token in sorted(eligible)])
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a4-selection-evaluator-inputs.v1",
        "status": "PASS_A4_SELECTION_EVALUATOR_INPUTS_MATERIALIZED",
        "attempt_id": attempt_id,
        "scope": "Selection-125",
        "population": "OUT",
        "selection_query_count": SELECTION_COUNT,
        "selection_input_receipt_sha256": selection_receipt["receipt_sha256"],
        "protected_split_file_sha256": file_sha256(protected_split_path),
        "parent_split_sha256": split["split_sha256"],
        "evaluator_relations_sha256": file_sha256(relation_path),
        "qrels_sha256": file_sha256(qrels_path),
        "membership_sha256": file_sha256(membership_path),
        "judged_query_count": sum(bool(values) for values in qrels.values()),
        "out_query_count": sum(eligible.values()),
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "claim_boundary": "Protected evaluator inputs only; no ranking or metric result.",
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _write_json(destination / "A4_SELECTION_EVALUATOR_INPUTS_RECEIPT.json", receipt)
    return receipt


def _selection_ids(split: Mapping[str, Any]) -> set[str]:
    if split.get("schema_version") != "myis.protected-split.v1" or split.get("split_sha256") != PARENT_SPLIT_SHA256:
        raise A4SelectionEvaluatorInputError("parent split is not canonical")
    values = split.get("selection")
    if not isinstance(values, list) or len(values) != SELECTION_COUNT or len(set(values)) != SELECTION_COUNT:
        raise A4SelectionEvaluatorInputError("Selection membership is not exactly 125")
    return {str(value) for value in values}


def _token(source_id: str) -> str:
    return "Q-" + hashlib.sha256(f"{A3_TRAIN250_OPAQUE_SCOPE}:Q:{source_id}".encode()).hexdigest()[:32]


def _family_token(source_id: str) -> str:
    if not source_id:
        return ""
    return "F-" + hashlib.sha256(f"{A3_TRAIN250_OPAQUE_SCOPE}:F:{source_id}".encode()).hexdigest()[:32]


def _object(path: Path, role: str) -> dict[str, Any]:
    value = json.loads(_file(path, role).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise A4SelectionEvaluatorInputError(f"{role} is not an object")
    return value


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def _file(path: Path, role: str) -> Path:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise A4SelectionEvaluatorInputError(f"{role} must be a regular file")
    return resolved


def _directory(path: Path, role: str) -> Path:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_dir():
        raise A4SelectionEvaluatorInputError(f"{role} must be a real directory")
    return resolved


def _fresh(path: Path, store: Path) -> Path:
    resolved = path.resolve()
    if resolved == store or not resolved.is_relative_to(store) or resolved.exists():
        raise A4SelectionEvaluatorInputError("output must be a fresh Owner Store child")
    return resolved
