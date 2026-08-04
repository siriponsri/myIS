"""Owner-local P1 runner for canonical bundles and legacy DAPFAM discovery."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .kernel.canonical import canonical_sha256, file_sha256
from .kernel.integrity import run_integrity_preflight
from .kernel.p1 import evaluate_baseline, tokenize
from .legacy_dapfam import (
    assert_legacy_p1_request_current,
    build_input_hashes,
    discover_legacy,
    iter_jsonl,
    legacy_project_root,
    pick,
    text_value,
)
from .owner_local import OwnerLocalContractError, build_receipt, validate_request


_BUNDLE_FILES = ("documents.json", "queries.json", "qrels.json", "splits.json")
_FTS_TOKENIZER = "unicode61 remove_diacritics 2"
_FTS_TOKENIZER_REVISION = "sqlite-fts5-unicode61-rd2-v1"
_FTS_QUERY_REVISION = "fts5-explicit-or-quoted-terms-v1"
_FTS_TERM_CAP = 64
_PARSER_REVISION = "legacy-dapfam-family-qrel-v2"
_R0_VIEW_REVISION = "dapfam-chunks-doc-family-v1"
_R0W_VIEW_REVISION = "dapfam-tac512-prewindowed-family-maxp-v1"
_INDEX_SCHEMA_VERSION = "myis.p1-index-lineage.v2"


def process(
    request_path: Path,
    protected_root: Path,
    receipt_path: Path,
    *,
    store_root: Path | None = None,
    legacy_root: Path | None = None,
    repository_root: Path | None = None,
) -> Path:
    """Run P1 inside an owner-local process and emit aggregate-only evidence."""

    repository_root = (repository_root or _repository_root()).resolve()
    _validate_roots(
        protected_root,
        receipt_path,
        repository_root=repository_root,
        legacy_root=legacy_root,
    )
    if protected_root.is_file():
        raise OwnerLocalContractError("precomputed aggregate sources are forbidden; pass a protected input directory")
    if receipt_path.exists():
        raise FileExistsError(f"valid receipts are immutable and cannot be overwritten: {receipt_path}")
    request = validate_request(json.loads(request_path.read_text(encoding="utf-8")))
    if legacy_root is not None:
        return _process_legacy(
            request,
            legacy_root,
            receipt_path,
            store_root,
            repository_root=repository_root,
        )
    return _process_bundle(request, protected_root, receipt_path)


def _process_bundle(request: dict[str, Any], protected_root: Path, receipt_path: Path) -> Path:
    bundle = _load_bundle(protected_root)
    actual_hashes = {f"{name.removesuffix('.json')}_sha256": file_sha256(protected_root / name) for name in _BUNDLE_FILES}
    _require_declared_hashes(request, actual_hashes)
    rows = bundle["documents"]
    queries = bundle["queries"]
    qrels = bundle["qrels"]
    splits = bundle["splits"]
    metrics: list[dict[str, Any]] = []
    hashes: dict[str, str] = {f"input_{key}": value for key, value in actual_hashes.items()}
    started = time.perf_counter()
    for arm in ("R0", "R0-W"):
        for split in ("train", "selection"):
            subset = _queries_for_split(queries, splits, split)
            result = evaluate_baseline(documents=rows, queries=subset, qrels=qrels, arm_id=arm, top_k=100, window_size=512, split_name=split)
            metrics.extend(_tag_metrics(result["metrics"], arm))
            hashes[f"{arm.lower()}_{split}_metrics"] = result["metrics_hash"]
    aggregate_counts = {"documents": len(rows), "queries": len(queries), "train_queries": len(splits.get("train", [])), "selection_queries": len(splits.get("selection", []))}
    lineage = {"dataset_sha256": canonical_sha256(actual_hashes), "corpus_sha256": actual_hashes["documents_sha256"], "query_sha256": actual_hashes["queries_sha256"], "qrels_sha256": actual_hashes["qrels_sha256"], "split_sha256": actual_hashes["splits_sha256"], "index_sha256": canonical_sha256("in_memory_okapi_bm25_v1"), "evaluator_sha256": canonical_sha256("myis-p1-evaluator-v1")}
    receipt = build_receipt(request, aggregate_counts=aggregate_counts, aggregate_hashes=hashes, metrics=metrics, cost_usd=0.0, latency_seconds=time.perf_counter() - started, lineage_hashes=lineage, historical_exposure={"active_final_872_global_untouched": "not_assessed_from_fixture"})
    return _write_receipt(receipt_path, receipt)


def _process_legacy(
    request: dict[str, Any],
    legacy_root: Path,
    receipt_path: Path,
    store_root: Path | None,
    *,
    repository_root: Path,
) -> Path:
    root = legacy_root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise OwnerLocalContractError("legacy root must be a regular directory")
    try:
        assert_legacy_p1_request_current(request, root, repository_root)
    except ValueError as error:
        raise OwnerLocalContractError(str(error)) from error
    inventory = discover_legacy(root, include_protected_hashes=True)
    actual_hashes = build_input_hashes(root, inventory, include_protected=True)
    _require_declared_hashes(request, actual_hashes)
    candidates = inventory["candidates"]
    required = {"patents", "queries", "qrels", "qrels_domain", "chunks_doc", "chunks_tac"}
    missing = sorted(required - set(candidates))
    if missing:
        return _blocked_receipt(request, receipt_path, blockers=[f"legacy_missing:{item}" for item in missing], actual_hashes=actual_hashes)
    patents = _load_patents(root / candidates["patents"])
    family_map = {str(row["publication_id"]): str(row["family_id"]) for row in patents if row.get("publication_id") and row.get("family_id")}
    docs = _load_text_rows(root / candidates["chunks_doc"], family_map)
    passages = _load_text_rows(root / candidates["chunks_tac"], family_map)
    queries = _load_queries(root / candidates["queries"], family_map)
    qrels, qrel_domains = _load_qrels(
        root / candidates["qrels"],
        root / candidates["qrels_domain"],
        family_map,
        {row["family_id"] for row in docs} | {row["family_id"] for row in passages},
    )
    split_payload, exposure = _derive_splits(root, [str(row["query_id"]) for row in queries])
    if len(split_payload["train"]) != 250 or len(split_payload["selection"]) != 125:
        return _blocked_receipt(request, receipt_path, blockers=["active_split_cardinality_mismatch"], actual_hashes=actual_hashes, historical_exposure=exposure)
    _assign_declared_splits(queries, split_payload)
    split_membership = {name: values for name, values in split_payload.items() if name in {"train", "selection", "final"}}
    preflight_inputs = {
        "documents_sha256": actual_hashes["chunks_doc_sha256"],
        "passages_sha256": actual_hashes["chunks_tac_sha256"],
        "queries_sha256": actual_hashes["queries_sha256"],
        "qrels_sha256": actual_hashes["qrels_sha256"],
        "qrels_domain_sha256": actual_hashes["qrels_domain_sha256"],
        "family_map_sha256": canonical_sha256(family_map),
        "parser_revision": _PARSER_REVISION,
    }
    r0_integrity = run_integrity_preflight(
        documents=docs,
        queries=queries,
        targets=qrels,
        splits=split_membership,
        input_commitment=canonical_sha256({**preflight_inputs, "view": _R0_VIEW_REVISION}),
    )
    r0w_integrity = run_integrity_preflight(
        documents=passages,
        queries=queries,
        targets=qrels,
        splits=split_membership,
        input_commitment=canonical_sha256({**preflight_inputs, "view": _R0W_VIEW_REVISION}),
    )
    if r0_integrity["status"] != "pass" or r0w_integrity["status"] != "pass":
        return _blocked_receipt(
            request,
            receipt_path,
            blockers=["integrity_preflight_blocked"],
            actual_hashes=actual_hashes,
            historical_exposure=exposure,
            extra_hashes={"r0_integrity": r0_integrity["receipt_sha256"], "r0w_integrity": r0w_integrity["receipt_sha256"]},
        )
    destination = _store_path(
        store_root,
        legacy_root=legacy_project_root(root),
        repository_root=repository_root,
    )
    r0_index, r0_hash = _build_or_reuse_index(
        docs,
        root / candidates["chunks_doc"],
        destination / "r0",
        family_map=family_map,
        source_hashes=actual_hashes,
        view_revision=_R0_VIEW_REVISION,
    )
    rw_index, rw_hash = _build_or_reuse_index(
        passages,
        root / candidates["chunks_tac"],
        destination / "r0-w",
        family_map=family_map,
        source_hashes=actual_hashes,
        view_revision=_R0W_VIEW_REVISION,
    )
    metrics: list[dict[str, Any]] = []
    aggregate_hashes: dict[str, str] = {f"input_{key}": value for key, value in actual_hashes.items()}
    dataset_lineage = {
        "dataset_sha256": canonical_sha256(actual_hashes),
        "query_sha256": file_sha256(root / candidates["queries"]),
        "qrels_sha256": file_sha256(root / candidates["qrels"]),
    }
    corpus_lineage = {
        "R0": file_sha256(root / candidates["chunks_doc"]),
        "R0-W": file_sha256(root / candidates["chunks_tac"]),
    }
    started = time.perf_counter()
    for arm, index_path, corpus_rows, index_hash in (("R0", r0_index, docs, r0_hash), ("R0-W", rw_index, passages, rw_hash)):
        ranker = _sqlite_ranker(index_path)
        for split in ("train", "selection"):
            subset_ids = set(split_payload[split])
            subset = [
                {"query_id": row["query_id"], "text": row["text"], "split": row["split"]}
                for row in queries
                if str(row["query_id"]) in subset_ids
            ]
            lineage_hint = {
                **dataset_lineage,
                "corpus_sha256": corpus_lineage[arm],
                "index_sha256": index_hash,
            }
            arguments = {
                "documents": corpus_rows,
                "queries": subset,
                "qrels": qrels,
                "arm_id": arm,
                "top_k": 100,
                "window_size": 512,
                "qrel_domains": qrel_domains,
                "split_name": split,
                "ranker": ranker,
                "lineage_hint": lineage_hint,
                # TAC512 rows are the controlled input view.  Re-windowing
                # would change its retrieval universe and family MaxP result.
                "documents_are_windowed": arm == "R0-W",
            }
            first = evaluate_baseline(**arguments)
            second = evaluate_baseline(**arguments)
            if not _repeat_equivalent(first, second):
                return _blocked_receipt(request, receipt_path, blockers=[f"{arm}_{split}_determinism_mismatch"], actual_hashes=actual_hashes, historical_exposure=exposure)
            metrics.extend(_tag_metrics(first["metrics"], arm))
            aggregate_hashes[f"{arm.lower()}_{split}_metrics"] = first["metrics_hash"]
        aggregate_hashes[f"{arm.lower()}_index"] = index_hash
    aggregate_counts = {"patents": len(patents), "r0_documents": len(docs), "r0w_passages": len(passages), "queries": len(queries), "train_queries": 250, "selection_queries": 125, "final_queries": len(split_payload["final"])}
    lineage = {"dataset_sha256": canonical_sha256(actual_hashes), "corpus_sha256": actual_hashes["chunks_doc_sha256"], "query_sha256": actual_hashes["queries_sha256"], "qrels_sha256": actual_hashes["qrels_sha256"], "split_sha256": canonical_sha256(split_payload), "index_sha256": canonical_sha256({"r0": r0_hash, "r0w": rw_hash}), "evaluator_sha256": canonical_sha256("myis-p1-evaluator-v1")}
    blockers = []
    if exposure.get("active_final_872_global_untouched") != "not_claimable":
        blockers.append("historical_exposure_present_final_872_not_globally_untouched")
    if blockers:
        return _blocked_receipt(
            request,
            receipt_path,
            blockers=blockers,
            actual_hashes=actual_hashes,
            historical_exposure=exposure,
            extra_hashes={
                "r0_integrity": r0_integrity["receipt_sha256"],
                "r0w_integrity": r0w_integrity["receipt_sha256"],
                "r0_index": r0_hash,
                "r0w_index": rw_hash,
            },
        )
    aggregate_hashes["r0_integrity"] = r0_integrity["receipt_sha256"]
    aggregate_hashes["r0w_integrity"] = r0w_integrity["receipt_sha256"]
    receipt = build_receipt(request, aggregate_counts=aggregate_counts, aggregate_hashes=aggregate_hashes, metrics=metrics, cost_usd=0.0, latency_seconds=time.perf_counter() - started, lineage_hashes=lineage, historical_exposure=exposure, status="accepted" if not blockers else "blocked", blockers=blockers)
    return _write_receipt(receipt_path, receipt)


def _build_or_reuse_index(
    rows: list[dict[str, str]],
    source_path: Path,
    destination: Path,
    *,
    family_map: Mapping[str, str],
    source_hashes: Mapping[str, str],
    view_revision: str,
) -> tuple[Path, str]:
    """Build one immutable FTS generation or reuse only a verified one."""
    if not source_path.is_file() or source_path.is_symlink():
        raise OwnerLocalContractError("legacy index source must be a regular file")
    canonical_rows = sorted(
        (
            {"doc_id": str(row["doc_id"]), "family_id": str(row["family_id"]), "text": str(row["text"])}
            for row in rows
        ),
        key=lambda row: (row["doc_id"], row["family_id"], row["text"]),
    )
    config = {
        "schema_version": _INDEX_SCHEMA_VERSION,
        "scorer": "sqlite_fts5_bm25_v1",
        "tokenizer": _FTS_TOKENIZER,
        "tokenizer_revision": _FTS_TOKENIZER_REVISION,
        "query_revision": _FTS_QUERY_REVISION,
        "term_cap": _FTS_TERM_CAP,
        "parser_revision": _PARSER_REVISION,
        "view_revision": view_revision,
        "source_sha256": file_sha256(source_path),
        "source_hashes_sha256": canonical_sha256(dict(sorted(source_hashes.items()))),
        "canonical_rows_sha256": canonical_sha256(canonical_rows),
        "family_id_map_sha256": canonical_sha256({
            "publication_to_family": dict(sorted((str(key), str(value)) for key, value in family_map.items())),
            "document_to_family": {row["doc_id"]: row["family_id"] for row in canonical_rows},
        }),
        "rows": len(canonical_rows),
    }
    lineage_hash = canonical_sha256(config)
    destination.mkdir(parents=True, exist_ok=True)
    index_dir: Path | None = None
    index_path: Path | None = None
    manifest_path: Path | None = None
    for generation in range(1000):
        suffix = "" if generation == 0 else f"-g{generation:04d}"
        candidate_dir = destination / f"{lineage_hash[:16]}{suffix}"
        candidate_index = candidate_dir / "index.sqlite"
        candidate_manifest = candidate_dir / "lineage.json"
        if candidate_dir.exists():
            try:
                return _reuse_verified_index(
                    candidate_dir,
                    candidate_index,
                    candidate_manifest,
                    config,
                    lineage_hash,
                )
            except OwnerLocalContractError:
                # Preserve invalid generations as evidence and allocate a new one.
                continue
        try:
            candidate_dir.mkdir()
        except FileExistsError:
            continue
        index_dir = candidate_dir
        index_path = candidate_index
        manifest_path = candidate_manifest
        break
    if index_dir is None or index_path is None or manifest_path is None:
        raise OwnerLocalContractError("index generation limit reached without a reusable index")
    temp_path = index_dir / "index.sqlite.tmp"
    temp_manifest_path = index_dir / "lineage.json.tmp"
    if temp_path.exists() or temp_manifest_path.exists():
        raise OwnerLocalContractError("partial index generation exists and will not be overwritten")
    connection = sqlite3.connect(temp_path)
    try:
        connection.execute(
            f"CREATE VIRTUAL TABLE rows USING fts5(doc_id UNINDEXED, family_id UNINDEXED, text, tokenize='{_FTS_TOKENIZER}')"
        )
        batch: list[tuple[str, str, str]] = []
        for row in canonical_rows:
            batch.append((row["doc_id"], row["family_id"], row["text"]))
            if len(batch) >= 1000:
                connection.executemany("INSERT INTO rows(doc_id, family_id, text) VALUES (?, ?, ?)", batch)
                batch.clear()
        if batch:
            connection.executemany("INSERT INTO rows(doc_id, family_id, text) VALUES (?, ?, ?)", batch)
        connection.execute("INSERT INTO rows(rows) VALUES ('optimize')")
        connection.commit()
    finally:
        connection.close()
    sqlite_sha256 = file_sha256(temp_path)
    manifest = {
        "schema_version": _INDEX_SCHEMA_VERSION,
        "lineage_sha256": lineage_hash,
        "sqlite_sha256": sqlite_sha256,
        "config": config,
    }
    temp_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # The generation directory was newly created.  Refuse to replace any
    # unexpected path even here, preserving stale/corrupt evidence verbatim.
    if index_path.exists() or manifest_path.exists():
        raise OwnerLocalContractError("existing index generation cannot be overwritten")
    temp_path.replace(index_path)
    temp_manifest_path.replace(manifest_path)
    _verify_index(index_path, expected_rows=len(canonical_rows))
    return index_path, sqlite_sha256


def _reuse_verified_index(
    index_dir: Path,
    index_path: Path,
    manifest_path: Path,
    config: Mapping[str, Any],
    lineage_hash: str,
) -> tuple[Path, str]:
    if index_dir.is_symlink() or not index_path.is_file() or index_path.is_symlink() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise OwnerLocalContractError("existing index generation is incomplete or unsafe; it will not be overwritten")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OwnerLocalContractError("existing index lineage manifest is unreadable; it will not be overwritten") from error
    actual_hash = file_sha256(index_path)
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != _INDEX_SCHEMA_VERSION
        or manifest.get("lineage_sha256") != lineage_hash
        or manifest.get("config") != dict(config)
        or manifest.get("sqlite_sha256") != actual_hash
    ):
        raise OwnerLocalContractError("existing index generation has stale or corrupt lineage; it will not be overwritten")
    _verify_index(index_path, expected_rows=int(config["rows"]))
    return index_path, actual_hash


def _verify_index(index_path: Path, *, expected_rows: int) -> None:
    try:
        connection = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise OwnerLocalContractError("existing index fails SQLite integrity verification")
            actual_rows = connection.execute("SELECT count(*) FROM rows").fetchone()
            if actual_rows != (expected_rows,):
                raise OwnerLocalContractError("existing index row count does not match lineage")
        finally:
            connection.close()
    except sqlite3.DatabaseError as error:
        raise OwnerLocalContractError("existing index cannot be opened read-only") from error


def _sqlite_ranker(index_path: Path):
    def rank(query: str) -> list[tuple[str, str, float]]:
        terms = tuple(sorted(set(tokenize(query))))
        if not terms:
            return []
        if len(terms) > _FTS_TERM_CAP:
            raise OwnerLocalContractError("FTS query exceeds the configured term cap")
        expression = " OR ".join(f'"{term}"' for term in terms)
        connection = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
        try:
            rows = connection.execute("SELECT doc_id, family_id, bm25(rows) AS score FROM rows WHERE rows MATCH ? ORDER BY score ASC, doc_id ASC", (expression,)).fetchall()
        finally:
            connection.close()
        return [(str(doc_id), str(family_id), -float(score)) for doc_id, family_id, score in rows]

    return rank


def _load_patents(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in iter_jsonl(path):
        # Legacy Paper-D exports use patent_id as the family-level candidate key.
        # Preserve that contract explicitly when no separate family field exists.
        family = pick(row, ("family_id", "family", "familyId", "patent_family_id", "patent_id"))
        publication = pick(row, ("publication_id", "publication_number", "patent_id", "id"), required=False)
        rows.append({"family_id": family, "publication_id": publication})
    return rows


def _load_text_rows(path: Path, family_map: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, raw in enumerate(iter_jsonl(path)):
        doc_id = pick(raw, ("chunk_id", "passage_id", "doc_id", "document_id", "id"), required=False) or f"row-{index:09d}"
        family = pick(raw, ("family_id", "family", "familyId", "patent_family_id"), required=False)
        publication = pick(raw, ("publication_id", "publication_number", "patent_id", "document_id"), required=False)
        family = family or family_map.get(publication, publication or doc_id)
        text = text_value(raw, ("text", "content", "passage_text", "chunk_text", "tac_text", "title", "abstract", "claims"))
        if text:
            rows.append({"doc_id": doc_id, "family_id": family, "text": text})
    if not rows:
        raise ValueError(f"no searchable text rows in {path}")
    return rows


def _load_queries(path: Path, family_map: Mapping[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in iter_jsonl(path):
        query_id = pick(raw, ("query_id", "qid", "id"))
        text = text_value(raw, ("text", "query", "title", "abstract", "tac"))
        if text:
            family_id = pick(
                raw,
                ("query_family_id", "family_id", "family", "familyId", "patent_family_id"),
                required=False,
            ) or family_map.get(query_id, "")
            if not family_id:
                raise OwnerLocalContractError("query family mapping cannot be resolved")
            rows.append({"query_id": query_id, "family_id": family_id, "text": text, "split": "unassigned"})
    return rows


def _load_qrels(
    path: Path,
    domain_path: Path,
    family_map: Mapping[str, str],
    known_families: set[str],
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    base = _read_qrel_file(path, family_map, known_families, require_domain_label=False)
    domain = _read_qrel_file(domain_path, family_map, known_families, require_domain_label=True)
    base_pairs = {(query_id, family) for query_id, families in base.items() for family in families}
    domain_pairs = {(query_id, family) for query_id, families in domain.items() for family in families}
    if base_pairs != domain_pairs:
        raise OwnerLocalContractError("base and domain qrels do not resolve to the same positive family relevance pairs")
    qrel_domains = {
        query_id: {family: label for family, label in families.items()}
        for query_id, families in domain.items()
    }
    if any(len(qrel_domains.get(query_id, {})) != len(families) for query_id, families in base.items()):
        raise OwnerLocalContractError("domain qrels do not provide one IN/OUT label per positive family")
    return base, qrel_domains


def _read_qrel_file(
    path: Path,
    family_map: Mapping[str, str],
    known_families: set[str],
    *,
    require_domain_label: bool,
) -> dict[str, dict[str, str]] | dict[str, set[str]]:
    labels: dict[str, dict[str, str]] = {}
    targets: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 3:
                fields = line.split()
            if len(fields) < 3:
                continue
            query_id, target_id = fields[0], fields[2]
            try:
                relevance = int(float(fields[3])) if len(fields) > 3 else 1
            except ValueError:
                continue
            if relevance <= 0:
                continue
            family = target_id if target_id in known_families else family_map.get(target_id, target_id)
            if require_domain_label:
                label = fields[4].strip().upper() if len(fields) >= 5 else ""
                if label not in {"IN", "OUT"}:
                    raise OwnerLocalContractError("domain qrels contain a missing or invalid IN/OUT label")
                previous = labels.setdefault(query_id, {}).setdefault(family, label)
                if previous != label:
                    raise OwnerLocalContractError("domain qrels assign conflicting labels to one query-family pair")
            else:
                targets.setdefault(query_id, set()).add(family)
    return labels if require_domain_label else targets


def _assign_declared_splits(queries: list[dict[str, str]], split_payload: Mapping[str, Sequence[str]]) -> None:
    assignments: dict[str, str] = {}
    for split in ("train", "selection", "final"):
        for query_id in split_payload.get(split, ()):
            if query_id in assignments:
                raise OwnerLocalContractError("split derivation assigned a query to more than one split")
            assignments[query_id] = split
    for query in queries:
        split = assignments.get(str(query["query_id"]))
        if split is None:
            raise OwnerLocalContractError("split derivation omitted a loaded query")
        query["split"] = split


def _derive_splits(root: Path, query_ids: list[str]) -> tuple[dict[str, list[str]], dict[str, Any]]:
    ordered = sorted(set(query_ids), key=lambda value: hashlib.sha256(f"42:{value}".encode("utf-8")).hexdigest())
    train = ordered[:250]
    selection = ordered[250:375]
    final = ordered[375:]
    historical: set[str] = set()
    split_files = list(root.parents[1].glob("paper-*/config/*split*.json")) if len(root.parents) > 1 else []
    for path in split_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        historical.update(_collect_exposed_ids(payload))
    return {"seed": 42, "train": train, "selection": selection, "final": final}, {
        "paper_a": "historically_exposed",
        "paper_b": "historically_exposed",
        "paper_d": "historically_exposed",
        "paper_d_test_997": "historically_exposed",
        "historical_split_sources": len(split_files),
        "historical_exposed_query_count": len(historical),
        "active_final_872_global_untouched": "not_claimable" if historical else "not_verified",
        "active_final_overlap_count": len(set(final) & historical),
    }


def _collect_exposed_ids(value: Any) -> set[str]:
    exposed: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if any(token in str(key).casefold() for token in ("test", "heldout", "holdout", "eval")) and isinstance(item, list):
                exposed.update(str(entry) for entry in item if isinstance(entry, (str, int)))
            else:
                exposed.update(_collect_exposed_ids(item))
    elif isinstance(value, list):
        for item in value:
            exposed.update(_collect_exposed_ids(item))
    return exposed


def _tag_metrics(metrics: Iterable[dict[str, Any]], arm: str) -> list[dict[str, Any]]:
    return [{**dict(metric), "arm": arm} for metric in metrics]


def _repeat_equivalent(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    """Compare every protected-run commitment that can affect retrieval."""
    fields = (
        "metrics",
        "metrics_hash",
        "input_commitment",
        "query_commitment",
        "ranking_commitment",
        "lineage",
        "retrieval",
    )
    return all(first.get(field) == second.get(field) for field in fields)


def _require_declared_hashes(request: dict[str, Any], actual: dict[str, str]) -> None:
    declared = {str(key): str(value) for key, value in request["input_hashes"].items()}
    if declared != actual:
        missing = sorted(set(actual) - set(declared))
        extra = sorted(set(declared) - set(actual))
        changed = sorted(key for key in set(actual) & set(declared) if actual[key] != declared[key])
        raise OwnerLocalContractError(f"declared input hashes do not match files: missing={missing}, extra={extra}, changed={changed}")


def _blocked_receipt(
    request: dict[str, Any],
    receipt_path: Path,
    *,
    blockers: list[str],
    actual_hashes: dict[str, str],
    historical_exposure: dict[str, Any] | None = None,
    extra_hashes: Mapping[str, str] | None = None,
) -> Path:
    metrics = [{"name": "recall_at_100", "value": None, "n": 0, "hits": 0, "scope": scope, "split": "train_selection", "direction": "maximize", "denominator": "queries_with_positive_family_relevance", "evidence_role": "blocked"} for scope in ("ALL", "IN", "OUT")]
    hashes = {f"input_{key}": value for key, value in actual_hashes.items()}
    hashes.update(dict(extra_hashes or {}))
    lineage = {"dataset_sha256": canonical_sha256(actual_hashes), "corpus_sha256": canonical_sha256(actual_hashes), "query_sha256": canonical_sha256(actual_hashes.get("queries_sha256", "")), "qrels_sha256": canonical_sha256(actual_hashes.get("qrels_sha256", "")), "split_sha256": canonical_sha256("blocked"), "index_sha256": canonical_sha256("not_built"), "evaluator_sha256": canonical_sha256("myis-p1-evaluator-v1")}
    receipt = build_receipt(request, aggregate_counts={"documents": 0, "queries": 0}, aggregate_hashes=hashes or {"blocker": canonical_sha256(blockers)}, metrics=metrics, cost_usd=0.0, latency_seconds=0.0, lineage_hashes=lineage, historical_exposure=historical_exposure or {}, status="blocked", blockers=blockers)
    return _write_receipt(receipt_path, receipt)


def _write_receipt(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _store_path(
    store_root: Path | None,
    *,
    legacy_root: Path | None = None,
    repository_root: Path | None = None,
) -> Path:
    if store_root is not None:
        path = store_root.resolve()
    else:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        path = (base / "myIS" / "p1-cpu-store").resolve()
    git_root = (repository_root or _repository_root()).resolve()
    if _is_within(path, git_root) or (legacy_root is not None and _is_within(path, legacy_root.resolve())):
        raise OwnerLocalContractError("P1 derived index store must be outside Git and legacy roots")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _repository_root() -> Path:
    for candidate in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        if (candidate / ".git").exists():
            return candidate
    return Path.cwd().resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _validate_roots(
    protected_root: Path,
    receipt_path: Path,
    *,
    repository_root: Path,
    legacy_root: Path | None,
) -> None:
    if protected_root.is_symlink():
        raise OwnerLocalContractError("protected input root must not be a symlink")
    if receipt_path.is_symlink():
        raise OwnerLocalContractError("receipt path must not be a symlink")
    resolved_receipt = receipt_path.resolve()
    if _is_within(resolved_receipt, repository_root):
        raise OwnerLocalContractError("owner-local receipts must be written outside Git")
    if legacy_root is not None and _is_within(resolved_receipt, legacy_project_root(legacy_root.resolve())):
        raise OwnerLocalContractError("owner-local receipts must be written outside the read-only legacy tree")


def _load_bundle(root: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in _BUNDLE_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise OwnerLocalContractError(f"protected bundle file is missing or not regular: {name}")
        try:
            values[name.removesuffix(".json")] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise OwnerLocalContractError(f"protected bundle JSON is invalid: {name}") from error
    if not isinstance(values["documents"], list) or not isinstance(values["queries"], list):
        raise OwnerLocalContractError("documents and queries must be arrays")
    if not isinstance(values["qrels"], dict) or not isinstance(values["splits"], dict):
        raise OwnerLocalContractError("qrels and splits must be objects")
    for split, query_ids in values["splits"].items():
        if not isinstance(split, str) or not isinstance(query_ids, list) or any(not isinstance(item, str) for item in query_ids):
            raise OwnerLocalContractError("splits must map names to query-id arrays")
    return values


def _queries_for_split(queries: list[dict[str, Any]], splits: dict[str, list[str]], split: str) -> list[dict[str, Any]]:
    allowed = set(splits.get(split, []))
    return [query for query in queries if str(query.get("query_id")) in allowed]
