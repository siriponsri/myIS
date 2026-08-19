"""Evaluate returned A4 HDEV rankings inside Owner-local storage only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a2_owner_local_engine import FamilyRank, _metrics
from myis_research.armindex.a4_evaluator import evaluate_a4_profile_owner_local
from myis_research.kernel.canonical import canonical_json, file_sha256


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--profile-registry", type=Path, required=True)
    parser.add_argument("--hdev-queries", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--evaluator-binding", required=True)
    parser.add_argument("--hdev-commitment", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    package = json.loads(args.package.read_text(encoding="utf-8"))
    registry = json.loads(args.profile_registry.read_text(encoding="utf-8"))
    profile = next(row for row in registry["profiles"] if row["profile_id"] == args.profile)
    hdev_tokens = {row["work_token"] for row in _jsonl(args.hdev_queries)}
    qrels = {row["work_token"]: row["relevance"] for row in _jsonl(args.qrels) if row["work_token"] in hdev_tokens}
    membership = {row["work_token"]: row["eligible_out"] for row in _jsonl(args.membership) if row["work_token"] in hdev_tokens}
    if set(qrels) != hdev_tokens or set(membership) != hdev_tokens:
        raise ValueError("HDEV protected evaluator coverage is incomplete")

    def metric_evaluator(rankings: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
        typed = {
            token: tuple(FamilyRank(row["family_token"], int(row["rank"]), float(row["score"])) for row in rows)
            for token, rows in rankings.items()
        }
        recall, ndcg100, ndcg10 = _metrics(typed, qrels, {token for token, eligible in membership.items() if eligible})
        return {"recall_at_100": recall, "ndcg_at_100": ndcg100, "ndcg_at_10": ndcg10}

    result = evaluate_a4_profile_owner_local(
        profile,
        package,
        evaluator_binding_sha256=args.evaluator_binding,
        hdev_commitment_sha256=args.hdev_commitment,
        metric_evaluator=metric_evaluator,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(canonical_json({"status": result["status"], "profile_id": result["profile_id"], "receipt_sha256": result["receipt_sha256"], "qrels_sha256": file_sha256(args.qrels), "membership_sha256": file_sha256(args.membership)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
