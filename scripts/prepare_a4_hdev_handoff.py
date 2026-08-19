"""Validate and materialize the protected HDEV handoff for one A4 attempt."""

from __future__ import annotations

import argparse
from pathlib import Path

from myis_research.armindex.a4_hdev_materializer import materialize_a4_hdev_handoff


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--split-receipt", type=Path, required=True)
    parser.add_argument("--train-package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.train_package.resolve(strict=True)
    receipt = materialize_a4_hdev_handoff(
        membership_path=args.membership,
        split_receipt_path=args.split_receipt,
        train_scope_path=root / "train-scope.json",
        train_package_receipt_path=root / "A3_TRAIN250_OWNER_PACKAGE_RECEIPT.json",
        train_queries_path=root / "inputs" / "queries.jsonl",
        train_membership_path=root / "inputs" / "membership.jsonl",
        train_qrels_path=root / "inputs" / "qrels.jsonl",
        evaluator_relations_path=root / "inputs" / "evaluator-relations.arrow",
        output_root=args.output,
        owner_store_root=args.owner_store_root,
        attempt_id=args.attempt_id,
    )
    print(
        {
            "status": receipt["status"],
            "attempt_id": receipt["attempt_id"],
            "hdev_query_count": receipt["hdev_query_count"],
            "receipt_sha256": receipt["receipt_sha256"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
