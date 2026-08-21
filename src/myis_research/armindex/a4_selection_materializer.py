"""Owner-local materialization of the canonical A4 Selection-125 inputs.

This module deliberately stops before evaluation.  It binds the protected
Selection membership to the complete canonical query payload and emits an
opaque query package plus aggregate-safe hashes under the Owner Store.  The
one-shot Selection runner must consume a separately produced paired-vector
handoff; this materializer never opens Selection and never creates metrics.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from ..dapfam_p1 import iter_arrow_rows
from .a1_2_owner_local_protected_materializer_v15 import _query_text
from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256


SELECTION_COUNT = 125
TRAIN_COUNT = 250
FINAL_COUNT = 872
PARENT_COUNT = TRAIN_COUNT + SELECTION_COUNT + FINAL_COUNT
PARENT_SPLIT_SHA256 = "33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6"
CANONICAL_QUERIES_SHA256 = "b596c2dcc73399840c0a9c2143b23e8497bbaa33af8dbb2a8877ad52e5f9f2fd"
CANONICAL_RELATIONS_SHA256 = "861a991875f3594e301c84ffe0ad4f0fbd6edcf07c534c172609f40bf623e298"
SPLIT_ALGORITHM = "sha256-seed-colon-id-lexical-v1"
SPLIT_SEED = 42
A3_TRAIN250_OPAQUE_SCOPE = "742b38916b194950515ffcb911c9f6b9f44f458b962c376db6a187c8b971a2e6"


class A4SelectionMaterializerError(ValueError):
    """Raised when canonical Selection input coverage or provenance is invalid."""


def materialize_selection_inputs(
    *,
    protected_split_path: Path,
    source_queries_path: Path,
    evaluator_relations_path: Path,
    output_root: Path,
    owner_store_root: Path,
    attempt_id: str,
    expected_parent_split_sha256: str = PARENT_SPLIT_SHA256,
    expected_source_queries_sha256: str = CANONICAL_QUERIES_SHA256,
    expected_evaluator_relations_sha256: str = CANONICAL_RELATIONS_SHA256,
) -> dict[str, Any]:
    """Materialize exactly the 125 canonical Selection queries.

    ``source_queries_path`` must be a complete, protected owner-local JSONL
    projection of the frozen 1,247-query payload.  Each row needs ``query_id``
    (or ``source_id``) and non-empty ``text``.  A work-token-only package is
    rejected because it cannot be independently bound to the parent split.
    """

    if not isinstance(attempt_id, str) or not attempt_id.startswith("a4-"):
        raise A4SelectionMaterializerError("A4 attempt identity is invalid")
    if not isinstance(expected_parent_split_sha256, str) or len(expected_parent_split_sha256) != 64:
        raise A4SelectionMaterializerError("expected parent split commitment is invalid")
    store = _directory(owner_store_root, "Owner Store")
    split_path = _regular_file(protected_split_path, "protected parent split")
    queries_path = _regular_file(source_queries_path, "canonical source queries")
    relations_path = _regular_file(evaluator_relations_path, "evaluator relations")
    if file_sha256(queries_path) != expected_source_queries_sha256:
        raise A4SelectionMaterializerError("canonical query payload hash mismatch")
    if file_sha256(relations_path) != expected_evaluator_relations_sha256:
        raise A4SelectionMaterializerError("canonical evaluator relations hash mismatch")
    destination = _fresh_output(output_root, store)
    try:
        split = _load_object(split_path, "protected parent split")
        selection_ids, parent_ids = _validate_split(split, expected_parent_split_sha256)
        query_rows = _load_query_rows(queries_path)
        if set(query_rows) != parent_ids:
            missing = len(parent_ids - set(query_rows))
            extra = len(set(query_rows) - parent_ids)
            raise A4SelectionMaterializerError(
                f"canonical query coverage mismatch: missing={missing}, extra={extra}"
            )
        selected = [query_rows[source_id] for source_id in selection_ids]
        if len(selected) != SELECTION_COUNT:
            raise A4SelectionMaterializerError("Selection query coverage is not exactly 125")
        opaque_rows = sorted(
            ({"work_token": _opaque_work_token(source_id), "text": _row_text(query_rows[source_id])} for source_id in selection_ids),
            key=lambda row: row["work_token"],
        )
        destination.mkdir(parents=True, exist_ok=False)
        protected = destination / "protected"
        protected.mkdir()
        query_output = protected / "selection-125-queries.jsonl"
        _write_jsonl(query_output, opaque_rows)
        body: dict[str, Any] = {
            "schema_version": "myis.armindex-a4-selection-input-materialization.v1",
            "status": "PASS_A4_SELECTION_INPUT_MATERIALIZED",
            "attempt_id": attempt_id,
            "scope": "Selection-125",
            "population": "OUT",
            "selection_query_count": SELECTION_COUNT,
            "parent_query_count": PARENT_COUNT,
            "train_query_count": TRAIN_COUNT,
            "final_query_count": FINAL_COUNT,
            "parent_split_sha256": split["split_sha256"],
            "protected_split_file_sha256": file_sha256(split_path),
            "source_queries_sha256": file_sha256(queries_path),
            "evaluator_relations_sha256": file_sha256(relations_path),
            "selection_query_package_sha256": file_sha256(query_output),
            "selection_membership_sha256": canonical_sha256(sorted(selection_ids)),
            "split_algorithm": split["algorithm"],
            "split_seed": split["seed"],
            "protected_artifacts": [{
                "relative_path": "protected/selection-125-queries.jsonl",
                "sha256": file_sha256(query_output),
                "query_count": SELECTION_COUNT,
            }],
            "evaluator_handoff": "PENDING_PAIRED_OUT_VECTORS",
            "selection_accesses": 0,
            "final_accesses": 0,
            "protected_payload_included": False,
            "claim_boundary": "Input materialization only; no Selection exposure, ranking, or metric result.",
        }
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _write_json(destination / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json", receipt)
        scope_body = {
            "schema_version": "myis.armindex-a4-selection-scope.v1",
            "scope": "Selection-125",
            "population": "OUT",
            "query_count": SELECTION_COUNT,
            "parent_split_sha256": split["split_sha256"],
            "receipt_sha256": receipt["receipt_sha256"],
            "selection_accesses": 0,
            "final_accesses": 0,
        }
        _write_json(destination / "A4_SELECTION_SCOPE.json", {**scope_body, "scope_sha256": canonical_sha256(scope_body)})
        return receipt
    except Exception:
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        raise


def validate_selection_input_materialization(root: Path, *, expected_attempt_id: str) -> dict[str, Any]:
    """Validate the aggregate-safe receipt and protected query package."""

    package = _directory(root, "Selection input materialization")
    receipt = _load_object(package / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json", "Selection receipt")
    if receipt.get("status") != "PASS_A4_SELECTION_INPUT_MATERIALIZED" or receipt.get("attempt_id") != expected_attempt_id:
        raise A4SelectionMaterializerError("Selection receipt identity is invalid")
    _self_hash(receipt, "receipt_sha256", "Selection receipt")
    if receipt.get("scope") != "Selection-125" or receipt.get("population") != "OUT" or receipt.get("selection_query_count") != SELECTION_COUNT:
        raise A4SelectionMaterializerError("Selection receipt scope is invalid")
    if receipt.get("selection_accesses") != 0 or receipt.get("final_accesses") != 0:
        raise A4SelectionMaterializerError("Selection input validation cannot open a scientific counter")
    artifacts = receipt.get("protected_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 1 or not isinstance(artifacts[0], Mapping):
        raise A4SelectionMaterializerError("Selection protected artifact declaration is invalid")
    relative = artifacts[0].get("relative_path")
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise A4SelectionMaterializerError("Selection protected artifact path is invalid")
    query_file = (package / relative).resolve(strict=True)
    if not query_file.is_relative_to(package) or query_file.is_symlink() or artifacts[0].get("sha256") != file_sha256(query_file):
        raise A4SelectionMaterializerError("Selection protected artifact hash drift")
    rows = _load_jsonl(query_file)
    if len(rows) != SELECTION_COUNT or any(set(row) != {"work_token", "text"} for row in rows):
        raise A4SelectionMaterializerError("Selection protected query package coverage is invalid")
    return receipt


def _validate_split(split: Mapping[str, Any], expected_hash: str) -> tuple[list[str], set[str]]:
    if split.get("schema_version") != "myis.protected-split.v1":
        raise A4SelectionMaterializerError("unsupported protected split schema")
    if split.get("split_sha256") != expected_hash:
        raise A4SelectionMaterializerError("parent split commitment mismatch")
    if split.get("algorithm") != SPLIT_ALGORITHM or split.get("seed") != SPLIT_SEED:
        raise A4SelectionMaterializerError("parent split algorithm or seed drift")
    groups = {key: split.get(key) for key in ("train", "selection", "final")}
    if any(not isinstance(value, list) for value in groups.values()):
        raise A4SelectionMaterializerError("parent split groups are malformed")
    if [len(groups["train"]), len(groups["selection"]), len(groups["final"])] != [TRAIN_COUNT, SELECTION_COUNT, FINAL_COUNT]:
        raise A4SelectionMaterializerError("parent split counts are not 250/125/872")
    all_ids = [item for value in groups.values() for item in value]
    if any(not isinstance(item, str) or not item for item in all_ids) or len(set(all_ids)) != PARENT_COUNT:
        raise A4SelectionMaterializerError("parent split IDs are malformed or overlapping")
    return list(groups["selection"]), set(all_ids)


def _load_query_rows(path: Path) -> dict[str, dict[str, Any]]:
    if path.suffix.casefold() == ".arrow":
        rows = list(iter_arrow_rows((path,), ("query_id", "title_en", "abstract_en", "claims_text")))
    else:
        rows = _load_jsonl(path)
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        source_id = row.get("query_id", row.get("source_id"))
        if not isinstance(source_id, str) or not source_id or source_id in result:
            raise A4SelectionMaterializerError("canonical query source IDs are missing or duplicated")
        if path.suffix.casefold() != ".arrow":
            text = row.get("text")
            if not isinstance(text, str) or not text.strip():
                raise A4SelectionMaterializerError("canonical query text is missing")
        result[source_id] = row
    if len(result) != PARENT_COUNT:
        raise A4SelectionMaterializerError(f"canonical query payload must contain {PARENT_COUNT} unique rows")
    return result


def _row_text(row: Mapping[str, Any]) -> str:
    if "text" in row:
        text = row.get("text")
        if isinstance(text, str) and text.strip():
            return text
    try:
        text = _query_text(row, token="Q-placeholder")
    except Exception as error:  # pragma: no cover - defensive source-shape guard
        raise A4SelectionMaterializerError("canonical query text cannot be materialized") from error
    if not isinstance(text, str) or not text.strip():
        raise A4SelectionMaterializerError("canonical query text is empty")
    return text


def _opaque_work_token(source_id: str) -> str:
    digest = hashlib.sha256(f"{A3_TRAIN250_OPAQUE_SCOPE}:Q:{source_id}".encode("utf-8")).hexdigest()
    return f"Q-{digest[:32]}"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise A4SelectionMaterializerError(f"JSONL row is not an object: {path.name}")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _load_object(path: Path, role: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise A4SelectionMaterializerError(f"{role} must be a JSON object")
    return value


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    digest = value.get(field)
    if not isinstance(digest, str) or digest != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4SelectionMaterializerError(f"{role} self-hash is invalid")


def _regular_file(path: Path, role: str) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise A4SelectionMaterializerError(f"{role} must be a regular file")
    return resolved


def _directory(path: Path, role: str) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_dir() or resolved.is_symlink():
        raise A4SelectionMaterializerError(f"{role} must be a real directory")
    return resolved


def _fresh_output(path: Path, store: Path) -> Path:
    resolved = path.resolve()
    if resolved == store or not resolved.is_relative_to(store):
        raise A4SelectionMaterializerError("output must be a child of Owner Store")
    if resolved.exists():
        raise A4SelectionMaterializerError("output attempt root already exists")
    return resolved


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")
