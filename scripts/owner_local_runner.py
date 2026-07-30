"""Owner-controlled aggregate runner.

This process is intended to run from a protected directory outside the agent
workspace. It consumes hash-only requests and a precomputed aggregate source;
it never opens qrels, query IDs, membership, or per-query outcomes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.owner_local_runner import process


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-owner-local")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--aggregate-source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    path = process(args.request, args.aggregate_source, args.receipt)
    print(json.dumps({"status": "accepted", "receipt": str(path)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
