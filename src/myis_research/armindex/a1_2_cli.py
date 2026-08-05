"""Dedicated CLI for the versioned A1.2 contract scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .a1_2_contract import materialize_a1_2_scaffold, validate_a1_2_scaffold


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2")
    parser.add_argument("command", choices=["materialize", "validate"])
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    result = (
        materialize_a1_2_scaffold(root)
        if args.command == "materialize"
        else validate_a1_2_scaffold(root)
    )
    print(json.dumps(result.summary(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
