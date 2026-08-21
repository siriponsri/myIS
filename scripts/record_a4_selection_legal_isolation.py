"""Record an aggregate-only legal-transfer boundary for a fresh A4 attempt.

The legal benchmark assets are not present in the authorized stores at this
checkpoint.  The explicit UNSUPPORTED/NOT_RUN receipt preserves that negative
evidence without inventing metrics, touching patent data, or changing gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.a4_evaluator import build_legal_transfer_receipt
from myis_research.kernel.canonical import canonical_json, canonical_sha256


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--isolation-sha256")
    args = parser.parse_args()
    isolation_sha256 = args.isolation_sha256 or canonical_sha256(
        {
            "schema_version": "myis.armindex-a4-legal-transfer-isolation.v1",
            "target_domain": "legal_structured_retrieval",
            "mini_input": "absent_from_authorized_store",
            "patent_feedback": False,
            "protected_data_accessed": False,
        }
    )
    receipt = build_legal_transfer_receipt(
        attempt_id=args.attempt_id,
        mini_status="UNSUPPORTED",
        mini_metrics={
            "reason": "required LegalBench-RAG mini dataset/evaluator/runtime artifact is absent",
            "metric_status": "NOT_VERIFIED",
        },
        full_status="NOT_RUN",
        isolation_sha256=isolation_sha256,
        a5_reserve_intact=True,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refusing to overwrite {args.output}")
    args.output.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt_sha256": receipt["receipt_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
