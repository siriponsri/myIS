"""Validate the local-only amended A3 preparation package without provider access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a3_three_primary_preparation import (
    build_three_primary_pending_preflight,
    validate_three_primary_authority,
    validate_three_primary_budget_extension,
    validate_three_primary_manifest,
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repository_root.resolve()
    budget = validate_three_primary_budget_extension(
        _load(root / "control/budgets/armindex-budget-extension-a3-three-primary.v1.json")
    )
    authority = validate_three_primary_authority(
        _load(root / "control/armindex/a3/a3-three-primary-preparation-authority.v1.json")
    )
    manifest = validate_three_primary_manifest(
        _load(root / "control/armindex/a3/a3-three-primary-preparation-manifest.v1.json"),
        authority=authority,
    )
    print(json.dumps(build_three_primary_pending_preflight(budget, authority, manifest), sort_keys=True))


if __name__ == "__main__":
    main()
