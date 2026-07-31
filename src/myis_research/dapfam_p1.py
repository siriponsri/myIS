"""Pinned, offline DAPFAM full-text execution for the P1 CPU baseline."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from jsonschema import Draft202012Validator

from .kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .kernel.manifest import build_manifest, manifest_round_trip
from .kernel.manifest_validation import (
    ManifestValidationError,
    build_validation_report,
    capture_git_state,
    validate_validation_report,
)
from .kernel.p1 import evaluate_baseline, tokenize
from .owner_local import (
    OwnerLocalContractError,
    build_receipt,
    canonical_json_bytes,
    validate_receipt,
    validate_request,
)


SOURCE_CONTRACT = Path("control/assets/dapfam-p1-source.v1.json")
SOURCE_SCHEMA = Path("schemas/dapfam-p1-source.v1.json")
INDEX_SCHEMA = "myis.p1-dapfam-index.v1"
PACKAGE_SCHEMA = "myis.p1-package.v1"
REQUEST_PREFIX = "dapfam-p1-fulltext"
FTS_TOKENIZER = "unicode61 remove_diacritics 2"
EXPECTED_SLOTS = (("R0", "train"), ("R0", "selection"), ("R0-W", "train"), ("R0-W", "selection"))


@dataclass(frozen=True)
class CacheLayout:
    root: Path
    contract: dict[str, Any]
    files: dict[str, tuple[Path, ...]]
    input_hashes: dict[str, str]


@dataclass(frozen=True)
class IndexArtifact:
    arm: str
    path: Path
    sha256: str
    rows: int
    families: int
    lineage_sha256: str


class DapfamP1Error(OwnerLocalContractError):
    """Raised when the pinned P1 DAPFAM contract cannot be satisfied."""


def load_source_contract(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    contract_path = root / SOURCE_CONTRACT
    schema_path = root / SOURCE_SCHEMA
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(contract)
    except Exception as error:
        raise DapfamP1Error("DAPFAM source contract is missing or invalid") from error
    if contract["protocol"]["split"] != {
        "seed": 42,
        "algorithm": "sha256-seed-colon-id-lexical-v1",
        "train": 250,
        "selection": 125,
        "final": 872,
    }:
        raise DapfamP1Error("DAPFAM split contract drifted")
    if contract["protocol"]["retrieval"].get("query_operator") != "OR":
        raise DapfamP1Error("DAPFAM retrieval contract must use OR semantics")
    return contract


def resolve_cache(cache_root: Path, repository_root: Path, *, verify_hashes: bool = True) -> CacheLayout:
    root = cache_root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise DapfamP1Error("DAPFAM cache root must be a regular directory")
    contract = load_source_contract(repository_root)
    revision = str(contract["dataset"]["revision"])
    resolved: dict[str, tuple[Path, ...]] = {}
    input_hashes: dict[str, str] = {}
    for config_name in ("corpus", "queries", "relations"):
        config = contract["configs"][config_name]
        directory = root / config_name / "0.0.0" / revision
        paths: list[Path] = []
        for index, entry in enumerate(config["files"]):
            path = (directory / str(entry["name"])).resolve()
            try:
                path.relative_to(root)
            except ValueError as error:
                raise DapfamP1Error("DAPFAM cache contract escaped its root") from error
            if path.is_symlink() or not path.is_file() or path.stat().st_size != int(entry["bytes"]):
                raise DapfamP1Error(f"DAPFAM cache file is missing or has wrong size: {config_name}/{entry['name']}")
            if verify_hashes and file_sha256(path) != str(entry["sha256"]):
                raise DapfamP1Error(f"DAPFAM cache SHA-256 drift: {config_name}/{entry['name']}")
            paths.append(path)
            input_hashes[f"{config_name}_{index:03d}_sha256"] = str(entry["sha256"])
        resolved[config_name] = tuple(paths)
    return CacheLayout(root=root, contract=contract, files=resolved, input_hashes=dict(sorted(input_hashes.items())))


def iter_arrow_rows(paths: Sequence[Path], fields: Sequence[str]) -> Iterator[dict[str, Any]]:
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
    except ImportError as error:
        raise DapfamP1Error("PyArrow is required; sync the p1 extra from uv.lock") from error
    for path in paths:
        if path.suffix != ".arrow":
            continue
        with pa.memory_map(str(path), "r") as source:
            try:
                reader = ipc.open_stream(source)
            except pa.ArrowInvalid as error:
                raise DapfamP1Error(f"DAPFAM Arrow stream is invalid: {path.name}") from error
            names = set(reader.schema.names)
            missing = set(fields) - names
            if missing:
                raise DapfamP1Error(f"DAPFAM Arrow fields are missing in {path.name}: {sorted(missing)}")
            for batch in reader:
                columns = [batch.column(batch.schema.get_field_index(field)).to_pylist() for field in fields]
                for values in zip(*columns, strict=True):
                    yield dict(zip(fields, values, strict=True))


def compose_tac(row: Mapping[str, Any]) -> str:
    parts = [str(row[field]).strip() for field in ("title_en", "abstract_en", "claims_text") if row.get(field) is not None and str(row[field]).strip()]
    return "\n\n".join(parts)


def derive_split(query_ids: Iterable[str]) -> dict[str, Any]:
    ids = [str(value) for value in query_ids]
    if len(ids) != 1247 or len(set(ids)) != 1247 or any(not value for value in ids):
        raise DapfamP1Error("DAPFAM query IDs must contain exactly 1,247 unique non-empty values")
    ordered = sorted(ids, key=lambda value: (hashlib.sha256(f"42:{value}".encode("utf-8")).hexdigest(), value))
    body: dict[str, Any] = {
        "schema_version": "myis.protected-split.v1",
        "seed": 42,
        "algorithm": "sha256-seed-colon-id-lexical-v1",
        "train": ordered[:250],
        "selection": ordered[250:375],
        "final": ordered[375:],
    }
    body["split_sha256"] = canonical_sha256(body)
    return body


def build_request(cache_root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], CacheLayout]:
    root = repository_root.resolve()
    git = capture_git_state(root)
    if git["tracked_worktree_state"] != "clean":
        raise DapfamP1Error("tracked worktree must be clean before creating a measured request")
    layout = resolve_cache(cache_root, root)
    query_arrow = tuple(path for path in layout.files["queries"] if path.suffix == ".arrow")
    query_ids = [str(row["query_id"]) for row in iter_arrow_rows(query_arrow, ("query_id",))]
    split = derive_split(query_ids)
    scope = _request_scope(root, split_sha256=str(split["split_sha256"]))
    identity = {
        "git_commit": git["commit"],
        "scope": scope,
        "input_hashes": layout.input_hashes,
    }
    request_id = f"{REQUEST_PREFIX}-{canonical_sha256(identity)[:16]}"
    request = validate_request({
        "schema_version": "myis.owner-local-request.v2",
        "request_id": request_id,
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE",
        "phase_id": "P1_CPU_BASELINE",
        "stage": "train_selection",
        "scope": scope,
        "git_commit": git["commit"],
        "input_hashes": layout.input_hashes,
    })
    return request, split, layout


def prepare_request(cache_root: Path, repository_root: Path, evidence_root: Path) -> tuple[Path, Path]:
    root = repository_root.resolve()
    evidence = _external_root(evidence_root, root, cache_root.resolve(), label="P1 evidence store")
    request, split, _ = build_request(cache_root, root)
    request_dir = evidence / request["request_id"]
    request_path = request_dir / "request.json"
    split_path = request_dir / "protected" / "split-membership.json"
    _write_new_or_identical_json(split_path, split)
    _write_new_or_identical_json(request_path, request)
    return request_path, split_path


def assert_request_current(request: Mapping[str, Any], cache_root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], CacheLayout]:
    validated = validate_request(request)
    expected, split, layout = build_request(cache_root, repository_root)
    if validated != expected:
        raise DapfamP1Error("owner-local request does not match the current Git, source, protocol, or split commitments")
    return validated, split, layout


def _request_scope(repository_root: Path, *, split_sha256: str) -> dict[str, str]:
    root = repository_root.resolve()
    paths = {
        "campaign_sha256": root / "control/campaigns/scope-autoindex-v1.yaml",
        "envelope_sha256": root / "control/execution-envelope.yaml",
        "source_contract_sha256": root / SOURCE_CONTRACT,
        "source_schema_sha256": root / SOURCE_SCHEMA,
        "adapter_code_sha256": root / "src/myis_research/dapfam_p1.py",
        "cli_code_sha256": root / "src/myis_research/dapfam_p1_cli.py",
        "evaluator_code_sha256": root / "src/myis_research/kernel/p1.py",
        "request_schema_sha256": root / "control/owner-local/request.schema.json",
        "receipt_schema_sha256": root / "control/owner-local/receipt.schema.json",
    }
    scope = {key: file_sha256(path) for key, path in paths.items()}
    scope["split_membership_sha256"] = split_sha256
    return dict(sorted(scope.items()))


def _external_root(path: Path, repository_root: Path, cache_root: Path, *, label: str) -> Path:
    resolved = path.resolve()
    for forbidden in (repository_root.resolve(), cache_root.resolve()):
        if _is_within(resolved, forbidden):
            raise DapfamP1Error(f"{label} must be outside Git and the read-only DAPFAM cache")
    resolved.mkdir(parents=True, exist_ok=True)
    if resolved.is_symlink() or not resolved.is_dir():
        raise DapfamP1Error(f"{label} must be a regular directory")
    return resolved


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _write_new_or_identical_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (canonical_json(payload) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != encoded:
            raise DapfamP1Error(f"immutable artifact already exists with different bytes: {path}")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def run_p1(
    request_path: Path,
    cache_root: Path,
    repository_root: Path,
    index_root: Path,
    evidence_root: Path,
) -> Path:
    """Execute the protected train/selection baseline and emit one aggregate receipt."""

    root = repository_root.resolve()
    request_file = request_path.resolve(strict=True)
    if request_file.is_symlink() or not request_file.is_file():
        raise DapfamP1Error("request must be a regular file")
    request_payload = json.loads(request_file.read_text(encoding="utf-8"))
    request, split, layout = assert_request_current(request_payload, cache_root, root)
    indexes = _external_root(index_root, root, cache_root.resolve(), label="P1 index store")
    evidence = _external_root(evidence_root, root, cache_root.resolve(), label="P1 evidence store")
    run_dir = _allocate_generation(evidence / request["request_id"] / "runs")
    started = time.perf_counter()

    corpus_ids = _load_corpus_ids(layout)
    queries = _load_selected_queries(layout, split)
    qrels, domains, relation_counts = _load_selected_relations(layout, split, corpus_ids)
    artifacts = _build_or_reuse_indexes(layout, indexes, request)

    metrics: list[dict[str, Any]] = []
    aggregate_hashes: dict[str, str] = {
        f"input_{key}": value for key, value in request["input_hashes"].items()
    }
    for arm, split_name in EXPECTED_SLOTS:
        artifact = artifacts[arm]
        outcome_path = run_dir / "protected" / f"{arm.lower()}-{split_name}-rankings.jsonl"
        subset = queries[split_name]
        lineage_hint = {
            "dataset_sha256": canonical_sha256(request["input_hashes"]),
            "corpus_sha256": _corpus_commitment(request["input_hashes"]),
            "query_sha256": _config_commitment(request["input_hashes"], "queries"),
            "qrels_sha256": _config_commitment(request["input_hashes"], "relations"),
            "split_sha256": str(split["split_sha256"]),
            "index_sha256": artifact.sha256,
            "evaluator_sha256": request["scope"]["evaluator_code_sha256"],
        }
        first_sink = _OutcomeSink(outcome_path)
        with _FTSRanker(artifact.path, limit=100) as ranker:
            first = evaluate_baseline(
                documents=[],
                queries=subset,
                qrels=qrels,
                arm_id=arm,
                top_k=100,
                window_size=512,
                qrel_domains=domains,
                split_name=split_name,
                ranker=ranker,
                lineage_hint=lineage_hint,
                protected_sink=first_sink,
                documents_are_windowed=arm == "R0-W",
            )
        first_outcome_hash = first_sink.close()
        second_sink = _OutcomeSink(None)
        with _FTSRanker(artifact.path, limit=100) as ranker:
            second = evaluate_baseline(
                documents=[],
                queries=subset,
                qrels=qrels,
                arm_id=arm,
                top_k=100,
                window_size=512,
                qrel_domains=domains,
                split_name=split_name,
                ranker=ranker,
                lineage_hint=lineage_hint,
                protected_sink=second_sink,
                documents_are_windowed=arm == "R0-W",
            )
        second_outcome_hash = second_sink.close()
        if not _results_equivalent(first, second) or first_outcome_hash != second_outcome_hash:
            raise DapfamP1Error(f"determinism mismatch for {arm}/{split_name}")
        metrics.extend({**row, "arm": arm} for row in first["metrics"])
        key = arm.lower()
        aggregate_hashes[f"{key}_{split_name}_metrics"] = str(first["metrics_hash"])
        aggregate_hashes[f"{key}_{split_name}_rankings_sha256"] = first_outcome_hash

    for arm, artifact in artifacts.items():
        aggregate_hashes[f"{arm.lower()}_index"] = artifact.sha256
        aggregate_hashes[f"{arm.lower()}_index_lineage"] = artifact.lineage_sha256

    # Detect source mutation during a long index build before accepting evidence.
    post_layout = resolve_cache(cache_root, root, verify_hashes=True)
    if post_layout.input_hashes != request["input_hashes"]:
        raise DapfamP1Error("DAPFAM cache changed during execution")

    aggregate_counts = {
        "families": len(corpus_ids),
        "r0_documents": artifacts["R0"].rows,
        "r0w_windows": artifacts["R0-W"].rows,
        "queries": 1247,
        "train_queries": len(queries["train"]),
        "selection_queries": len(queries["selection"]),
        "final_queries": len(split["final"]),
        "positive_relations": relation_counts["IN"] + relation_counts["OUT"],
        "positive_in_relations": relation_counts["IN"],
        "positive_out_relations": relation_counts["OUT"],
    }
    lineage = {
        "dataset_sha256": canonical_sha256(request["input_hashes"]),
        "corpus_sha256": _corpus_commitment(request["input_hashes"]),
        "query_sha256": _config_commitment(request["input_hashes"], "queries"),
        "qrels_sha256": _config_commitment(request["input_hashes"], "relations"),
        "split_sha256": str(split["split_sha256"]),
        "index_sha256": canonical_sha256({arm: artifact.sha256 for arm, artifact in sorted(artifacts.items())}),
        "evaluator_sha256": request["scope"]["evaluator_code_sha256"],
    }
    receipt = build_receipt(
        request,
        aggregate_counts=aggregate_counts,
        aggregate_hashes=aggregate_hashes,
        metrics=metrics,
        cost_usd=0.0,
        latency_seconds=time.perf_counter() - started,
        lineage_hashes=lineage,
        historical_exposure={
            "paper_a": "historically_exposed",
            "paper_b": "historically_exposed",
            "paper_d": "historically_exposed",
            "paper_d_test_997": "historically_exposed",
            "active_final_872_global_untouched": "not_claimable",
        },
        status="accepted",
    )
    receipt_path = run_dir / "receipt.json"
    _write_new_or_identical_json(receipt_path, receipt)
    return receipt_path


def _load_corpus_ids(layout: CacheLayout) -> set[str]:
    arrow = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
    ids: set[str] = set()
    rows = 0
    for row in iter_arrow_rows(arrow, ("relevant_id",)):
        family = str(row["relevant_id"] or "")
        if not family or family in ids:
            raise DapfamP1Error("DAPFAM corpus family IDs must be non-empty and unique")
        ids.add(family)
        rows += 1
    if rows != int(layout.contract["configs"]["corpus"]["rows"]):
        raise DapfamP1Error("DAPFAM corpus row count drifted")
    return ids


def _load_selected_queries(layout: CacheLayout, split: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    membership = {
        query_id: role
        for role in ("train", "selection")
        for query_id in split[role]
    }
    output: dict[str, list[dict[str, str]]] = {"train": [], "selection": []}
    seen: set[str] = set()
    arrow = tuple(path for path in layout.files["queries"] if path.suffix == ".arrow")
    for row in iter_arrow_rows(arrow, ("query_id", "title_en", "abstract_en", "claims_text")):
        query_id = str(row["query_id"] or "")
        role = membership.get(query_id)
        if role is None:
            continue
        if query_id in seen:
            raise DapfamP1Error("DAPFAM selected query IDs are duplicated")
        text = compose_tac(row)
        if not text:
            raise DapfamP1Error("DAPFAM selected TAC query is empty")
        seen.add(query_id)
        output[role].append({"query_id": query_id, "text": text, "split": role})
    for role, expected in (("train", 250), ("selection", 125)):
        output[role].sort(key=lambda row: str(row["query_id"]))
        if len(output[role]) != expected:
            raise DapfamP1Error(f"DAPFAM {role} query cardinality drifted")
    return output


def _load_selected_relations(
    layout: CacheLayout,
    split: Mapping[str, Any],
    corpus_ids: set[str],
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]], dict[str, int]]:
    selected = set(split["train"]) | set(split["selection"])
    qrels: dict[str, set[str]] = {}
    domains: dict[str, dict[str, str]] = {}
    counts = {"IN": 0, "OUT": 0}
    rows = 0
    arrow = tuple(path for path in layout.files["relations"] if path.suffix == ".arrow")
    for row in iter_arrow_rows(arrow, ("query_id", "relevant_id", "relevance_score", "domain_rel")):
        rows += 1
        score = float(row["relevance_score"] or 0.0)
        if score <= 0:
            continue
        query_id = str(row["query_id"] or "")
        family_id = str(row["relevant_id"] or "")
        domain = str(row["domain_rel"] or "").upper()
        if domain not in {"IN", "OUT"}:
            raise DapfamP1Error("positive DAPFAM relation has invalid IN/OUT label")
        if family_id not in corpus_ids:
            raise DapfamP1Error("positive DAPFAM relation references an unknown family")
        counts[domain] += 1
        if query_id not in selected:
            continue
        qrels.setdefault(query_id, set()).add(family_id)
        previous = domains.setdefault(query_id, {}).setdefault(family_id, domain)
        if previous != domain:
            raise DapfamP1Error("DAPFAM relation assigns conflicting domains to one query-family pair")
    expected = layout.contract["configs"]["relations"]
    if rows != int(expected["rows"]) or counts != {key: int(value) for key, value in expected["positive_rows"].items()}:
        raise DapfamP1Error("DAPFAM relation counts drifted from the pinned contract")
    return qrels, domains, counts


def _config_commitment(hashes: Mapping[str, str], prefix: str) -> str:
    return canonical_sha256({key: value for key, value in sorted(hashes.items()) if key.startswith(f"{prefix}_")})


def _corpus_commitment(hashes: Mapping[str, str]) -> str:
    return _config_commitment(hashes, "corpus")


def _allocate_generation(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for generation in range(10000):
        candidate = root / f"g{generation:04d}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise DapfamP1Error("P1 evidence generation limit reached")


def _build_or_reuse_indexes(
    layout: CacheLayout,
    index_root: Path,
    request: Mapping[str, Any],
) -> dict[str, IndexArtifact]:
    configs = {
        arm: {
            "schema_version": INDEX_SCHEMA,
            "arm": arm,
            "dataset_id": layout.contract["dataset"]["dataset_id"],
            "dataset_revision": layout.contract["dataset"]["revision"],
            "source_contract_sha256": request["scope"]["source_contract_sha256"],
            "source_hashes_sha256": canonical_sha256(request["input_hashes"]),
            "parser_revision": "dapfam-arrow-tac-v1",
            "view": layout.contract["protocol"]["corpus_view"],
            "retrieval": layout.contract["protocol"]["retrieval"],
            "arm_contract": layout.contract["protocol"]["arms"][arm],
        }
        for arm in ("R0", "R0-W")
    }
    artifacts: dict[str, IndexArtifact] = {}
    pending: dict[str, tuple[Path, Path, Path, dict[str, Any]]] = {}
    for arm, config in configs.items():
        lineage = canonical_sha256(config)
        base = index_root / arm.lower()
        base.mkdir(parents=True, exist_ok=True)
        for generation in range(1000):
            suffix = "" if generation == 0 else f"-g{generation:04d}"
            directory = base / f"{lineage[:16]}{suffix}"
            index_path = directory / "index.sqlite"
            manifest_path = directory / "lineage.json"
            if directory.exists():
                try:
                    artifacts[arm] = _reuse_index(arm, index_path, manifest_path, config, lineage)
                    break
                except DapfamP1Error:
                    continue
            try:
                directory.mkdir()
            except FileExistsError:
                continue
            pending[arm] = (directory, index_path, manifest_path, config)
            break
        else:
            raise DapfamP1Error(f"index generation limit reached for {arm}")

    if pending:
        built = _stream_build_indexes(layout, pending)
        artifacts.update(built)
    if set(artifacts) != {"R0", "R0-W"}:
        raise DapfamP1Error("both P1 indexes must be available")
    return artifacts


def _stream_build_indexes(
    layout: CacheLayout,
    pending: Mapping[str, tuple[Path, Path, Path, dict[str, Any]]],
) -> dict[str, IndexArtifact]:
    connections: dict[str, sqlite3.Connection] = {}
    temp_paths: dict[str, Path] = {}
    batches: dict[str, list[tuple[str, str, str]]] = {arm: [] for arm in pending}
    counts = {arm: 0 for arm in pending}
    families: set[str] = set()
    try:
        for arm, (directory, _, _, _) in pending.items():
            temp_path = directory / "index.sqlite.tmp"
            if temp_path.exists():
                raise DapfamP1Error("partial index generation exists and will not be overwritten")
            connection = sqlite3.connect(temp_path)
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA temp_store=FILE")
            connection.execute(
                f"CREATE VIRTUAL TABLE rows USING fts5(unit_id UNINDEXED, family_id UNINDEXED, text, tokenize='{FTS_TOKENIZER}')"
            )
            connections[arm] = connection
            temp_paths[arm] = temp_path

        arrow = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
        for row in iter_arrow_rows(arrow, ("relevant_id", "title_en", "abstract_en", "claims_text")):
            family_id = str(row["relevant_id"] or "")
            if not family_id or family_id in families:
                raise DapfamP1Error("DAPFAM corpus family IDs must be non-empty and unique")
            families.add(family_id)
            tac = compose_tac(row)
            if not tac:
                raise DapfamP1Error("DAPFAM full TAC corpus row is empty")
            if "R0" in pending:
                batches["R0"].append((f"{family_id}#d000000", family_id, tac))
                counts["R0"] += 1
                _flush_batch(connections["R0"], batches["R0"])
            if "R0-W" in pending:
                tokens = tokenize(tac)
                if not tokens:
                    raise DapfamP1Error("DAPFAM full TAC corpus row has no lexical tokens")
                for start in range(0, len(tokens), 512):
                    window = " ".join(tokens[start : start + 512])
                    unit_id = f"{family_id}#w{start // 512:06d}"
                    batches["R0-W"].append((unit_id, family_id, window))
                    counts["R0-W"] += 1
                    _flush_batch(connections["R0-W"], batches["R0-W"])
        if len(families) != int(layout.contract["configs"]["corpus"]["rows"]):
            raise DapfamP1Error("DAPFAM corpus cardinality drifted during index construction")
        for arm, connection in connections.items():
            if batches[arm]:
                connection.executemany("INSERT INTO rows(unit_id, family_id, text) VALUES (?, ?, ?)", batches[arm])
                batches[arm].clear()
            connection.execute("INSERT INTO rows(rows) VALUES ('optimize')")
            connection.commit()
    finally:
        for connection in connections.values():
            connection.close()

    artifacts: dict[str, IndexArtifact] = {}
    for arm, (_, index_path, manifest_path, config) in pending.items():
        temp_path = temp_paths[arm]
        sqlite_hash = file_sha256(temp_path)
        lineage = canonical_sha256(config)
        manifest: dict[str, Any] = {
            "schema_version": INDEX_SCHEMA,
            "lineage_sha256": lineage,
            "sqlite_sha256": sqlite_hash,
            "rows": counts[arm],
            "families": len(families),
            "config": config,
        }
        manifest["manifest_sha256"] = canonical_sha256(manifest)
        temp_manifest = manifest_path.with_suffix(".json.tmp")
        _write_new_or_identical_json(temp_manifest, manifest)
        if index_path.exists() or manifest_path.exists():
            raise DapfamP1Error("immutable index destination unexpectedly exists")
        temp_path.replace(index_path)
        temp_manifest.replace(manifest_path)
        _verify_index(index_path, expected_rows=counts[arm])
        artifacts[arm] = IndexArtifact(arm, index_path, sqlite_hash, counts[arm], len(families), lineage)
    return artifacts


def _flush_batch(connection: sqlite3.Connection, batch: list[tuple[str, str, str]]) -> None:
    if len(batch) < 1000:
        return
    connection.executemany("INSERT INTO rows(unit_id, family_id, text) VALUES (?, ?, ?)", batch)
    batch.clear()


def _reuse_index(
    arm: str,
    index_path: Path,
    manifest_path: Path,
    config: Mapping[str, Any],
    lineage: str,
) -> IndexArtifact:
    if index_path.is_symlink() or manifest_path.is_symlink() or not index_path.is_file() or not manifest_path.is_file():
        raise DapfamP1Error("existing index generation is incomplete")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DapfamP1Error("existing index lineage is unreadable") from error
    recorded_manifest_hash = manifest.get("manifest_sha256")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    actual_hash = file_sha256(index_path)
    if (
        manifest.get("schema_version") != INDEX_SCHEMA
        or manifest.get("lineage_sha256") != lineage
        or manifest.get("config") != dict(config)
        or manifest.get("sqlite_sha256") != actual_hash
        or recorded_manifest_hash != canonical_sha256(unsigned)
        or not isinstance(manifest.get("rows"), int)
        or not isinstance(manifest.get("families"), int)
    ):
        raise DapfamP1Error("existing index lineage is stale or corrupt")
    _verify_index(index_path, expected_rows=int(manifest["rows"]))
    return IndexArtifact(arm, index_path, actual_hash, int(manifest["rows"]), int(manifest["families"]), lineage)


def _verify_index(index_path: Path, *, expected_rows: int) -> None:
    try:
        connection = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise DapfamP1Error("SQLite index integrity check failed")
            if connection.execute("SELECT count(*) FROM rows").fetchone() != (expected_rows,):
                raise DapfamP1Error("SQLite index row count does not match its lineage")
        finally:
            connection.close()
    except sqlite3.DatabaseError as error:
        raise DapfamP1Error("SQLite index cannot be verified") from error


class _FTSRanker:
    def __init__(self, index_path: Path, *, limit: int) -> None:
        self.connection = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
        self.limit = limit

    def __enter__(self) -> Callable[[str], list[tuple[str, str, float]]]:
        return self.rank

    def __exit__(self, *_: object) -> None:
        self.connection.close()

    def rank(self, query: str) -> list[tuple[str, str, float]]:
        terms = tuple(sorted(set(tokenize(query))))
        if not terms:
            return []
        expression = " OR ".join(f'"{term}"' for term in terms)
        cursor = self.connection.execute(
            "SELECT unit_id, family_id, bm25(rows) AS score FROM rows "
            "WHERE rows MATCH ? ORDER BY score ASC, family_id COLLATE BINARY ASC, unit_id COLLATE BINARY ASC",
            (expression,),
        )
        seen: set[str] = set()
        ranked: list[tuple[str, str, float]] = []
        for unit_id, family_id, score in cursor:
            family = str(family_id)
            if family in seen:
                continue
            seen.add(family)
            ranked.append((str(unit_id), family, -float(score)))
            if len(ranked) == self.limit:
                break
        return ranked


class _OutcomeSink:
    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.digest = hashlib.sha256()
        self.handle = None
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise DapfamP1Error(f"protected outcome already exists: {path}")
            self.handle = path.open("xb")

    def __call__(self, row: dict[str, Any]) -> None:
        encoded = canonical_json_bytes(row) + b"\n"
        self.digest.update(encoded)
        if self.handle is not None:
            self.handle.write(encoded)

    def close(self) -> str:
        if self.handle is not None:
            self.handle.flush()
            os.fsync(self.handle.fileno())
            self.handle.close()
            self.handle = None
        return self.digest.hexdigest()


def _results_equivalent(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    fields = ("metrics", "metrics_hash", "input_commitment", "query_commitment", "ranking_commitment", "lineage", "retrieval")
    return all(first.get(field) == second.get(field) for field in fields)


def import_p1_package(request_path: Path, receipt_path: Path, repository_root: Path) -> dict[str, Any]:
    """Import one aggregate-safe P1 result as an immutable four-slot package."""

    root = repository_root.resolve()
    git = capture_git_state(root)
    if git["tracked_worktree_state"] != "clean":
        raise DapfamP1Error("tracked worktree must be clean before importing canonical P1 evidence")
    request = validate_request(json.loads(request_path.resolve(strict=True).read_text(encoding="utf-8")))
    receipt = validate_receipt(json.loads(receipt_path.resolve(strict=True).read_text(encoding="utf-8")))
    if receipt["status"] != "accepted" or receipt["blockers"]:
        raise DapfamP1Error("only an accepted blocker-free P1 receipt can be imported")
    if receipt["request_sha256"] != canonical_sha256(request) or receipt["request_id"] != request["request_id"]:
        raise DapfamP1Error("receipt is not bound to the supplied request")
    if request["git_commit"] != git["commit"]:
        raise DapfamP1Error("P1 evidence must be imported at its clean execution commit")
    split_hash = str(request["scope"].get("split_membership_sha256", ""))
    if request["scope"] != _request_scope(root, split_sha256=split_hash):
        raise DapfamP1Error("P1 request scope no longer matches its execution commit")
    contract = load_source_contract(root)
    expected_inputs = _contract_input_hashes(contract)
    if request["input_hashes"] != expected_inputs:
        raise DapfamP1Error("P1 request inputs do not match the pinned source contract")

    receipt_hash = str(receipt["receipt_sha256"])
    parent_run_id = f"p1-dapfam-fulltext-{receipt_hash[:12]}"
    manifests: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for arm, split_name in EXPECTED_SLOTS:
        metrics = [
            dict(row) for row in receipt["metrics"]
            if row.get("arm") == arm and row.get("split") == split_name
        ]
        if len(metrics) != 3:
            raise DapfamP1Error(f"receipt metric slot is incomplete: {arm}/{split_name}")
        arm_key = arm.lower()
        index_key = f"{arm_key}_index"
        ranking_key = f"{arm_key}_{split_name}_rankings_sha256"
        if index_key not in receipt["aggregate_hashes"] or ranking_key not in receipt["aggregate_hashes"]:
            raise DapfamP1Error(f"receipt artifact commitments are incomplete: {arm}/{split_name}")
        run_id = f"p1-{arm_key.replace('-', 'w')}-{split_name}-{receipt_hash[:12]}"
        manifest = build_manifest(
            run_id=run_id,
            parent_run_id=parent_run_id,
            experiment_id="myis-scope-autoindex-v1",
            campaign_id="scope-autoindex-v1",
            stage=split_name,
            status="valid",
            source={
                "dataset_id": contract["dataset"]["dataset_id"],
                "revision": contract["dataset"]["revision"],
                "license": contract["dataset"]["license"],
                "source_contract_sha256": request["scope"]["source_contract_sha256"],
            },
            data={
                "query_view": "tac",
                "corpus_view": "full_tac",
                "evaluation_unit": "family",
                "split": split_name,
                "split_membership_sha256": split_hash,
            },
            method={
                "arm_id": arm,
                "retriever": "sqlite_fts5_bm25_v1",
                "query_operator": "OR",
                "top_k": 100,
                "window_tokens": 512 if arm == "R0-W" else None,
                "window_stride": 512 if arm == "R0-W" else None,
                "family_aggregation": "maxP" if arm == "R0-W" else "family_first",
            },
            resources={
                "cpu_only": True,
                "gpu": False,
                "paid_api": False,
                "network_model_download": False,
                "cost_actual": 0.0,
                "latency_seconds_total": receipt["latency_seconds"],
                "index_store_external": True,
                "protected_evidence_store_external": True,
            },
            metrics=metrics,
            artifacts=[
                {
                    "artifact_id": f"{arm_key}-index",
                    "role": "derived_retrieval_index",
                    "uri": f"owner-local://p1/{request['request_id']}/{arm_key}/index",
                    "sha256": receipt["aggregate_hashes"][index_key],
                },
                {
                    "artifact_id": f"{arm_key}-{split_name}-rankings",
                    "role": "protected_ranking_outcomes",
                    "uri": f"owner-local://p1/{request['request_id']}/{arm_key}/{split_name}/rankings",
                    "sha256": receipt["aggregate_hashes"][ranking_key],
                },
            ],
            evidence_class="train_selection_measured",
            repository_root=root,
            owner_local_request=request,
            owner_local_receipt=receipt,
        )
        manifests.append(manifest)
        reports.append(build_validation_report(manifest, owner_local_request=request, owner_local_receipt=receipt))

    campaign_root = root / "campaigns/scope-autoindex-v1"
    request_target = campaign_root / "requests" / f"{request['request_id']}.json"
    receipt_target = campaign_root / "evidence" / f"{request['request_id']}.receipt.json"
    manifest_targets = [campaign_root / "manifests" / f"{manifest['run_id']}.json" for manifest in manifests]
    report_targets = [campaign_root / "validation-reports" / f"{manifest['run_id']}.json" for manifest in manifests]
    package_target = campaign_root / "packages" / f"{request['request_id']}.package.json"
    targets = [request_target, receipt_target, *report_targets, *manifest_targets, package_target]
    if any(path.exists() for path in targets):
        raise DapfamP1Error("canonical P1 import target already exists; immutable evidence cannot be overwritten")

    package: dict[str, Any] = {
        "schema_version": PACKAGE_SCHEMA,
        "package_id": request["request_id"],
        "status": "validated_structural",
        "source_commit": request["git_commit"],
        "request_uri": request_target.relative_to(root).as_posix(),
        "request_sha256": canonical_sha256(request),
        "receipt_uri": receipt_target.relative_to(root).as_posix(),
        "receipt_sha256": receipt_hash,
        "source_contract_sha256": request["scope"]["source_contract_sha256"],
        "slots": [
            {
                "arm": manifest["method"]["arm_id"],
                "split": manifest["stage"],
                "run_id": manifest["run_id"],
                "manifest_uri": manifest_target.relative_to(root).as_posix(),
                "manifest_sha256": manifest["manifest_sha256"],
                "validation_report_uri": report_target.relative_to(root).as_posix(),
                "validation_report_sha256": report["validation_report_sha256"],
            }
            for manifest, report, manifest_target, report_target in zip(
                manifests, reports, manifest_targets, report_targets, strict=True
            )
        ],
    }
    package["package_sha256"] = canonical_sha256(package)
    _validate_package_shape(package)

    _write_new_or_identical_json(request_target, request)
    _write_new_or_identical_json(receipt_target, receipt)
    for report_target, report in zip(report_targets, reports, strict=True):
        validate_validation_report(report)
        _write_new_or_identical_json(report_target, report)
    for manifest_target, manifest in zip(manifest_targets, manifests, strict=True):
        _write_new_or_identical_json(manifest_target, manifest)
    _write_new_or_identical_json(package_target, package)
    return {"package": package, "package_path": package_target, "manifests": manifests, "reports": reports}


def load_package(package_path: Path, repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    path = package_path.resolve(strict=True)
    try:
        path.relative_to((root / "campaigns/scope-autoindex-v1/packages").resolve())
    except ValueError as error:
        raise DapfamP1Error("P1 package must be in the canonical package directory") from error
    package = json.loads(path.read_text(encoding="utf-8"))
    _validate_package_shape(package)

    request_path = _resolve_package_artifact(root, package["request_uri"])
    receipt_path = _resolve_package_artifact(root, package["receipt_uri"])
    request = validate_request(json.loads(request_path.read_text(encoding="utf-8")))
    receipt = validate_receipt(json.loads(receipt_path.read_text(encoding="utf-8")))
    if (
        canonical_sha256(request) != package["request_sha256"]
        or receipt["receipt_sha256"] != package["receipt_sha256"]
        or receipt["request_sha256"] != package["request_sha256"]
        or request["git_commit"] != package["source_commit"]
        or request["scope"].get("source_contract_sha256") != package["source_contract_sha256"]
    ):
        raise DapfamP1Error("P1 package request/receipt binding failed")

    for slot in package["slots"]:
        manifest_path = _resolve_package_artifact(root, slot["manifest_uri"])
        report_path = _resolve_package_artifact(root, slot["validation_report_uri"])
        try:
            manifest = manifest_round_trip(json.loads(manifest_path.read_text(encoding="utf-8")))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            validate_validation_report(report)
        except (ManifestValidationError, json.JSONDecodeError, OSError) as error:
            raise DapfamP1Error(f"P1 package artifact is invalid: {slot['run_id']}") from error
        if (
            manifest["manifest_sha256"] != slot["manifest_sha256"]
            or report["validation_report_sha256"] != slot["validation_report_sha256"]
            or report["manifest_sha256"] != manifest["manifest_sha256"]
            or manifest["run_id"] != slot["run_id"]
            or manifest["method"].get("arm_id") != slot["arm"]
            or manifest["stage"] != slot["split"]
            or manifest["request_sha256"] != package["request_sha256"]
            or manifest["receipt_sha256"] != package["receipt_sha256"]
            or manifest["git"].get("commit") != package["source_commit"]
        ):
            raise DapfamP1Error(f"P1 package artifact binding failed: {slot['run_id']}")
    return package


def _resolve_package_artifact(root: Path, uri: str) -> Path:
    if not isinstance(uri, str) or not uri or "\\" in uri:
        raise DapfamP1Error("P1 package artifact URI is invalid")
    try:
        artifact = (root / uri).resolve(strict=True)
        artifact.relative_to(root)
    except (OSError, ValueError) as error:
        raise DapfamP1Error(f"P1 package artifact escapes the repository: {uri}") from error
    if artifact.is_symlink() or not artifact.is_file():
        raise DapfamP1Error(f"P1 package artifact is not a regular file: {uri}")
    return artifact


def _validate_package_shape(package: Mapping[str, Any]) -> None:
    expected_keys = {
        "schema_version", "package_id", "status", "source_commit", "request_uri", "request_sha256",
        "receipt_uri", "receipt_sha256", "source_contract_sha256", "slots", "package_sha256",
    }
    if set(package) != expected_keys or package.get("schema_version") != PACKAGE_SCHEMA or package.get("status") != "validated_structural":
        raise DapfamP1Error("P1 package shape is invalid")
    try:
        schema = json.loads((Path(__file__).resolve().parents[2] / "schemas/p1-package.v1.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(package)
    except Exception as error:
        raise DapfamP1Error("P1 package schema validation failed") from error
    unsigned = {key: value for key, value in package.items() if key != "package_sha256"}
    if package.get("package_sha256") != canonical_sha256(unsigned):
        raise DapfamP1Error("P1 package commitment is invalid")
    slots = package.get("slots")
    if not isinstance(slots, list) or len(slots) != 4:
        raise DapfamP1Error("P1 package must contain four slots")
    slot_keys = {
        "arm", "split", "run_id", "manifest_uri", "manifest_sha256",
        "validation_report_uri", "validation_report_sha256",
    }
    if any(not isinstance(slot, Mapping) or set(slot) != slot_keys for slot in slots):
        raise DapfamP1Error("P1 package slot shape is invalid")
    observed = {(slot.get("arm"), slot.get("split")) for slot in slots if isinstance(slot, Mapping)}
    if observed != set(EXPECTED_SLOTS):
        raise DapfamP1Error("P1 package slots are incomplete")


def _contract_input_hashes(contract: Mapping[str, Any]) -> dict[str, str]:
    return dict(sorted({
        f"{config_name}_{index:03d}_sha256": str(entry["sha256"])
        for config_name in ("corpus", "queries", "relations")
        for index, entry in enumerate(contract["configs"][config_name]["files"])
    }.items()))
