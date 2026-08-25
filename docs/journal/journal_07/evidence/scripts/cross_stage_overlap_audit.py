"""Write aggregate-only cross-stage overlap evidence.

The script reads protected split metadata locally, but its output contains only
counts and whole-file hashes. It never writes query, family, or publication IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from itertools import combinations
from pathlib import Path

import pyarrow.ipc as ipc


STAGE_NAMES = ("train", "selection", "final")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_tac_hash(row: dict[str, object]) -> str:
    text = "\n\n".join(str(row.get(field) or "") for field in ("title_en", "abstract_en", "claims_text"))
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pairwise_counts(values: dict[str, set[str]]) -> dict[str, int]:
    return {
        f"{left}_vs_{right}": len(values[left] & values[right])
        for left, right in combinations(STAGE_NAMES, 2)
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    parent_split = args.owner_store / "armindex/a4/selection-125/a4-selection-125-20260821T000000Z-canonical-001/input/parent-split.json"
    query_arrow = args.owner_store / "armindex/a4/source-staging-20260821/queries.arrow"
    split = json.loads(parent_split.read_text(encoding="utf-8"))
    stage_ids = {name: set(split[name]) for name in STAGE_NAMES}

    with query_arrow.open("rb") as handle:
        table = ipc.open_stream(handle).read_all()
    query_schema = table.schema.names
    rows = table.select(["query_id", "title_en", "abstract_en", "claims_text"]).to_pylist()
    text_hash_by_id = {str(row["query_id"]): normalized_tac_hash(row) for row in rows}
    stage_text_hashes = {
        name: {text_hash_by_id[query_id] for query_id in identifiers}
        for name, identifiers in stage_ids.items()
    }

    missing_ids = sum(len(ids - text_hash_by_id.keys()) for ids in stage_ids.values())
    result = {
        "schema_version": "rcrs.cross-stage-overlap-audit.v1",
        "status": "PASS_AGGREGATE_ONLY_WITH_METADATA_LIMITS" if missing_ids == 0 else "FAIL_MISSING_QUERY_METADATA",
        "protected_payload_included": False,
        "inputs": {
            "parent_split_sha256": file_sha256(parent_split),
            "query_arrow_sha256": file_sha256(query_arrow),
        },
        "stage_query_counts": {name: len(stage_ids[name]) for name in STAGE_NAMES},
        "exact_query_id_overlap": pairwise_counts(stage_ids),
        "normalized_query_tac_overlap": pairwise_counts(stage_text_hashes),
        "normalization": "NFKC, whitespace collapse, trim, Unicode casefold over title+abstract+claims",
        "metadata_coverage": {
            "query_rows": len(rows),
            "missing_split_query_rows": missing_ids,
            "query_schema_fields": query_schema,
            "exact_query_family_mapping_available": False,
            "source_publication_member_mapping_available": False,
            "benchmark_related_family_grouping_available": False,
        },
        "claim_boundary": (
            "The audit establishes exact query-record and normalized query-text overlap only. "
            "The available benchmark metadata does not map query records to query families or "
            "source-publication members, so it cannot establish family-level independence."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
