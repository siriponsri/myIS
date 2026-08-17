"""Validate the local-only extended A3 preparation bundle without provider access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a3_execution_preparation import (
    build_a3_pending_preflight,
    validate_a3_budget_extension,
    validate_a3_preparation_authority,
    validate_a3_preparation_manifest,
)


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repository_root.resolve()
    budget = validate_a3_budget_extension(
        _load(root / "control/budgets/armindex-budget-extension-a3-v1.json")
    )
    authority = validate_a3_preparation_authority(
        _load(root / "control/armindex/a3/a3-five-arm-preparation-authority.v1.json")
    )
    manifest = validate_a3_preparation_manifest(
        _load(root / "control/armindex/a3/a3-five-arm-preparation-manifest.v1.json")
    )
    print(json.dumps(build_a3_pending_preflight(budget, authority, manifest), sort_keys=True))


if __name__ == "__main__":
    main()
