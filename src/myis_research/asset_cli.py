"""Command-line access to the governed reusable asset registry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .asset_registry import (
    MAP_RELATIVE_PATH,
    AssetRegistryError,
    canonical_json,
    load_registry,
    query_assets,
    render_asset_map,
    repository_root,
    validate_sources,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myis-assets", description="Query and validate reusable Research assets"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    query = subparsers.add_parser("query", help="query the reusable asset registry")
    query.add_argument("--task")
    query.add_argument("--disposition")
    query.add_argument("--asset-id")
    query.add_argument("--json", action="store_true")
    validate = subparsers.add_parser("validate", help="validate source pointers and provenance")
    validate.add_argument("--mode", choices=("quick", "full"), required=True)
    validate.add_argument("--asset-id", action="append", default=[])
    validate.add_argument("--approval-record", type=Path)
    validate.add_argument("--receipt", type=Path)
    asset_map = subparsers.add_parser("map", help="write or verify the generated Phase/Task map")
    asset_map.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = repository_root()
        registry = load_registry(root)
        if args.command == "query":
            assets = query_assets(
                registry,
                asset_id=args.asset_id,
                task_id=args.task,
                disposition=args.disposition,
            )
            if args.json:
                sys.stdout.write(canonical_json(list(assets)))
            else:
                for asset in assets:
                    print(
                        f"{asset['asset_id']} | {asset['disposition']} | {asset['kind']} | "
                        f"tasks={','.join(asset.get('task_ids', asset.get('allowed_phases', [])))} | "
                        f"copy={asset['copy_mode']}"
                    )
            return 0
        if args.command == "validate":
            report = validate_sources(
                registry,
                root,
                mode=args.mode,
                asset_ids=args.asset_id,
                approval_record=args.approval_record,
                receipt=args.receipt,
            )
            sys.stdout.write(canonical_json(report.as_dict()))
            return 0 if report.ok else 1
        rendered = render_asset_map(registry, root)
        map_path = root / MAP_RELATIVE_PATH
        if args.check:
            if not map_path.is_file() or map_path.read_text(encoding="utf-8") != rendered:
                print(f"generated map drift: {MAP_RELATIVE_PATH.as_posix()}", file=sys.stderr)
                return 1
            print(f"map is current: {MAP_RELATIVE_PATH.as_posix()}")
            return 0
        map_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {MAP_RELATIVE_PATH.as_posix()}")
        return 0
    except (AssetRegistryError, PermissionError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
