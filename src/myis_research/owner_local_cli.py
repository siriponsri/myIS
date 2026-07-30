"""Console entrypoint for the owner-local protected runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .owner_local_runner import process


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-owner-local")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--legacy-root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--aggregate-source", type=Path, help="deprecated and rejected; use --protected-root")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.aggregate_source is not None:
        parser.error("--aggregate-source is retired; pass --protected-root with local protected inputs")
    path = process(
        args.request,
        args.protected_root,
        args.receipt,
        store_root=args.store_root,
        legacy_root=args.legacy_root,
        repository_root=args.repository_root,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("status") == "blocked":
        print(
            json.dumps(
                {
                    "status": "P1_BLOCKED_WITH_EVIDENCE",
                    "receipt": str(path),
                    "blockers": receipt.get("blockers", []),
                },
                ensure_ascii=True,
            ),
            file=sys.stderr,
        )
        return 3
    print(json.dumps({"status": "accepted", "receipt": str(path)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
