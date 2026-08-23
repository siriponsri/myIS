"""Run the CPU-local portion of the hash-bound A7 diagnosis.

Inputs remain in Owner Store.  ``--output-root`` must be an aggregate-safe
project location outside Owner Store and protected directories.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.a7_diagnosis import diagnose, write_public_outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--token-map", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--execution-config", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    receipt, csv_rows = diagnose(
        pool_path=args.pool, relations_path=args.relations, token_map_path=args.token_map,
        evaluation_path=args.evaluation, execution_config_path=args.execution_config,
    )
    write_public_outputs(receipt=receipt, csv_rows=csv_rows, output_root=args.output_root)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": receipt["receipt_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
