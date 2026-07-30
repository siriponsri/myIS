"""Read-only validation of an Owner-local F1/G1 preparation bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from myis_research.harness.dapfam_contracts import validate_owner_value_batch

from prepare_f1_g1 import REPOSITORY_ROOT, default_owner_root


def validate(owner_root: Path) -> dict[str, object]:
    root = owner_root.resolve(strict=True)
    projection_path = root / "safe" / "projections" / "current.json"
    projection = json.loads(projection_path.read_text(encoding="utf-8"))
    if projection.get("schema_version") != "myis.f1-g1-safe-projection.v1":
        raise ValueError("safe projection schema is invalid")
    proposal = projection["proposal_sha256"]
    batch_path = root / "safe" / "batches" / f"g1-owner-value-batch-{proposal}.json"
    batch = validate_owner_value_batch(json.loads(batch_path.read_text(encoding="utf-8")))
    if _sha256(batch_path) != projection["safe_batch_sha256"]:
        raise ValueError("safe batch hash does not match the current projection")
    sealed_path = root / "sealed" / "splits" / proposal / "membership.json"
    sealed = json.loads(sealed_path.read_text(encoding="utf-8"))
    memberships = sealed.get("membership", {})
    counts = {role: len(ids) for role, ids in memberships.items()}
    if counts != batch.split.counts:
        raise ValueError("sealed membership counts do not match the safe batch")
    if len({query_id for ids in memberships.values() for query_id in ids}) != 1247:
        raise ValueError("sealed membership is not a disjoint 1,247-query partition")
    safe_text = batch_path.read_text(encoding="utf-8") + projection_path.read_text(encoding="utf-8")
    private = json.loads((root / "config" / "owner-paths.json").read_text(encoding="utf-8"))
    if any(path and path in safe_text for path in private["sources"].values()):
        raise ValueError("safe artifacts expose an Owner-local absolute path")
    forbidden = ('"membership"', '"query_ids"', '"per_query"', '"metrics"', '"results"')
    if any(token in safe_text for token in forbidden):
        raise ValueError("safe artifacts contain a protected or measured field")
    return {
        "status": "PASS",
        "proposal_sha256": proposal,
        "safe_batch_sha256": projection["safe_batch_sha256"],
        "query_count": 1247,
        "split_counts": counts,
        "gate_status": "pending",
        "scientific_run": False,
        "scientific_metric_count": 0,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Owner-local F1/G1 preparation bundle")
    parser.add_argument("--owner-root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.owner_root or default_owner_root(REPOSITORY_ROOT))
    except Exception as error:
        result = {"status": "FAIL", "reason": str(error), "error_type": type(error).__name__}
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
