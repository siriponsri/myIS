"""Owner-local production engine for one frozen A2 representation program.

This module is deliberately invoked only by :mod:`a2_measured_adapter`.  It
opens the committed Owner-local corpus, query, qrels, and membership files in
that subprocess, retains all per-query material in memory, and emits one
aggregate-only candidate result.  The A2 program compiler is separate because
the A1 v16 common-program runner deliberately accepts only its five historical
program IDs; the model runtime, token-window materialization, ranking depth,
and evaluation rules remain the frozen A1 v16 ones.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

import numpy as np

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_measured_executor_v16 import (
    DENSE_ARM_IDS,
    SentenceTransformerDenseAdapter,
    build_dense_index,
    encode_logical_inputs,
)
from .a1_2_raw_materializer_bridge_v16 import _physical_texts, materialize_raw_query
from .a1_2_owner_local_evaluator_v16 import _quality as _a1_v16_quality
from .a2_measured_adapter import (
    A2MeasuredAdapterError,
    frozen_program_for_candidate,
    validate_owner_local_input,
)
from .a2_program_runtime import A2ProgramRuntimeError, aggregate_family_scores, compile_program
from .bm25s_adapter import BM25sAdapter

_HASH = re.compile(r"^[a-f0-9]{64}$")
_TOKEN = re.compile(r"^[FQ]-[a-f0-9]{32}$")
_RESULT_SCHEMA = "myis.armindex-a2-external-candidate-result.v1"


class A2OwnerLocalEngineError(ValueError):
    """Raised without exposing an Owner-local protected payload."""


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2OwnerLocalEngineError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A2OwnerLocalEngineError(f"{role} is invalid")
    return value


def _safe_file(root: Path, relative: object, *, role: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise A2OwnerLocalEngineError(f"{role} path is unsafe")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except OSError as error:
        raise A2OwnerLocalEngineError(f"{role} is unavailable") from error
    if candidate.is_symlink() or not resolved.is_file() or not resolved.is_relative_to(root) or metadata.st_mode & 0o170000 != 0o100000:
        raise A2OwnerLocalEngineError(f"{role} path is unsafe")
    return resolved


def _jsonl(path: Path, *, role: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                raise A2OwnerLocalEngineError(f"{role} is invalid")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise A2OwnerLocalEngineError(f"{role} is invalid")
            rows.append(row)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2OwnerLocalEngineError(f"{role} is invalid") from error
    if not rows:
        raise A2OwnerLocalEngineError(f"{role} is empty")
    return rows


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise A2OwnerLocalEngineError(f"{role} hash is invalid")
    return value


def _decimal(value: float) -> str:
    if not math.isfinite(value) or value < 0:
        raise A2OwnerLocalEngineError("aggregate measurement is invalid")
    return format(value, ".16g")


def _artifact_path(
    owner_root: Path, manifest: Mapping[str, Any], name: str
) -> Path:
    item = manifest["owner_artifacts"][name]
    path = _safe_file(owner_root, item["path"], role=f"{name} artifact")
    if file_sha256(path) != item["sha256"]:
        raise A2OwnerLocalEngineError(f"{name} artifact hash drift")
    return path


def _load_program(path: Path, *, candidate_id: str, arm_id: str, program_sha256: str) -> dict[str, Any]:
    program = _load_json(path, role="frozen program")
    body = {key: value for key, value in program.items() if key != "program_sha256"}
    if (
        program.get("program_id") != candidate_id
        or program.get("arm_id") != arm_id
        or program.get("program_sha256") != program_sha256
        or canonical_sha256(body) != program_sha256
    ):
        raise A2OwnerLocalEngineError("frozen program identity drift")
    return program


def _corpus_rows(path: Path, program: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = set(program["source_fields"])
    rows = _jsonl(path, role="corpus")
    result: list[dict[str, Any]] = []
    for row in rows:
        if not {"family_token", "publication_token"}.issubset(row) or not fields.issubset(row):
            raise A2OwnerLocalEngineError("corpus contract is incomplete")
        family, publication = row["family_token"], row["publication_token"]
        if not isinstance(family, str) or _TOKEN.fullmatch(family) is None or not family.startswith("F-") or not isinstance(publication, str) or not publication:
            raise A2OwnerLocalEngineError("corpus identity is invalid")
        if any(not isinstance(row[field], str) for field in fields):
            raise A2OwnerLocalEngineError("corpus field is invalid")
        result.append({key: row[key] for key in {"family_token", "publication_token", *fields}})
    return result


def _queries(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _jsonl(path, role="queries"):
        if set(row) != {"work_token", "text"}:
            raise A2OwnerLocalEngineError("query contract is invalid")
        token, text = row["work_token"], row["text"]
        if not isinstance(token, str) or _TOKEN.fullmatch(token) is None or not token.startswith("Q-") or not isinstance(text, str) or not text or token in result:
            raise A2OwnerLocalEngineError("query contract is invalid")
        result[token] = text
    return result


def _evaluation_inputs(qrels_path: Path, membership_path: Path, tokens: set[str]) -> tuple[dict[str, dict[str, int]], set[str]]:
    qrels: dict[str, dict[str, int]] = {}
    for row in _jsonl(qrels_path, role="qrels"):
        if set(row) != {"work_token", "relevance"} or not isinstance(row["work_token"], str) or row["work_token"] not in tokens or row["work_token"] in qrels or not isinstance(row["relevance"], dict) or not row["relevance"]:
            raise A2OwnerLocalEngineError("qrels contract is invalid")
        parsed: dict[str, int] = {}
        for family, grade in row["relevance"].items():
            if not isinstance(family, str) or _TOKEN.fullmatch(family) is None or not family.startswith("F-") or isinstance(grade, bool) or not isinstance(grade, int) or grade < 1:
                raise A2OwnerLocalEngineError("qrels contract is invalid")
            parsed[family] = grade
        qrels[row["work_token"]] = parsed
    eligible: set[str] = set()
    seen: set[str] = set()
    for row in _jsonl(membership_path, role="membership"):
        if set(row) != {"work_token", "eligible_out"} or not isinstance(row["work_token"], str) or row["work_token"] not in tokens or row["work_token"] in seen or not isinstance(row["eligible_out"], bool):
            raise A2OwnerLocalEngineError("membership contract is invalid")
        seen.add(row["work_token"])
        if row["eligible_out"]:
            eligible.add(row["work_token"])
    if set(qrels) != tokens or seen != tokens or not eligible:
        raise A2OwnerLocalEngineError("evaluation coverage is incomplete")
    return qrels, eligible


def _rank_arm01(units: Sequence[Any], queries: Mapping[str, str], method: str) -> dict[str, tuple[Any, ...]]:
    documents = [{"doc_id": unit.logical_id, "family_id": unit.family_token, "text": unit.physical_inputs[0].text} for unit in units]
    index = BM25sAdapter().build_index(documents)
    by_id = {unit.logical_id: unit for unit in units}
    result: dict[str, tuple[Any, ...]] = {}
    for token, query in queries.items():
        rows = BM25sAdapter().search(index, query)
        ranked_units = [by_id[row[0]] for row in rows]
        result[token] = aggregate_family_scores(ranked_units, [row[2] for row in rows], method=method)
    return result


def _dense_units(compiled: Sequence[Any], *, arm_id: str, adapter: Any) -> tuple[Any, ...]:
    result = []
    for unit in compiled:
        physical = _physical_texts(arm_id=arm_id, text=unit.physical_inputs[0].text, adapter=adapter)
        result.append(type(unit)(unit.logical_id, unit.family_token, unit.view_id, physical))
    return tuple(result)


def _rank_dense(units: Sequence[Any], queries: Mapping[str, str], *, arm_id: str, model_directory: Path, method: str, adapter_factory: Callable[..., Any]) -> dict[str, tuple[Any, ...]]:
    adapter = adapter_factory(arm_id=arm_id, model_directory=model_directory, device="cuda:0", batch_size=1)
    materialized = _dense_units(units, arm_id=arm_id, adapter=adapter)
    index = build_dense_index(arm_id=arm_id, adapter=adapter, corpus=materialized)
    result: dict[str, tuple[Any, ...]] = {}
    for token, text in queries.items():
        query = materialize_raw_query({"work_token": token, "text": text}, arm_id=arm_id, adapter=adapter)
        vector = encode_logical_inputs(arm_id=arm_id, adapter=adapter, logical_inputs=(query,))[0]
        result[token] = aggregate_family_scores(index.logical_units, np.matmul(index.vectors, vector), method=method)
    return result


def _metrics(rankings: Mapping[str, Sequence[Any]], qrels: Mapping[str, Mapping[str, int]], eligible: set[str]) -> tuple[float, float, float]:
    evaluated: dict[str, list[str]] = {}
    for token in sorted(eligible):
        ranks = rankings.get(token)
        if ranks is None or len(ranks) != 100 or [row.rank for row in ranks] != list(range(1, 101)) or len({row.family_token for row in ranks}) != 100:
            raise A2OwnerLocalEngineError("top-100 ranking coverage is incomplete")
        evaluated[token] = [row.family_token for row in ranks]
    # Keep the A1 v16 Owner-local evaluator's aggregation and cutoff semantics.
    value = _a1_v16_quality(evaluated, qrels, eligible)
    return (
        float(value["recall_at_100_out"]),
        float(value["ndcg_at_100_out"]),
        float(value["ndcg_at_10_out"]),
    )


def run_owner_local_engine(
    repository_root: Path,
    *,
    owner_root: Path,
    manifest_relative_path: str,
    program_path: Path,
    candidate_id: str,
    arm_id: str,
    program_sha256: str,
    adapter_factory: Callable[..., Any] = SentenceTransformerDenseAdapter.from_staged_directory,
) -> dict[str, Any]:
    """Execute one A2 candidate and return its aggregate-safe external result."""

    root = repository_root.resolve()
    owner = owner_root.resolve(strict=True)
    try:
        manifest = validate_owner_local_input(root, owner_root=owner, manifest_relative_path=manifest_relative_path)
    except A2MeasuredAdapterError as error:
        raise A2OwnerLocalEngineError("Owner-local input contract is invalid") from error
    if manifest["engine"]["code_sha256"] != file_sha256(Path(__file__)):
        raise A2OwnerLocalEngineError("production engine code binding drift")
    program = _load_program(program_path.resolve(strict=True), candidate_id=candidate_id, arm_id=arm_id, program_sha256=program_sha256)
    try:
        expected_program = frozen_program_for_candidate(root, candidate_id)
    except A2MeasuredAdapterError as error:
        raise A2OwnerLocalEngineError("frozen candidate program is unavailable") from error
    if program != expected_program:
        raise A2OwnerLocalEngineError("frozen candidate program bytes drift")
    corpus = _corpus_rows(_artifact_path(owner, manifest, "corpus"), program)
    queries = _queries(_artifact_path(owner, manifest, "queries"))
    qrels, eligible = _evaluation_inputs(_artifact_path(owner, manifest, "qrels"), _artifact_path(owner, manifest, "membership"), set(queries))
    try:
        compiled = compile_program(corpus, program)
    except A2ProgramRuntimeError as error:
        raise A2OwnerLocalEngineError("frozen A2 program compilation failed") from error
    started = time.perf_counter()
    if arm_id == "ARM-01":
        rankings = _rank_arm01(compiled.units, queries, compiled.family_aggregation)
    elif arm_id in DENSE_ARM_IDS:
        model_directory = owner / manifest["engine"]["model_directories"][arm_id]
        rankings = _rank_dense(compiled.units, queries, arm_id=arm_id, model_directory=model_directory, method=compiled.family_aggregation, adapter_factory=adapter_factory)
    else:
        raise A2OwnerLocalEngineError("frozen arm identity is invalid")
    wall_seconds = time.perf_counter() - started
    primary, ndcg100, ndcg10 = _metrics(rankings, qrels, eligible)
    ranking_commitment = canonical_sha256({token: [{"family_token": row.family_token, "rank": row.rank, "score": float(row.score)} for row in rows] for token, rows in rankings.items()})
    evaluator_input = canonical_sha256({"qrels_sha256": manifest["owner_artifacts"]["qrels"]["sha256"], "membership_sha256": manifest["owner_artifacts"]["membership"]["sha256"], "ranking_sha256": ranking_commitment})
    result = {
        "schema_version": _RESULT_SCHEMA,
        "attempt_id": manifest["attempt_id"],
        "candidate_id": candidate_id,
        "arm_id": arm_id,
        "program_sha256": program_sha256,
        "executor_output_sha256": ranking_commitment,
        "evaluator_input_sha256": evaluator_input,
        "evaluator_sha256": manifest["owner_artifacts"]["evaluator"]["binding_sha256"],
        "code_sha256": manifest["engine"]["code_sha256"],
        "model_sha256": manifest["owner_artifacts"]["model_lockset"]["binding_sha256"],
        "data_sha256": manifest["owner_artifacts"]["data_handoff"]["binding_sha256"],
        "primary_metric": {"name": "recall_at_100/out", "value": _decimal(primary)},
        "secondary_metrics": {"ndcg_at_100/out": _decimal(ndcg100), "ndcg_at_10/out": _decimal(ndcg10)},
        "latency": {
            "wall_seconds": _decimal(wall_seconds),
            "search_p95_seconds": _decimal(wall_seconds / len(queries)),
        },
        "cost": {"charged_usd": "0", "currency": "USD"},
        "coverage": {"expected_units": len(queries), "completed_units": len(rankings)},
        "resume_count": 0,
        "failure_count": 0,
        "reserve_activation_passed": False,
        "reserve_activation_evidence_sha256": None,
        "train_only": True,
        "rep_dev_measured": False,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    assert_aggregate_only(result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a2-owner-local-engine")
    parser.add_argument("program_path", type=Path)
    parser.add_argument("--repository-root", type=Path, default=os.environ.get("MYIS_A2_REPOSITORY_ROOT"))
    parser.add_argument("--owner-root", type=Path, default=os.environ.get("MYIS_A2_OWNER_ROOT"))
    parser.add_argument("--input-manifest", default=os.environ.get("MYIS_A2_OWNER_INPUT_MANIFEST"))
    args = parser.parse_args(argv)
    try:
        if args.repository_root is None or args.owner_root is None or not args.input_manifest:
            raise A2OwnerLocalEngineError("Owner-local engine context is unavailable")
        result = run_owner_local_engine(
            args.repository_root,
            owner_root=args.owner_root,
            manifest_relative_path=args.input_manifest,
            program_path=args.program_path,
            candidate_id=os.environ.get("MYIS_A2_CANDIDATE_ID", ""),
            arm_id=os.environ.get("MYIS_A2_ARM_ID", ""),
            program_sha256=os.environ.get("MYIS_A2_PROGRAM_SHA256", ""),
        )
    except (A2OwnerLocalEngineError, OSError, ValueError):
        print('{"status":"FAILED_CLOSED"}')
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["A2OwnerLocalEngineError", "run_owner_local_engine"]
