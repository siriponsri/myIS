"""Build an Owner-Store-only bridge between canonical A6 bytes and A5 export bytes.

The two materializations use different opaque token namespaces.  This receipt
proves that the frozen retrieval fields are the same multiset of records while
keeping byte/token hashes explicit and never exporting protected identifiers.
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any


FIELDS = ("title_en", "abstract_en", "claims_text", "claims", "publication_ordinal")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("corpus JSONL is empty or malformed")
    return rows


def content_hash(rows: list[dict[str, Any]]) -> str:
    records = [canonical({field: row.get(field) for field in FIELDS}) for row in rows]
    records.sort()
    digest = sha256()
    for record in records:
        digest.update(len(record).to_bytes(8, "big"))
        digest.update(record)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--a5", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    canonical_rows = load(args.canonical)
    a5_rows = load(args.a5)
    if len(canonical_rows) != 45336 or len(a5_rows) != 45336:
        raise ValueError("A6 source bridge requires exactly 45,336 rows in both inputs")
    canonical_content = content_hash(canonical_rows)
    a5_content = content_hash(a5_rows)
    if canonical_content != a5_content:
        raise ValueError("A5 and canonical source content multisets differ")
    body = {
        "schema_version": "myis.armindex-a6-source-equivalence-bridge.v1",
        "status": "PASS_A6_SOURCE_SEMANTIC_EQUIVALENCE_BRIDGE",
        "claim_boundary": "same frozen retrieval-field record multiset; opaque token namespaces differ and are regenerated for A6; no A5 metric reinterpretation",
        "canonical_source_sha256": sha256(args.canonical.read_bytes()).hexdigest(),
        "a5_materialized_source_sha256": sha256(args.a5.read_bytes()).hexdigest(),
        "canonical_row_count": len(canonical_rows),
        "a5_row_count": len(a5_rows),
        "frozen_field_set": list(FIELDS),
        "canonical_content_multiset_sha256": canonical_content,
        "a5_content_multiset_sha256": a5_content,
        "token_namespace_equivalent": False,
        "protected_payload_included": False,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    result = {**body, "bridge_sha256": sha256(canonical(body)).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError("refusing to overwrite immutable bridge")
    args.output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
