"""Run the independent aggregate-only integrity audit for amended A2 closeout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.a2_three_primary_closeout import audit_three_primary_closeout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--owner-attempt-root", required=True, type=Path)
    parser.add_argument("--amendment", required=True, type=Path)
    parser.add_argument("--closeout", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--safe-return", required=True, type=Path)
    parser.add_argument("--terminal-checkpoint", required=True, type=Path)
    parser.add_argument("--aggregate-accounting-summary", required=True, type=Path)
    parser.add_argument("--worker-reap-summary", required=True, type=Path)
    parser.add_argument("--budget-cap-summary", required=True, type=Path)
    parser.add_argument("--dormant-repair-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise SystemExit("audit output already exists or is unsafe")
    audit = audit_three_primary_closeout(
        args.repository_root,
        owner_attempt_root=args.owner_attempt_root,
        amendment_path=args.amendment,
        closeout_path=args.closeout,
        coverage_path=args.coverage,
        safe_return_path=args.safe_return,
        terminal_checkpoint_path=args.terminal_checkpoint,
        aggregate_accounting_summary_path=args.aggregate_accounting_summary,
        worker_reap_summary_path=args.worker_reap_summary,
        budget_cap_summary_path=args.budget_cap_summary,
        dormant_repair_manifest_path=args.dormant_repair_manifest,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(audit, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"status": audit["status"], "audit_sha256": audit["audit_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
