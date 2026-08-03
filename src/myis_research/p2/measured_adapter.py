"""Owner-local DAPFAM measurement adapter for P2 SCOPE candidates."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping

from ..dapfam_p1 import (
    FTS_TOKENIZER,
    _FTSRanker,
    _OutcomeSink,
    _config_commitment,
    _corpus_commitment,
    _load_corpus_ids,
    _load_selected_queries,
    _load_selected_relations,
    _results_equivalent,
    _verify_index,
    derive_split,
    iter_arrow_rows,
    resolve_cache,
)
from ..kernel.canonical import canonical_sha256, file_sha256
from ..kernel.p1 import evaluate_baseline
from ..owner_local import validate_receipt
from ..scope import compile_scope
from .contracts import P2ContractError, write_immutable_json
from .measured_contracts import load_measured_request, validate_measured_artifact
from .measured_state import atomic_write_json


PRIOR_BASELINE_URI = Path(
    "campaigns/scope-autoindex-v1/evidence/"
    "dapfam-p1-fulltext-c058a3aa7357c782.receipt.json"
)
P2_RETRIEVAL_CONFIG = {
    "schema_version": "myis.p2-retrieval-config.v1",
    "scorer": "sqlite_fts5_bm25_v1",
    "query_operator": "OR",
    "top_k": 100,
    "fts_tokenizer": FTS_TOKENIZER,
    "lexical_tokenizer": "python-re-unicode-word-casefold-v1",
    "family_tie_policy": "lexical_family_then_unit",
}


class P2MeasurementAdapterError(P2ContractError):
    """Raised when the Owner-local DAPFAM adapter cannot produce safe evidence."""


def p2_retrieval_config_sha256() -> str:
    return canonical_sha256(P2_RETRIEVAL_CONFIG)


def current_scope_hashes(repository_root: Path) -> dict[str, str]:
    root = Path(repository_root).resolve()
    return {
        "compiler_sha256": file_sha256(root / "src/myis_research/scope/compiler.py"),
        "config_sha256": p2_retrieval_config_sha256(),
        "retriever_sha256": file_sha256(root / "src/myis_research/p2/measured_adapter.py"),
        "evaluator_sha256": file_sha256(root / "src/myis_research/kernel/p1.py"),
    }


def validate_owner_inputs(
    *,
    request: Mapping[str, Any],
    repository_root: Path,
    cache_root: Path,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    layout = resolve_cache(Path(cache_root), root, verify_hashes=True)
    dataset_lineage = canonical_sha256(layout.input_hashes)
    request_inputs = dict(request["input_hashes"])
    for key, value in layout.input_hashes.items():
        if request_inputs.get(key) != value:
            raise P2MeasurementAdapterError(
                f"measured request input hash is stale: {key}"
            )
    if request_inputs.get("dataset_lineage_sha256") != dataset_lineage:
        raise P2MeasurementAdapterError(
            "measured request dataset lineage is missing or stale"
        )
    expected_scope = current_scope_hashes(root)
    request_scope = dict(request["scope_hashes"])
    for key, value in expected_scope.items():
        if request_scope.get(key) != value:
            raise P2MeasurementAdapterError(
                f"measured request scope hash is stale: {key}"
            )
    return {
        "layout": layout,
        "dataset_lineage_sha256": dataset_lineage,
        "scope_hashes": expected_scope,
    }


def baseline_expectation(
    *,
    request: Mapping[str, Any],
    repository_root: Path,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    prior_path = root / PRIOR_BASELINE_URI
    try:
        prior = validate_receipt(json.loads(prior_path.read_text(encoding="utf-8")))
    except (OSError, ValueError, PermissionError, json.JSONDecodeError) as error:
        raise P2MeasurementAdapterError(
            "accepted P1 baseline receipt is missing or invalid"
        ) from error
    try:
        source = prior["metrics"][8]
        dataset_lineage = prior["lineage_hashes"]["dataset_sha256"]
        prior_evaluator = prior["lineage_hashes"]["evaluator_sha256"]
    except (KeyError, IndexError, TypeError) as error:
        raise P2MeasurementAdapterError(
            "accepted P1 baseline receipt lacks the frozen metric binding"
        ) from error
    scope_hashes = dict(request["scope_hashes"])
    if scope_hashes.get("evaluator_sha256") != prior_evaluator:
        raise P2MeasurementAdapterError(
            "P2 evaluator hash differs from the accepted P1 baseline"
        )
    metric = {
        "schema_version": "myis.p2-train-metric.v1",
        "candidate_id": "p2-control-r0-window-maxp",
        "arm": "R0-W",
        "metric_name": source["name"],
        "data_role": source["split"],
        "scope": source["scope"],
        "evidence_role": source["evidence_role"],
        "direction": "higher_is_better",
        "value": source["value"],
        "n": source["n"],
        "denominator": source["denominator"],
        "dataset_lineage_sha256": dataset_lineage,
        "config_sha256": scope_hashes["config_sha256"],
        "retriever_sha256": scope_hashes["retriever_sha256"],
        "evaluator_sha256": scope_hashes["evaluator_sha256"],
    }
    return {
        "prior_artifact_uri": PRIOR_BASELINE_URI.as_posix(),
        "prior_artifact_sha256": file_sha256(prior_path),
        "metric_locator": {"metrics_index": 8},
        "expected_metric": metric,
        "tolerance": 0.0,
    }


def measure_candidate(
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    data_role: str,
    repository_root: Path,
    cache_root: Path,
    run_root: Path,
) -> dict[str, Any]:
    if data_role not in {"train", "selection"}:
        raise P2MeasurementAdapterError("candidate data role must be train or selection")
    root = Path(repository_root).resolve()
    owner_run_root = Path(run_root).resolve()
    validated = validate_owner_inputs(
        request=request,
        repository_root=root,
        cache_root=cache_root,
    )
    layout = validated["layout"]
    started = time.perf_counter()
    index, built = _build_or_reuse_candidate_index(
        request=request,
        candidate=candidate,
        layout=layout,
        run_root=owner_run_root,
    )
    query_ids = [
        str(row["query_id"])
        for row in iter_arrow_rows(
            tuple(path for path in layout.files["queries"] if path.suffix == ".arrow"),
            ("query_id",),
        )
    ]
    split = derive_split(query_ids)
    corpus_ids = _load_corpus_ids(layout)
    queries = _load_selected_queries(layout, split)
    qrels, domains, _ = _load_selected_relations(layout, split, corpus_ids)
    lineage_hint = {
        "dataset_sha256": validated["dataset_lineage_sha256"],
        "corpus_sha256": _corpus_commitment(layout.input_hashes),
        "query_sha256": _config_commitment(layout.input_hashes, "queries"),
        "qrels_sha256": _config_commitment(layout.input_hashes, "relations"),
        "split_sha256": str(split["split_sha256"]),
        "index_sha256": index["index_sha256"],
        "evaluator_sha256": request["scope_hashes"]["evaluator_sha256"],
    }
    protected_path = _prepare_protected_outcome(
        owner_run_root, data_role=data_role, candidate_id=str(candidate["candidate_id"])
    )
    first_sink = _OutcomeSink(protected_path)
    with _FTSRanker(Path(index["index_path"]), limit=100) as ranker:
        first = evaluate_baseline(
            documents=[],
            queries=queries[data_role],
            qrels=qrels,
            arm_id="R0-W",
            top_k=100,
            window_size=512,
            qrel_domains=domains,
            split_name=data_role,
            ranker=ranker,
            lineage_hint=lineage_hint,
            protected_sink=first_sink,
            documents_are_windowed=True,
        )
    first_hash = first_sink.close()
    second_sink = _OutcomeSink(None)
    with _FTSRanker(Path(index["index_path"]), limit=100) as ranker:
        second = evaluate_baseline(
            documents=[],
            queries=queries[data_role],
            qrels=qrels,
            arm_id="R0-W",
            top_k=100,
            window_size=512,
            qrel_domains=domains,
            split_name=data_role,
            ranker=ranker,
            lineage_hint=lineage_hint,
            protected_sink=second_sink,
            documents_are_windowed=True,
        )
    second_hash = second_sink.close()
    if not _results_equivalent(first, second) or first_hash != second_hash:
        raise P2MeasurementAdapterError(
            f"candidate replay determinism failed: {candidate['candidate_id']}"
        )
    source_metric = next(
        row
        for row in first["metrics"]
        if row["scope"] == "OUT" and row["evidence_role"] == "primary"
    )
    if data_role == "train":
        metric: dict[str, Any] = {
            "schema_version": "myis.p2-train-metric.v1",
            "candidate_id": candidate["candidate_id"],
            "arm": candidate["arm"],
            "metric_name": source_metric["name"],
            "data_role": "train",
            "scope": "OUT",
            "evidence_role": "primary",
            "direction": "higher_is_better",
            "value": source_metric["value"],
            "n": source_metric["n"],
            "denominator": source_metric["denominator"],
            "dataset_lineage_sha256": validated["dataset_lineage_sha256"],
            "config_sha256": request["scope_hashes"]["config_sha256"],
            "retriever_sha256": request["scope_hashes"]["retriever_sha256"],
            "evaluator_sha256": request["scope_hashes"]["evaluator_sha256"],
        }
    else:
        metric = {
            "candidate_id": candidate["candidate_id"],
            "name": source_metric["name"],
            "value": source_metric["value"],
            "n": source_metric["n"],
            "scope": source_metric["scope"],
            "split": source_metric["split"],
            "direction": source_metric["direction"],
            "denominator": source_metric["denominator"],
            "evidence_role": source_metric["evidence_role"],
        }
    result = {
        "schema_version": "myis.p2-candidate-result.v1",
        "request_id": request["request_id"],
        "candidate_id": candidate["candidate_id"],
        "arm": candidate["arm"],
        "candidate_class": candidate["candidate_class"],
        "iteration": int(candidate.get("iteration", 0)),
        "data_role": data_role,
        "spec_sha256": candidate["spec_sha256"],
        "index_sha256": index["index_sha256"],
        "index_lineage_sha256": index["index_lineage_sha256"],
        "index_build_count": 1 if built else 0,
        "deterministic_replay": True,
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "metric": metric,
    }
    result["result_sha256"] = canonical_sha256(result)
    return validate_measured_artifact(result, root)


def measure_candidate_to_file(
    *,
    request_path: Path,
    candidate_path: Path,
    data_role: str,
    repository_root: Path,
    cache_root: Path,
    run_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    request = load_measured_request(
        request_path,
        Path(repository_root).resolve(),
        require_current_git=True,
    )
    request = {key: value for key, value in request.items() if key != "_resolved"}
    candidate = _json_file(candidate_path)
    result = measure_candidate(
        request=request,
        candidate=candidate,
        data_role=data_role,
        repository_root=repository_root,
        cache_root=cache_root,
        run_root=run_root,
    )
    atomic_write_json(output_path, result)
    return result


def _build_or_reuse_candidate_index(
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    layout: Any,
    run_root: Path,
) -> tuple[dict[str, Any], bool]:
    candidate_id = str(candidate["candidate_id"])
    directory = Path(run_root) / "indexes" / candidate_id
    marker_path = directory / "COMPLETE.json"
    index_path = directory / "index.sqlite"
    lineage_body = {
        "schema_version": "myis.p2-index-lineage.v1",
        "request_id": request["request_id"],
        "candidate_id": candidate_id,
        "spec_sha256": candidate["spec_sha256"],
        "input_hashes": dict(sorted(layout.input_hashes.items())),
        "retrieval": deepcopy(candidate["retrieval"]),
        "config_sha256": request["scope_hashes"]["config_sha256"],
        "retriever_sha256": request["scope_hashes"]["retriever_sha256"],
    }
    lineage_sha256 = canonical_sha256(lineage_body)
    if marker_path.is_file():
        marker = _json_file(marker_path)
        if (
            marker.get("index_lineage_sha256") != lineage_sha256
            or marker.get("index_sha256") != file_sha256(index_path)
            or marker.get("candidate_id") != candidate_id
        ):
            raise P2MeasurementAdapterError("completed candidate index is stale")
        _verify_index(index_path, expected_rows=int(marker["rows"]))
        return {
            "index_path": str(index_path),
            "index_sha256": marker["index_sha256"],
            "index_lineage_sha256": lineage_sha256,
        }, False
    if directory.exists():
        raise P2MeasurementAdapterError("partial candidate index requires quarantine")
    directory.mkdir(parents=True)
    temporary = directory / "index.sqlite.tmp"
    connection = sqlite3.connect(temporary)
    rows = 0
    families: set[str] = set()
    batch: list[tuple[str, str, str]] = []
    try:
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA temp_store=FILE")
        connection.execute(
            f"CREATE VIRTUAL TABLE rows USING fts5(unit_id UNINDEXED, family_id UNINDEXED, text, tokenize='{FTS_TOKENIZER}')"
        )
        arrow = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
        for source in iter_arrow_rows(
            arrow, ("relevant_id", "title_en", "abstract_en", "claims_text")
        ):
            family_id = str(source["relevant_id"] or "")
            if not family_id or family_id in families:
                raise P2MeasurementAdapterError(
                    "DAPFAM corpus family IDs must be non-empty and unique"
                )
            families.add(family_id)
            record = {
                **source,
                "family_id": family_id,
                "publication_id": family_id,
            }
            compiled = compile_scope(candidate["scope_spec"], [record])
            searchable = [unit for unit in compiled.units if unit.searchable]
            if not searchable:
                raise P2MeasurementAdapterError(
                    f"candidate produced no searchable units: {candidate_id}"
                )
            for unit in searchable:
                batch.append((unit.unit_id, unit.family_id, unit.text))
                rows += 1
                if len(batch) >= 1000:
                    connection.executemany(
                        "INSERT INTO rows(unit_id, family_id, text) VALUES (?, ?, ?)",
                        batch,
                    )
                    batch.clear()
        if batch:
            connection.executemany(
                "INSERT INTO rows(unit_id, family_id, text) VALUES (?, ?, ?)", batch
            )
        if len(families) != int(layout.contract["configs"]["corpus"]["rows"]):
            raise P2MeasurementAdapterError("DAPFAM corpus cardinality drifted")
        connection.execute("INSERT INTO rows(rows) VALUES ('optimize')")
        connection.commit()
    finally:
        connection.close()
    temporary.replace(index_path)
    index_sha256 = file_sha256(index_path)
    _verify_index(index_path, expected_rows=rows)
    marker = {
        "schema_version": "myis.p2-index-complete.v1",
        "request_id": request["request_id"],
        "candidate_id": candidate_id,
        "spec_sha256": candidate["spec_sha256"],
        "index_sha256": index_sha256,
        "index_lineage_sha256": lineage_sha256,
        "rows": rows,
        "families": len(families),
    }
    marker["marker_sha256"] = canonical_sha256(marker)
    write_immutable_json(marker_path, marker)
    return {
        "index_path": str(index_path),
        "index_sha256": index_sha256,
        "index_lineage_sha256": lineage_sha256,
    }, True


def _prepare_protected_outcome(
    run_root: Path, *, data_role: str, candidate_id: str
) -> Path:
    path = Path(run_root) / "protected" / f"{data_role}-{candidate_id}-rankings.jsonl"
    if not path.exists():
        return path
    quarantine = Path(run_root) / "quarantine" / "protected"
    quarantine.mkdir(parents=True, exist_ok=True)
    os.replace(path, quarantine / f"{path.name}-{time.time_ns()}")
    return path


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise P2MeasurementAdapterError(f"cannot read Owner-local JSON: {path}") from error
    if not isinstance(value, dict):
        raise P2MeasurementAdapterError(f"Owner-local JSON must be an object: {path}")
    return value
