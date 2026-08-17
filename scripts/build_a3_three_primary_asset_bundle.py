"""Create the opaque, Train-250-only A3 runtime asset archive in an Owner Store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a3_three_primary_asset_bundle import (
    build_a3_three_primary_asset_bundle,
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON input must be an object")
    return value


def _mapping(values: list[str], *, role: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{role} must use ARM-ID=PATH")
        arm_id, raw_path = value.split("=", 1)
        result[arm_id] = Path(raw_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-build-a3-three-primary-asset-bundle")
    parser.add_argument("--stage-source-root", required=True, type=Path)
    parser.add_argument("--runtime-bindings", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--queries", required=True, type=Path)
    parser.add_argument("--train-scope", required=True, type=Path)
    parser.add_argument("--winner-program", action="append", default=[])
    parser.add_argument("--target-model", action="append", default=[])
    args = parser.parse_args()
    receipt = build_a3_three_primary_asset_bundle(
        args.stage_source_root,
        runtime_bindings=_load(args.runtime_bindings),
        corpus_path=args.corpus,
        queries_path=args.queries,
        train_scope=_load(args.train_scope),
        winner_program_paths=_mapping(args.winner_program, role="winner program"),
        target_model_directories=_mapping(args.target_model, role="target model"),
    )
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
