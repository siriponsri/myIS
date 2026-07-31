"""Maintain the v2 MLflow evidence archive without accessing protected inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.mlflow_archive import MLflowEvidenceArchive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MLflow v2 archive maintenance")
    parser.add_argument("command", choices=("backup", "restore", "rebuild-plan"))
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--backup-id")
    parser.add_argument("--reason")
    parser.add_argument("--target-root", type=Path)
    args = parser.parse_args(argv)
    archive = MLflowEvidenceArchive(args.store_root)
    if args.command == "backup":
        if not args.backup_id:
            parser.error("backup requires --backup-id")
        result: object = {"status": "PASS", "backup": str(archive.backup(args.backup_id))}
    elif args.command == "restore":
        if not args.backup_id or not args.target_root:
            parser.error("restore requires --backup-id and --target-root")
        result = archive.restore_backup(args.backup_id, args.target_root)
    else:
        if not args.reason:
            parser.error("rebuild-plan requires --reason")
        result = archive.quarantine_and_rebuild_plan(args.reason)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
