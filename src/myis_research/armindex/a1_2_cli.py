"""Dedicated CLI for the versioned A1.2 contract scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .a1_2_contract import materialize_a1_2_scaffold, validate_a1_2_scaffold
from .a1_2_preflight import run_a1_2_preflight, write_preflight_receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2")
    parser.add_argument("command", choices=["materialize", "validate", "preflight"])
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--owner-input-root", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    if args.command == "preflight":
        result = run_a1_2_preflight(root, args.owner_input_root)
        receipt = write_preflight_receipt(root, result, args.receipt)
        output = dict(result.receipt)
        try:
            output["receipt"] = str(receipt.relative_to(root))
        except ValueError:
            output["receipt"] = str(receipt)
        print(json.dumps(output, ensure_ascii=True, sort_keys=True))
        return 0 if result.status == "passed_pending_owner_adoption" else 3
    result = materialize_a1_2_scaffold(root) if args.command == "materialize" else validate_a1_2_scaffold(root)
    print(json.dumps(result.summary(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
