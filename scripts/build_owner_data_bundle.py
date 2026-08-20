"""Build or validate the hash-only canonical Owner Data Bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.owner_data_bundle import build_bundle, validate_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--owner-store-root", type=Path)
    check = sub.add_parser("validate")
    check.add_argument("--bundle", type=Path, required=True)
    check.add_argument("--owner-store-root", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        receipt = build_bundle(output_root=args.output, owner_store_root=args.owner_store_root)
    else:
        receipt = validate_bundle(args.bundle, owner_store_root=args.owner_store_root)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": receipt["receipt_sha256"], "selection_accesses": receipt["selection_accesses"], "final_accesses": receipt["final_accesses"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
