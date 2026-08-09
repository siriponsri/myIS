"""Owner-local bridge for one hash-bound A1.2 v16 common-screen attempt.

The bridge is deliberately narrow: it reads only paths committed by an
Owner-local materializer manifest, invokes the v16 ``execute_program_cell``
callback, and writes aggregate-safe cell receipts.  It never evaluates qrels,
maps opaque identities, or emits ranking rows.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_measured_executor_v16 import (
    DenseEmbeddingAdapter,
    FamilyRank,
    LogicalInput,
    PhysicalInput,
    execute_program_cell_batch,
)
from .a1_2_raw_materializer_bridge_v16 import (
    RawMaterializerBridgeV16Error,
    materialize_raw_corpus,
    materialize_raw_query,
)

ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
ORIGINAL_PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
EXECUTABLE_PROGRAM_IDS = {
    **{program: program for program in ORIGINAL_PROGRAM_IDS if program != "P02-CLAIM1"},
    "P02-CLAIM1": "P02-FIRST-CLAIM",
}
CELL_IDS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in ORIGINAL_PROGRAM_IDS)
TOKEN_RE = re.compile(r"^[FQ]-[a-f0-9]{32}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
MANIFEST_SCHEMA = "myis.armindex-a1.2-owner-local-measured-input-manifest.v16"
RECEIPT_SCHEMA = "myis.armindex-a1.2-owner-local-cell-receipt.v16"
SUMMARY_SCHEMA = "myis.armindex-a1.2-owner-local-screen-receipt.v16"
GATE_NAMES = (
    "provider_admission",
    "execution_adoption",
    "watchdog_ttl",
    "protected_boundary",
    "frozen_bindings",
)


class OwnerLocalMeasuredRunnerV16Error(ValueError):
    """Raised for any manifest, callback, or completion mismatch."""


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} must be a JSON object")
    return value


def _hash(value: Any, *, role: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} hash is invalid")
    return value


def _safe_file(root: Path, relative: Any, *, role: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} path is invalid")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} path must be relative")
    candidate = root / path
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except OSError as error:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is missing") from error
    if candidate.is_symlink() or not resolved.is_relative_to(root) or metadata.st_mode & 0o170000 != 0o100000:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is unsafe")
    return resolved


def _atomic(path: Path, value: Mapping[str, Any]) -> None:
    text = _json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != text:
            raise OwnerLocalMeasuredRunnerV16Error("immutable receipt already differs")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != value:
            raise OwnerLocalMeasuredRunnerV16Error("immutable text artifact already differs")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_jsonl(path: Path, *, role: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for line in handle:
                if not line.strip():
                    raise OwnerLocalMeasuredRunnerV16Error(f"{role} contains an empty row")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise OwnerLocalMeasuredRunnerV16Error(f"{role} contains a non-object row")
                rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        if isinstance(error, OwnerLocalMeasuredRunnerV16Error):
            raise
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is invalid JSONL") from error
    if not rows:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is empty")
    return rows


def _physical_inputs(row: Mapping[str, Any], *, role: str) -> tuple[PhysicalInput, ...]:
    values = row.get("physical_inputs")
    if values is None:
        text, count = row.get("text"), row.get("source_token_count", 1)
        values = [{"text": text, "source_token_count": count}]
    if not isinstance(values, list) or not values:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical plan is missing")
    parsed: list[PhysicalInput] = []
    for value in values:
        if not isinstance(value, Mapping) or set(value) != {"text", "source_token_count"}:
            raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical plan is invalid")
        text, count = value["text"], value["source_token_count"]
        if not isinstance(text, str) or not text or isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical input is invalid")
        parsed.append(PhysicalInput(text, count))
    return tuple(parsed)


def _logical(row: Mapping[str, Any], *, role: str, query: bool = False) -> LogicalInput:
    token_key = "work_token" if query else "family_token"
    token = row.get(token_key)
    if not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None or (query and not token.startswith("Q-")) or (not query and not token.startswith("F-")):
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} opaque token is invalid")
    logical_id = row.get("logical_id", row.get("unit_id", token))
    if not isinstance(logical_id, str) or not logical_id:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} logical identity is invalid")
    view = row.get("view_id")
    if view is not None and view not in {"title", "abstract", "claims"}:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} view is invalid")
    return LogicalInput(logical_id, token, view, _physical_inputs(row, role=role))


def _ranking_rows(rows: Sequence[Any]) -> tuple[str, tuple[str, ...]]:
    safe: list[dict[str, Any]] = []
    for item in rows:
        if isinstance(item, FamilyRank):
            family, rank, score = item.family_token, item.rank, item.score
        elif isinstance(item, Mapping) and set(item) == {"family_token", "rank", "score"}:
            family, rank, score = item["family_token"], item["rank"], item["score"]
        else:
            raise OwnerLocalMeasuredRunnerV16Error("executor returned an invalid rank row")
        if not isinstance(family, str) or not family.startswith("F-") or TOKEN_RE.fullmatch(family) is None:
            raise OwnerLocalMeasuredRunnerV16Error("executor returned a non-opaque family token")
        if not isinstance(rank, int) or rank < 1 or rank > 100 or not isinstance(score, (int, float)):
            raise OwnerLocalMeasuredRunnerV16Error("executor returned an invalid rank")
        safe.append({"family_token": family, "rank": rank, "score": float(score)})
    if len(safe) != 100 or [item["rank"] for item in safe] != list(range(1, 101)) or len({item["family_token"] for item in safe}) != 100:
        raise OwnerLocalMeasuredRunnerV16Error("executor must return exactly 100 unique ranked families")
    return canonical_sha256(safe), tuple(item["family_token"] for item in safe)


def _ranking_hash(rows: Sequence[Any]) -> str:
    return _ranking_rows(rows)[0]


def _validate_manifest(path: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = path.resolve(strict=True)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise OwnerLocalMeasuredRunnerV16Error("input manifest is unsafe")
    root = manifest_path.parent.resolve()
    manifest = _load_json(manifest_path, role="input manifest")
    observed = manifest.get("manifest_sha256")
    if observed != canonical_sha256({key: value for key, value in manifest.items() if key != "manifest_sha256"}):
        raise OwnerLocalMeasuredRunnerV16Error("input manifest self-hash mismatch")
    if manifest.get("schema_version") != MANIFEST_SCHEMA or manifest.get("status") != "READY":
        raise OwnerLocalMeasuredRunnerV16Error("input manifest is not READY v16")
    attempt_id = manifest.get("attempt_id")
    if not isinstance(attempt_id, str) or ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise OwnerLocalMeasuredRunnerV16Error("attempt identity is invalid")
    gates = manifest.get("gates")
    if not isinstance(gates, Mapping) or any(gates.get(name) != "PASS" for name in GATE_NAMES):
        raise OwnerLocalMeasuredRunnerV16Error("provider/adoption gates are not PASS")
    cells = manifest.get("cells")
    if not isinstance(cells, list) or len(cells) != 25:
        raise OwnerLocalMeasuredRunnerV16Error("manifest must bind exactly 25 cells")
    observed_cells: set[str] = set()
    for cell in cells:
        if not isinstance(cell, Mapping):
            raise OwnerLocalMeasuredRunnerV16Error("cell binding is invalid")
        required = {"cell_id", "arm_id", "program_id", "executable_program_id", "binding_path", "binding_sha256", "corpus_path", "corpus_sha256", "query_path", "query_sha256"}
        if set(cell) != required:
            raise OwnerLocalMeasuredRunnerV16Error("cell binding fields are invalid")
        cell_id = cell["cell_id"]
        if cell_id not in CELL_IDS or cell_id != f"{cell['arm_id']}--{cell['program_id']}" or cell_id in observed_cells or cell["arm_id"] not in ARM_IDS or cell["program_id"] not in ORIGINAL_PROGRAM_IDS:
            raise OwnerLocalMeasuredRunnerV16Error("cell topology is invalid")
        if cell["executable_program_id"] != EXECUTABLE_PROGRAM_IDS[cell["program_id"]]:
            raise OwnerLocalMeasuredRunnerV16Error("program ID bridge is invalid")
        for key in ("binding_sha256", "corpus_sha256", "query_sha256"):
            _hash(cell[key], role=key)
        for key in ("binding_path", "corpus_path", "query_path"):
            target = _safe_file(root, cell[key], role=key)
            if file_sha256(target) != cell[key.replace("_path", "_sha256")]:
                raise OwnerLocalMeasuredRunnerV16Error(f"{key} hash mismatch")
        observed_cells.add(cell_id)
    if observed_cells != set(CELL_IDS):
        raise OwnerLocalMeasuredRunnerV16Error("manifest cell set is incomplete")
    work = manifest.get("work_tokens")
    if not isinstance(work, Mapping) or set(work) != {"path", "sha256", "count"} or work["count"] != 150:
        raise OwnerLocalMeasuredRunnerV16Error("manifest work-token commitment is invalid")
    _hash(work["sha256"], role="work-token")
    work_path = _safe_file(root, work["path"], role="work-token")
    if file_sha256(work_path) != work["sha256"]:
        raise OwnerLocalMeasuredRunnerV16Error("work-token hash mismatch")
    return root, manifest


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    """Validate and return only aggregate-safe manifest facts."""

    _root, manifest = _validate_manifest(manifest_path)
    return {"status": "PASS", "attempt_id": manifest["attempt_id"], "cells": 25, "work_token_count": 150, "top_k": 100, "manifest_sha256": manifest["manifest_sha256"]}


def run_owner_local_measured_screen(
    manifest_path: Path,
    *,
    output_root: Path,
    adapters: Mapping[str, DenseEmbeddingAdapter] | None = None,
    batch_executor: Callable[..., Mapping[str, Sequence[Any]]] = execute_program_cell_batch,
    arm_ids: Sequence[str] = ARM_IDS,
) -> dict[str, Any]:
    """Run the selected complete arm set and emit aggregate-safe receipts."""

    root, manifest = _validate_manifest(manifest_path)
    selected_arms = tuple(arm_ids)
    if (
        not selected_arms
        or len(selected_arms) != len(set(selected_arms))
        or any(arm not in ARM_IDS for arm in selected_arms)
    ):
        raise OwnerLocalMeasuredRunnerV16Error("selected arm set is invalid")
    output = output_root.resolve()
    if output.is_relative_to(Path.cwd().resolve()):
        raise OwnerLocalMeasuredRunnerV16Error("receipt output must remain outside the repository")
    work_path = _safe_file(root, manifest["work_tokens"]["path"], role="work-token")
    work_rows = _read_jsonl(work_path, role="work-token input")
    if len(work_rows) != 150:
        raise OwnerLocalMeasuredRunnerV16Error("work-token input must contain exactly 150 rows")
    work_tokens: list[str] = []
    query_tokens: set[str] = set()
    for row in work_rows:
        token = row.get("work_token")
        if not isinstance(token, str) or not token.startswith("Q-") or TOKEN_RE.fullmatch(token) is None or token in query_tokens:
            raise OwnerLocalMeasuredRunnerV16Error("work-token input domain is invalid")
        work_tokens.append(token)
        query_tokens.add(token)
    if len(work_tokens) != 150:
        raise OwnerLocalMeasuredRunnerV16Error("work-token set is incomplete")
    token_set_hash = canonical_sha256({"work_tokens": sorted(work_tokens)})
    cell_receipts: list[dict[str, Any]] = []
    attempt_root = output / manifest["attempt_id"]
    if attempt_root.exists() and (attempt_root.is_symlink() or not attempt_root.is_dir()):
        raise OwnerLocalMeasuredRunnerV16Error("receipt attempt root is unsafe")
    receipts_root = attempt_root / "receipts"
    rankings_root = attempt_root / "rankings"
    for cell in manifest["cells"]:
        if cell["arm_id"] not in selected_arms:
            continue
        existing_receipt_path = receipts_root / f"{cell['cell_id']}.json"
        existing_ranking_path = rankings_root / f"{cell['cell_id']}.jsonl"
        if existing_receipt_path.exists() or existing_ranking_path.exists():
            if not existing_receipt_path.is_file() or not existing_ranking_path.is_file():
                raise OwnerLocalMeasuredRunnerV16Error("partial cell artifacts are inconsistent")
            existing = _load_json(existing_receipt_path, role="existing cell receipt")
            existing_body = {key: value for key, value in existing.items() if key != "receipt_sha256"}
            if (
                existing.get("schema_version") != RECEIPT_SCHEMA
                or existing.get("attempt_id") != manifest["attempt_id"]
                or existing.get("cell_id") != cell["cell_id"]
                or existing.get("arm_id") != cell["arm_id"]
                or existing.get("program_id") != cell["program_id"]
                or existing.get("executable_program_id") != cell["executable_program_id"]
                or existing.get("binding_sha256") != cell["binding_sha256"]
                or existing.get("status") != "PASS"
                or existing.get("aggregate_safe") is not True
                or existing.get("work_token_count") != 150
                or existing.get("returned_row_count") != 150
                or existing.get("top_k") != 100
                or existing.get("ranking_path") != f"rankings/{cell['cell_id']}.jsonl"
                or existing.get("receipt_sha256") != canonical_sha256(existing_body)
                or file_sha256(existing_ranking_path) != existing.get("ranking_file_sha256")
            ):
                raise OwnerLocalMeasuredRunnerV16Error("existing cell artifact is incompatible with manifest")
            ranking_rows = _read_jsonl(existing_ranking_path, role="existing ranking")
            observed_tokens: set[str] = set()
            for row in ranking_rows:
                if set(row) != {"work_token", "family_tokens"}:
                    raise OwnerLocalMeasuredRunnerV16Error("existing ranking row is invalid")
                token, families = row["work_token"], row["family_tokens"]
                if token not in query_tokens or token in observed_tokens or not isinstance(families, list) or len(families) != 100 or len(set(families)) != 100 or any(not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None or not value.startswith("F-") for value in families):
                    raise OwnerLocalMeasuredRunnerV16Error("existing ranking coverage is invalid")
                observed_tokens.add(token)
            if observed_tokens != query_tokens:
                raise OwnerLocalMeasuredRunnerV16Error("existing ranking query coverage is incomplete")
            cell_receipts.append(existing)
            continue
        corpus_rows = _read_jsonl(_safe_file(root, cell["corpus_path"], role="compiled corpus"), role="compiled corpus")
        adapter = None if cell["arm_id"] == "ARM-01" else (adapters or {}).get(cell["arm_id"])
        raw_corpus = bool(corpus_rows and {"claims", "claims_text", "publication_token"}.issubset(corpus_rows[0]))
        try:
            if raw_corpus:
                corpus = materialize_raw_corpus(
                    corpus_rows,
                    arm_id=cell["arm_id"],
                    program_id=cell["executable_program_id"],
                    adapter=adapter,
                )
            else:
                corpus = tuple(_logical(row, role="compiled corpus") for row in corpus_rows)
        except RawMaterializerBridgeV16Error as error:
            raise OwnerLocalMeasuredRunnerV16Error("raw corpus materialization failed") from error
        query_path = _safe_file(root, cell["query_path"], role="compiled query")
        query_rows = _read_jsonl(query_path, role="compiled query")
        if len(query_rows) != 150 or {row.get("work_token") for row in query_rows} != query_tokens:
            raise OwnerLocalMeasuredRunnerV16Error("compiled query coverage is not exactly 150 opaque work tokens")
        query_by_token = {str(row["work_token"]): row for row in query_rows}
        batch_queries: dict[str, str | LogicalInput] = {}
        for token in work_tokens:
            row = query_by_token[token]
            try:
                if "physical_inputs" in row:
                    batch_queries[token] = _logical(row, role="compiled query", query=True)
                elif cell["arm_id"] == "ARM-01" or not raw_corpus:
                    text = row.get("text")
                    if not isinstance(text, str) or not text:
                        raise RawMaterializerBridgeV16Error("raw query text is invalid")
                    batch_queries[token] = text
                else:
                    batch_queries[token] = materialize_raw_query(
                        row, arm_id=cell["arm_id"], adapter=adapter
                    )
            except RawMaterializerBridgeV16Error as error:
                raise OwnerLocalMeasuredRunnerV16Error("raw query materialization failed") from error
        if cell["arm_id"] != "ARM-01" and adapter is None:
            raise OwnerLocalMeasuredRunnerV16Error("dense adapter is missing")
        rank_hashes: list[str] = []
        ranking_lines: list[str] = []
        rankings = batch_executor(arm_id=cell["arm_id"], program_id=cell["executable_program_id"], corpus=corpus, queries=batch_queries, adapter=adapter)
        if not isinstance(rankings, Mapping) or tuple(rankings) != tuple(work_tokens):
            raise OwnerLocalMeasuredRunnerV16Error("batch executor returned incomplete work-token results")
        for token in work_tokens:
            ranks = rankings[token]
            ranking_hash, family_tokens = _ranking_rows(ranks)
            rank_hashes.append(ranking_hash)
            ranking_lines.append(_json({"work_token": token, "family_tokens": list(family_tokens)}))
        ranking_text = "".join(ranking_lines)
        ranking_sha256 = hashlib.sha256(ranking_text.encode("ascii")).hexdigest()
        ranking_relative = f"rankings/{cell['cell_id']}.jsonl"
        attempt_root.mkdir(parents=True, exist_ok=True)
        _atomic_text(attempt_root / ranking_relative, ranking_text)
        body = {
            "schema_version": RECEIPT_SCHEMA,
            "receipt_id": f"{manifest['attempt_id']}--{cell['cell_id']}",
            "attempt_id": manifest["attempt_id"],
            "cell_id": cell["cell_id"],
            "arm_id": cell["arm_id"],
            "program_id": cell["program_id"],
            "executable_program_id": cell["executable_program_id"],
            "status": "PASS",
            "aggregate_safe": True,
            "work_token_count": 150,
            "returned_row_count": 150,
            "top_k": 100,
            "work_token_set_sha256": token_set_hash,
            "ranking_set_sha256": canonical_sha256(rank_hashes),
            "ranking_path": ranking_relative,
            "ranking_file_sha256": ranking_sha256,
            "binding_sha256": cell["binding_sha256"],
        }
        body["receipt_sha256"] = canonical_sha256(body)
        _atomic(receipts_root / f"{cell['cell_id']}.json", body)
        cell_receipts.append(body)
    summary_body = {
        "schema_version": SUMMARY_SCHEMA,
        "receipt_id": f"{manifest['attempt_id']}--screen",
        "attempt_id": manifest["attempt_id"],
        "status": "PASS",
        "aggregate_safe": True,
        "cell_count": len(cell_receipts),
        "work_token_count": 150,
        "top_k": 100,
        "manifest_sha256": manifest["manifest_sha256"],
        "cell_receipts_sha256": canonical_sha256([item["receipt_sha256"] for item in cell_receipts]),
    }
    summary = {**summary_body, "receipt_sha256": canonical_sha256(summary_body)}
    output.mkdir(parents=True, exist_ok=True)
    _atomic(receipts_root / "screen.json", summary)
    return {"status": "PASS", "attempt_id": manifest["attempt_id"], "cells": len(cell_receipts), "work_tokens": 150, "top_k": 100, "receipt_sha256": summary["receipt_sha256"], "output_relative": f"{manifest['attempt_id']}/receipts"}


def merge_measured_arm_outputs(
    manifest_path: Path,
    *,
    arm_output_roots: Mapping[str, Path],
    output_root: Path,
) -> dict[str, Any]:
    """Validate five complete arm outputs and merge the unchanged payloads."""

    _root, manifest = _validate_manifest(manifest_path)
    if set(arm_output_roots) != set(ARM_IDS):
        raise OwnerLocalMeasuredRunnerV16Error("merge requires all five arms")
    output = output_root.resolve()
    if output.is_relative_to(Path.cwd().resolve()):
        raise OwnerLocalMeasuredRunnerV16Error("merged output must remain outside the repository")
    attempt_id = manifest["attempt_id"]
    work_path = _safe_file(_root, manifest["work_tokens"]["path"], role="work-token")
    work_rows = _read_jsonl(work_path, role="work-token input")
    work_tokens = tuple(str(row.get("work_token")) for row in work_rows)
    if len(work_tokens) != 150 or len(set(work_tokens)) != 150 or any(TOKEN_RE.fullmatch(token) is None or not token.startswith("Q-") for token in work_tokens):
        raise OwnerLocalMeasuredRunnerV16Error("merge work-token set is invalid")
    expected_work = set(work_tokens)
    expected_work_hash = canonical_sha256({"work_tokens": sorted(expected_work)})
    manifest_cells = {cell["cell_id"]: cell for cell in manifest["cells"]}
    receipts: list[dict[str, Any]] = []
    sources: list[tuple[Path, str]] = []
    for arm in ARM_IDS:
        arm_root = Path(arm_output_roots[arm]).resolve(strict=True)
        if arm_root.is_symlink() or not arm_root.is_dir() or arm_root.is_relative_to(Path.cwd().resolve()):
            raise OwnerLocalMeasuredRunnerV16Error("arm output root is unsafe")
        attempt = arm_root / attempt_id
        summary = _load_json(attempt / "receipts" / "screen.json", role="arm screen receipt")
        summary_body = {key: value for key, value in summary.items() if key != "receipt_sha256"}
        if (
            summary.get("schema_version") != SUMMARY_SCHEMA
            or summary.get("status") != "PASS"
            or summary.get("aggregate_safe") is not True
            or summary.get("cell_count") != 5
            or summary.get("work_token_count") != 150
            or summary.get("top_k") != 100
            or summary.get("manifest_sha256") != manifest["manifest_sha256"]
            or summary.get("receipt_sha256") != canonical_sha256(summary_body)
        ):
            raise OwnerLocalMeasuredRunnerV16Error("arm screen receipt is invalid")
        for cell in (value for value in CELL_IDS if value.startswith(f"{arm}--")):
            receipt_path = attempt / "receipts" / f"{cell}.json"
            receipt = _load_json(receipt_path, role="arm cell receipt")
            binding = manifest_cells[cell]
            receipt_body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
            ranking_relative = f"rankings/{cell}.jsonl"
            ranking_path = attempt / ranking_relative
            if (
                receipt.get("schema_version") != RECEIPT_SCHEMA
                or receipt.get("attempt_id") != attempt_id
                or receipt.get("cell_id") != cell
                or receipt.get("arm_id") != arm
                or receipt.get("program_id") != binding["program_id"]
                or receipt.get("executable_program_id") != binding["executable_program_id"]
                or receipt.get("binding_sha256") != binding["binding_sha256"]
                or receipt.get("status") != "PASS"
                or receipt.get("aggregate_safe") is not True
                or receipt.get("work_token_count") != 150
                or receipt.get("returned_row_count") != 150
                or receipt.get("top_k") != 100
                or receipt.get("work_token_set_sha256") != expected_work_hash
                or receipt.get("ranking_path") != ranking_relative
                or receipt.get("receipt_sha256") != canonical_sha256(receipt_body)
                or not ranking_path.is_file()
                or ranking_path.is_symlink()
                or file_sha256(ranking_path) != receipt.get("ranking_file_sha256")
            ):
                raise OwnerLocalMeasuredRunnerV16Error("arm cell receipt is invalid")
            ranking_rows = _read_jsonl(ranking_path, role="arm ranking")
            observed_work: set[str] = set()
            for row in ranking_rows:
                if set(row) != {"work_token", "family_tokens"}:
                    raise OwnerLocalMeasuredRunnerV16Error("arm ranking row is invalid")
                token, families = row["work_token"], row["family_tokens"]
                if (
                    token not in expected_work
                    or token in observed_work
                    or not isinstance(families, list)
                    or len(families) != 100
                    or len(set(families)) != 100
                    or any(not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None or not value.startswith("F-") for value in families)
                ):
                    raise OwnerLocalMeasuredRunnerV16Error("arm ranking coverage is invalid")
                observed_work.add(token)
            if observed_work != expected_work:
                raise OwnerLocalMeasuredRunnerV16Error("arm ranking work-token set is incomplete")
            receipts.append(receipt)
            sources.extend(((ranking_path, ranking_relative), (receipt_path, f"receipts/{cell}.json")))
    ordered_receipts = sorted(receipts, key=lambda value: CELL_IDS.index(value["cell_id"]))
    if len(ordered_receipts) != 25:
        raise OwnerLocalMeasuredRunnerV16Error("merged cell set is not 25/25")
    summary_body = {
        "schema_version": SUMMARY_SCHEMA,
        "receipt_id": f"{attempt_id}--screen",
        "attempt_id": attempt_id,
        "status": "PASS",
        "aggregate_safe": True,
        "cell_count": 25,
        "work_token_count": 150,
        "top_k": 100,
        "manifest_sha256": manifest["manifest_sha256"],
        "cell_receipts_sha256": canonical_sha256([item["receipt_sha256"] for item in ordered_receipts]),
    }
    summary = {**summary_body, "receipt_sha256": canonical_sha256(summary_body)}
    attempt_root = output / attempt_id
    if attempt_root.exists():
        raise OwnerLocalMeasuredRunnerV16Error("merged output already exists")
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{attempt_id}.", dir=output))
    try:
        for source, relative in sources:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        _atomic(staging / "receipts" / "screen.json", summary)
        os.replace(staging, attempt_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"status": "PASS", "attempt_id": attempt_id, "cells": 25, "work_tokens": 150, "top_k": 100, "receipt_sha256": summary["receipt_sha256"]}


__all__ = ["OwnerLocalMeasuredRunnerV16Error", "merge_measured_arm_outputs", "run_owner_local_measured_screen", "validate_manifest"]
