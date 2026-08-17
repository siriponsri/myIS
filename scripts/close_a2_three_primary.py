"""Close A2 under the Owner-approved three-primary amendment.

This script reads only aggregate-safe receipt objects and writes only new,
append-only closeout artifacts below an Owner-local output directory.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from myis_research.armindex.a2_three_primary_closeout import (
    build_three_primary_closeout,
    build_three_primary_coverage,
    build_three_primary_terminal_checkpoint,
)
from myis_research.kernel.canonical import file_sha256
from myis_research.protection import assert_aggregate_only


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise SystemExit(f"{role} must be an object")
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise SystemExit(f"{role} contains protected content") from error
    return value


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise SystemExit(f"refusing to overwrite {path}")
    path.write_text(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--receipt-directory", required=True, type=Path)
    parser.add_argument("--safe-return-receipt", required=True, type=Path)
    parser.add_argument("--aggregate-accounting-summary", required=True, type=Path)
    parser.add_argument("--worker-reap-summary", required=True, type=Path)
    parser.add_argument("--budget-cap-summary", required=True, type=Path)
    parser.add_argument("--dormant-repair-manifest", required=True, type=Path)
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = args.repository_root.resolve()
    amendment = _load(root / "control/armindex/a2/a2-goal004-three-primary-amendment.v1.json", role="amendment")
    receipt_directory = args.receipt_directory.resolve()
    receipts = {
        path_value.stem: _load(path_value, role="candidate receipt")
        for path_value in sorted(receipt_directory.glob("*.json"))
    }
    candidate_receipts = {value.get("candidate_id"): value for value in receipts.values()}
    if None in candidate_receipts or len(candidate_receipts) != len(receipts):
        raise SystemExit("receipt directory contains an invalid or duplicate candidate receipt")
    safe_return = _load(args.safe_return_receipt.resolve(), role="safe-return receipt")
    accounting = _load(args.aggregate_accounting_summary.resolve(), role="aggregate accounting summary")
    workers = _load(args.worker_reap_summary.resolve(), role="worker-reap summary")
    budget = _load(args.budget_cap_summary.resolve(), role="budget cap summary")
    dormant_repair = _load(args.dormant_repair_manifest.resolve(), role="dormant-repair manifest")

    coverage = build_three_primary_coverage(root, receipts_by_candidate=candidate_receipts)
    terminal = build_three_primary_terminal_checkpoint(root, amendment=amendment, safe_return_receipt=safe_return)
    closeout = build_three_primary_closeout(
        root,
        amendment=amendment,
        coverage=coverage,
        safe_return_receipt=safe_return,
        terminal_checkpoint=terminal,
        aggregate_accounting_summary=accounting,
        worker_reap_summary=workers,
        dormant_repair_manifest_file_sha256=file_sha256(args.dormant_repair_manifest.resolve()),
        aggregate_accounting_summary_sha256=file_sha256(args.aggregate_accounting_summary.resolve()),
        worker_reap_summary_sha256=file_sha256(args.worker_reap_summary.resolve()),
        budget_cap_summary=budget,
        budget_cap_summary_sha256=file_sha256(args.budget_cap_summary.resolve()),
        claim_evidence_pointers=[
            "docs/goal/A2_PER_ARM_AUTOINDEX_goal_004.md",
            "control/armindex/a2/a2-goal004-three-primary-amendment.v1.json",
        ],
    )
    result = {
        "status": closeout["status"],
        "closeout_receipt_sha256": closeout["receipt_sha256"],
        "coverage_sha256": coverage["coverage_sha256"],
        "terminal_checkpoint_sha256": terminal["checkpoint_sha256"],
        "primary_winner_arms": list(closeout["primary_winner_receipt_sha256s"]),
        "diagnostic_no_winner_arms": list(closeout["diagnostic_no_winner_receipt_sha256s"]),
    }
    if args.validate_only:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    if args.output_directory is None:
        raise SystemExit("--output-directory is required unless --validate-only is set")
    output = args.output_directory.resolve()
    if output.exists():
        raise SystemExit("closeout output directory already exists")
    output.mkdir(parents=True)
    _write_new(output / "three-primary-coverage.receipt.v1.json", coverage)
    _write_new(output / "three-primary-terminal.checkpoint.v1.json", terminal)
    _write_new(output / "a2-execution-closeout.receipt.v2.json", closeout)
    for arm_id, value in coverage["primary_winner_receipts"].items():
        _write_new(output / f"{arm_id.lower()}-winner.receipt.v1.json", value)
    for arm_id, value in coverage["diagnostic_no_winner_receipts"].items():
        _write_new(output / f"{arm_id.lower()}-diagnostic-no-winner.receipt.v1.json", value)
    print(json.dumps({**result, "output_directory": str(output)}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
