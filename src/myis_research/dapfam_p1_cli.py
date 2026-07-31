"""Console entrypoint for the pinned offline DAPFAM P1 CPU workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .dapfam_p1 import DapfamP1Error, import_p1_package, prepare_request, run_p1
from .progress import DEFAULT_HEARTBEAT_SECONDS


def _default_root(name: str) -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "myIS" / name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-p1-dapfam")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="create a hash-only request and protected split commitment")
    prepare.add_argument("--cache-root", type=Path, required=True)
    prepare.add_argument("--evidence-root", type=Path, default=_default_root("p1-evidence"))

    run = commands.add_parser("run", help="run R0 and R0-W against train/selection only")
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--cache-root", type=Path, required=True)
    run.add_argument("--index-root", type=Path, default=_default_root("p1-cpu-store"))
    run.add_argument("--evidence-root", type=Path, default=_default_root("p1-evidence"))
    run.add_argument(
        "--progress-interval-seconds",
        type=float,
        default=DEFAULT_HEARTBEAT_SECONDS,
        help="structured heartbeat interval for non-interactive execution",
    )

    import_command = commands.add_parser("import", help="import an accepted aggregate package into Git")
    import_command.add_argument("--request", type=Path, required=True)
    import_command.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repository_root.resolve()
    try:
        if args.command == "prepare":
            request_path, split_path = prepare_request(args.cache_root, root, args.evidence_root)
            result = {
                "status": "PASS",
                "request": str(request_path),
                "protected_split": str(split_path),
                "protected_payloads_emitted_to_git": False,
            }
        elif args.command == "run":
            receipt_path = run_p1(
                args.request,
                args.cache_root,
                root,
                args.index_root,
                args.evidence_root,
                progress_interval_seconds=args.progress_interval_seconds,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            result = {
                "status": "accepted",
                "request_id": receipt["request_id"],
                "receipt": str(receipt_path),
                "receipt_sha256": receipt["receipt_sha256"],
                "metric_rows": len(receipt["metrics"]),
            }
        else:
            imported = import_p1_package(args.request, args.receipt, root)
            result = {
                "status": "PASS",
                "package": str(imported["package_path"]),
                "package_sha256": imported["package"]["package_sha256"],
                "manifest_count": len(imported["manifests"]),
                "validation_report_count": len(imported["reports"]),
            }
    except (DapfamP1Error, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
