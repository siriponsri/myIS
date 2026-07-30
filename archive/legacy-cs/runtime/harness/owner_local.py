"""Owner-local DAPFAM discovery, validation, and safe aggregation.

Only this module opens the declared DAPFAM sources. Callers receive sealed raw
membership separately from a hash/count-only batch suitable for projections.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .dapfam_contracts import (
    OWNER_VALUE_BATCH_SCHEMA,
    GeneratorIdentity,
    OwnerValueBatchV1,
    SourceCommitment,
    ValidationReceipt,
    proposal_hash,
)
from .g1_preparation import PreparedSplit, prepare_shared_split


SOURCE_PATHS = {
    "corpus": "processed/dapfam/patents.jsonl",
    "queries": "processed/dapfam/queries.jsonl",
    "qrels": "processed/dapfam/qrels.tsv",
    "out_strata": "processed/retrieval/dapfam_paper_aligned/qrels_domain.tsv",
    "validation": "processed/dapfam/validation_summary.json",
}
EXPECTED_BYTES = {
    "corpus": 3_125_138_209,
    "queries": 158_762_269,
    "qrels": 2_194_236,
    "out_strata": 2_349_036,
    "validation": 2_243,
}
EXPECTED_SHA256 = {
    "corpus": "2d79ee7d0479565711889553d2da849fef5e3a7aa5014bf398a43c5becd0cab7",
    "queries": "50a0e9c5673e9e3e0ae2558272dc824572554067bd1443d043016aedeb7fe3fa",
    "qrels": "adf93d74d539d883f4ebeb48ecf5ef7e39acc21680c589b1b171c07d25097828",
    "out_strata": "07a2f16a98c1c430422eb83e29d597668246eef2892d0609ee72f040a0dd0270",
    "validation": "e3af6a11caad81021b8f0ae33ba3da688d512a70290e0df42eeda19086e8cc74",
}


class OwnerLocalPreparationError(RuntimeError):
    """Generic fail-closed error safe to expose without source payloads."""


def discover_source_root(repository_root: Path) -> Path:
    candidates: list[Path] = []
    for ancestor in (repository_root.resolve(), *repository_root.resolve().parents):
        candidates.extend(
            [
                ancestor / "00_App" / "is1-projects" / "shared" / "data",
                ancestor / "data",
            ]
        )
    valid = [root for root in candidates if all((root / relative).is_file() for relative in SOURCE_PATHS.values())]
    unique = list(dict.fromkeys(path.resolve() for path in valid))
    if len(unique) != 1:
        raise OwnerLocalPreparationError("DAPFAM_SOURCE_DISCOVERY_AMBIGUOUS")
    return unique[0]


def describe_source_schema(source_root: Path) -> dict[str, object]:
    """Return field names only; never return source values or identifiers."""

    paths = _validated_source_paths(source_root.resolve(strict=True))
    output: dict[str, object] = {}
    for role in ("corpus", "queries"):
        first = next(iter(_jsonl(paths[role])), None)
        nested = {
            str(key): sorted(str(child) for child in value)
            for key, value in (first or {}).items()
            if isinstance(value, Mapping)
        }
        output[role] = {
            "format": "jsonl",
            "fields": sorted(str(key) for key in (first or {})),
            "nested_fields": nested,
        }
        id_names = ("publication_id", "corpus_id", "doc_id", "patent_id", "_id", "id") if role == "corpus" else ("query_id", "qid", "_id", "id")
        row_count = 0
        missing_count = 0
        identifiers: set[str] = set()
        for row in _jsonl(paths[role]):
            row_count += 1
            identifier = _first(row, *id_names)
            if identifier is None:
                missing_count += 1
            else:
                identifiers.add(str(identifier))
        output[role]["identifier_summary"] = {
            "rows": row_count,
            "missing": missing_count,
            "unique": len(identifiers),
            "duplicates": row_count - missing_count - len(identifiers),
        }
    for role in ("qrels", "out_strata"):
        with paths[role].open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t")
            header = next(reader, [])
        output[role] = {"format": "tsv", "fields": [str(value) for value in header]}
    corpus_ids, family_pairs, corpus_count = _corpus_inventory(paths["corpus"])
    output["corpus"]["family_summary"] = {
        "rows": corpus_count,
        "unique_publications": len(corpus_ids),
        "unique_mappings": len(family_pairs),
    }
    validation = json.loads(paths["validation"].read_text(encoding="utf-8"))
    output["validation"] = {
        "format": "json",
        "fields": sorted(str(key) for key in validation) if isinstance(validation, Mapping) else [],
    }
    return {"status": "PASS", "schema_only": True, "sources": output}


def prepare_owner_value_batch(repository_root: Path, source_root: Path) -> tuple[OwnerValueBatchV1, PreparedSplit, dict[str, str]]:
    repository_root = repository_root.resolve(strict=True)
    source_root = source_root.resolve(strict=True)
    paths = _validated_source_paths(source_root)
    commitments = [_source_commitment(role, paths[role]) for role in SOURCE_PATHS]
    query_ids = _query_inventory(paths["queries"])
    qrels_query_ids, qrels_document_ids, qrels_count = _qrels_inventory(paths["qrels"])
    domain_by_query, out_positive, domain_distribution = _domain_inventory(paths["out_strata"])
    corpus_ids, family_pairs, corpus_count = _corpus_inventory(paths["corpus"])

    if len(query_ids) != 1247 or not qrels_query_ids.issubset(query_ids):
        raise OwnerLocalPreparationError("DAPFAM_QUERY_ALIGNMENT_FAILED")
    if corpus_count != 45_336 or qrels_count != 49_869:
        raise OwnerLocalPreparationError("DAPFAM_INVENTORY_COUNT_MISMATCH")
    if domain_by_query.keys() != query_ids or not out_positive.issubset(query_ids):
        raise OwnerLocalPreparationError("DAPFAM_STRATA_ALIGNMENT_FAILED")
    if set(domain_distribution) != {"IN", "OUT", "NC"} or sum(domain_distribution.values()) != qrels_count:
        raise OwnerLocalPreparationError("DAPFAM_DOMAIN_DISTRIBUTION_MISMATCH")
    if qrels_document_ids and not qrels_document_ids.issubset(corpus_ids):
        raise OwnerLocalPreparationError("DAPFAM_CORPUS_ALIGNMENT_FAILED")

    strata = {
        query_id: "+".join(sorted(domain_by_query[query_id])) or "NONE"
        for query_id in sorted(query_ids)
    }
    prepared = prepare_shared_split(strata, out_positive_query_ids=out_positive)
    family_sha = _hash_lines(f"{publication_id}\t{family_id}" for publication_id, family_id in sorted(family_pairs))
    now = datetime.now(timezone.utc)
    semantic: dict[str, Any] = {
        "schema_version": OWNER_VALUE_BATCH_SCHEMA,
        "document_kind": "g1_owner_value_batch",
        "status": "proposal",
        "executable": False,
        "gate": "G1",
        "gate_status": "pending",
        "authorization": "NOT_AUTHORIZED",
        "scientific_run": False,
        "dataset_access": "owner_local_read_only",
        "scientific_metric_count": 0,
        "track": "C",
        "phase": "F1",
        "task": "F1.1",
        "generated_at_utc": now,
        "generator": GeneratorIdentity(
            program_id="myis-research",
            protocol_version="1.0",
            research_version="0.1",
            package_version="0.1.0",
            git_commit=_git_commit(repository_root),
            python_version=platform.python_version(),
            platform=platform.platform(),
        ).model_dump(mode="json"),
        "sources": [item.model_dump(mode="json") for item in commitments],
        "inventory_counts": {
            "corpus": corpus_count,
            "queries": len(query_ids),
            "qrels": qrels_count,
        },
        "qrels_domain_distribution": dict(sorted(domain_distribution.items())),
        "family_commitment_sha256": family_sha,
        "evaluator": {
            "evaluator_id": "dapfam-family-retrieval-v1",
            "unit": "patent_family",
            "relevance_rule": "grade_gt_0",
            "primary_metric": "recall_at_100",
            "claim_boundary": "retrieval_relevance_not_legal_truth",
        },
        "field_protocol": {
            "B0": "TAC dense top-400 then family top-100",
            "B1": "TAC dense/BM25 min-max 0.7/0.3 then family top-100",
            "B2": "TAC/Abstract/Claim1 naive RRF k=60 then family top-100",
        },
        "published_targets": {
            "encoder": "Llama-Embed-Nemotron-8B",
            "encoder_revision": "aa3b43a495a9b280d1bdb716da37c54bb495d630",
            "arms": ["B0", "B1", "B2"],
        },
        "split": prepared.commitment.model_dump(mode="json"),
        "unresolved_owner_decisions": [
            "scientific_compute_provider_time_cost_budget",
            "reproduction_authorization_F1.1_B0_B1_B2_only",
            "paid_gpu_api_or_data_egress_permission",
            "clean_committed_implementation_identity",
            "final_G1_immutable_decision",
        ],
        "owner_decision_sha256": None,
        "mlflow": None,
    }
    semantic["proposal_sha256"] = proposal_hash(semantic)
    semantic["validation"] = ValidationReceipt(
        status="PASS",
        validated_at_utc=now,
        checks={
            "source_paths_exact": True,
            "source_bytes_match": True,
            "source_hashes_computed": True,
            "query_count_1247": True,
            "qrels_query_alignment": True,
            "corpus_qrels_alignment": True,
            "domain_strata_complete": True,
            "split_exact_and_disjoint": True,
            "safe_projection_redacted": True,
        },
    ).model_dump(mode="json")
    batch = OwnerValueBatchV1.model_validate(semantic)
    return batch, prepared, {role: str(path) for role, path in paths.items()}


def _validated_source_paths(source_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for role, relative in SOURCE_PATHS.items():
        path = source_root / relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size != EXPECTED_BYTES[role]:
            raise OwnerLocalPreparationError("DAPFAM_SOURCE_ANCHOR_MISMATCH")
        result[role] = path
    return result


def _source_commitment(role: str, path: Path) -> SourceCommitment:
    digest = _sha256_file(path)
    if digest != EXPECTED_SHA256[role]:
        raise OwnerLocalPreparationError("DAPFAM_SOURCE_HASH_MISMATCH")
    return SourceCommitment(
        role=role,
        source_id=f"dapfam-{role}",
        relative_path=SOURCE_PATHS[role],
        bytes=path.stat().st_size,
        sha256=digest,
    )


def _query_inventory(path: Path) -> set[str]:
    ids: set[str] = set()
    for payload in _jsonl(path):
        query_id = _first(payload, "query_id", "qid", "_id", "id")
        if query_id is None or str(query_id) in ids:
            raise OwnerLocalPreparationError("DAPFAM_QUERY_SCHEMA_INVALID")
        ids.add(str(query_id))
    return ids


def _qrels_inventory(path: Path) -> tuple[set[str], set[str], int]:
    queries: set[str] = set()
    documents: set[str] = set()
    count = 0
    for row in _tsv(path, role="qrels"):
        query_id = _first(row, "query_id", "qid", "query-id")
        document_id = _first(row, "corpus_id", "doc_id", "document_id", "patent_id", "family_id")
        if query_id is None or document_id is None:
            raise OwnerLocalPreparationError("DAPFAM_QRELS_SCHEMA_INVALID")
        queries.add(str(query_id))
        documents.add(str(document_id))
        count += 1
    return queries, documents, count


def _domain_inventory(path: Path) -> tuple[dict[str, set[str]], set[str], Counter[str]]:
    domains: dict[str, set[str]] = defaultdict(set)
    out_positive: set[str] = set()
    distribution: Counter[str] = Counter()
    for row in _tsv(path, role="out_strata"):
        query_id = _first(row, "query_id", "qid", "query-id")
        domain = _first(row, "domain", "domain_label", "stratum")
        grade = _first(row, "grade", "score", "relevance", "label")
        if query_id is None or domain is None or grade is None:
            raise OwnerLocalPreparationError("DAPFAM_DOMAIN_SCHEMA_INVALID")
        normalized = str(domain).strip().upper()
        if normalized not in {"IN", "OUT", "NC"}:
            raise OwnerLocalPreparationError("DAPFAM_DOMAIN_VALUE_INVALID")
        query_id = str(query_id)
        domains[query_id].add(normalized)
        distribution[normalized] += 1
        if float(grade) > 0:
            if normalized == "OUT":
                out_positive.add(query_id)
    return dict(domains), out_positive, distribution


def _corpus_inventory(path: Path) -> tuple[set[str], set[tuple[str, str]], int]:
    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    family_by_publication: dict[str, str] = {}
    count = 0
    for payload in _jsonl(path):
        publication = _first(payload, "publication_id", "corpus_id", "doc_id", "patent_id", "_id", "id")
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}
        family = _first(payload, "family_id", "family", "family-id") or _first(
            metadata, "family_id", "family", "family-id", "simple_family_id", "docdb_family_id"
        ) or publication
        if publication is None or family is None:
            raise OwnerLocalPreparationError("DAPFAM_CORPUS_SCHEMA_INVALID")
        publication_id = str(publication)
        family_id = str(family)
        if publication_id in family_by_publication and family_by_publication[publication_id] != family_id:
            raise OwnerLocalPreparationError("DAPFAM_FAMILY_MAPPING_AMBIGUOUS")
        family_by_publication[publication_id] = family_id
        ids.add(publication_id)
        pairs.add((publication_id, family_id))
        count += 1
    return ids, pairs, count


def _jsonl(path: Path) -> Iterable[Mapping[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, Mapping):
                    raise OwnerLocalPreparationError("DAPFAM_JSONL_SCHEMA_INVALID")
                yield payload


def _tsv(path: Path, *, role: str) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        first = next(reader, None)
        if not first:
            raise OwnerLocalPreparationError("DAPFAM_TSV_HEADER_INVALID")
        normalized = {value.strip().lower() for value in first}
        has_header = bool(normalized & {"query_id", "qid", "corpus_id", "doc_id", "domain", "grade"})
        if has_header:
            for values in reader:
                yield dict(zip(first, values, strict=False))
            return
        expected = 4 if role == "qrels" else 5
        for values in (first, *reader):
            if len(values) != expected:
                raise OwnerLocalPreparationError("DAPFAM_TSV_ROW_INVALID")
            row = {
                "query_id": values[0],
                "query_partition": values[1],
                "corpus_id": values[2],
                "grade": values[3],
            }
            if role == "out_strata":
                row["domain"] = values[4]
            yield row


def _first(payload: Mapping[str, Any], *names: str) -> Any:
    lowered = {str(key).lower(): value for key, value in payload.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in {None, ""}:
            return value
    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_lines(lines: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _git_commit(repository_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, check=True, capture_output=True, text=True
    ).stdout.strip()
