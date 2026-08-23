"""Prepare the committed full query view as opaque Owner-Store input.

Only query text and deterministic opaque tokens leave the Owner Store. Raw
query identifiers, membership, and qrels are never written to the output.
"""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import pyarrow as pa

from myis_research.kernel.canonical import canonical_sha256


EXPECTED = 1_247


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split())


def prepare(source: Path, output: Path, receipt: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    with source.open("rb") as handle:
        reader = pa.ipc.open_stream(handle)
        for index, batch in enumerate(reader):
            columns = {name: batch.column(name) for name in batch.schema.names}
            for offset in range(batch.num_rows):
                raw_id = str(columns["query_id"][offset].as_py())
                token = "q-" + sha256(raw_id.encode("utf-8")).hexdigest()
                if token in seen:
                    raise ValueError("duplicate opaque query token")
                seen.add(token)
                text = " ".join(
                    part for part in (
                        _norm(columns.get("title_en")[offset].as_py() if "title_en" in columns else ""),
                        _norm(columns.get("abstract_en")[offset].as_py() if "abstract_en" in columns else ""),
                        _norm(columns.get("claims_text")[offset].as_py() if "claims_text" in columns else ""),
                    ) if part
                )
                if not text:
                    raise ValueError(f"empty query text at index {index + offset}")
                rows.append({"opaque_query_token": token, "query_text": text, "query_index": len(rows)})
    if len(rows) != EXPECTED:
        raise ValueError(f"expected {EXPECTED} queries, observed {len(rows)}")
    body = {
        "schema_version": "myis.armindex-a6-opaque-query-source.v1",
        "query_count": len(rows),
        "query_source_sha256": canonical_sha256(rows),
        "protected_payload_included": True,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or receipt.exists():
        raise ValueError("refusing to overwrite immutable A6 query staging")
    output.write_text("".join(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="ascii")
    receipt.write_text(json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    return {**body, "receipt_sha256": canonical_sha256(body)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output, args.receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
