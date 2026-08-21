"""Materialize protected Selection-125 qrels and OUT membership locally."""

from __future__ import annotations

import argparse
from pathlib import Path

from myis_research.armindex.a4_selection_evaluator_inputs import materialize_selection_evaluator_inputs
from myis_research.kernel.canonical import canonical_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-input-root", type=Path, required=True)
    parser.add_argument("--protected-split", type=Path, required=True)
    parser.add_argument("--evaluator-relations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    owner_root = args.owner_store_root.resolve(strict=True)
    for path in (args.selection_input_root, args.protected_split, args.evaluator_relations, args.output):
        resolved = path.resolve()
        if resolved != owner_root and owner_root not in resolved.parents:
            raise ValueError(f"Selection path is outside Owner Store: {path}")
        if path.is_symlink():
            raise ValueError(f"Selection path cannot be a symlink: {path}")
    receipt = materialize_selection_evaluator_inputs(
        selection_input_root=args.selection_input_root,
        protected_split_path=args.protected_split,
        evaluator_relations_path=args.evaluator_relations,
        output_root=args.output,
        owner_store_root=owner_root,
        attempt_id=args.attempt_id,
    )
    print(canonical_json({"status": receipt["status"], "receipt_sha256": receipt["receipt_sha256"], "selection_query_count": receipt["selection_query_count"], "out_query_count": receipt["out_query_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
