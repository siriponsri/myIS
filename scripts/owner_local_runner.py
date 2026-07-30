"""Owner-controlled CPU runner for protected local inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.owner_local_runner import process


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-owner-local")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--aggregate-source", type=Path, help="deprecated and rejected; use --protected-root")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.aggregate_source is not None:
        parser.error("--aggregate-source is retired; pass --protected-root with local protected inputs")
    path = process(args.request, args.protected_root, args.receipt)
    print(json.dumps({"status": "accepted", "receipt": str(path)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
