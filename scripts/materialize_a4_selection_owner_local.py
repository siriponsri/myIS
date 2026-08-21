"""Materialize the hash-bound Selection-125 query input in Owner Store.

This command does not rank, evaluate, or open Selection.  It fails closed when
the complete canonical 1,247-query payload is not available.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.a4_selection_materializer import materialize_selection_inputs
from myis_research.kernel.canonical import canonical_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protected-split", type=Path, required=True)
    parser.add_argument("--source-queries", type=Path, required=True)
    parser.add_argument("--evaluator-relations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    owner_root = args.owner_store_root.resolve(strict=True)
    paths = [args.protected_split, args.source_queries, args.evaluator_relations, args.output]
    for path in paths:
        resolved = path.resolve()
        if resolved != owner_root and owner_root not in resolved.parents:
            raise ValueError(f"Selection path is outside Owner Store: {path}")
        if path.is_symlink():
            raise ValueError(f"Selection path cannot be a symlink: {path}")
    receipt = materialize_selection_inputs(
        protected_split_path=args.protected_split,
        source_queries_path=args.source_queries,
        evaluator_relations_path=args.evaluator_relations,
        output_root=args.output,
        owner_store_root=owner_root,
        attempt_id=args.attempt_id,
    )
    print(canonical_json({
        "status": receipt["status"],
        "receipt_sha256": receipt["receipt_sha256"],
        "selection_query_count": receipt["selection_query_count"],
        "selection_accesses": receipt["selection_accesses"],
        "final_accesses": receipt["final_accesses"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
