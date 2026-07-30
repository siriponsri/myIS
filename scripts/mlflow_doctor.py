"""Fail-closed doctor for the SCOPE MLflow projection contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.mlflow_mirror import EXPERIMENTS, SCOPE_AUTOINDEX_EXPERIMENT


def doctor(repository_root: Path, store_root: Path | None = None) -> dict[str, object]:
    root = repository_root.resolve()
    checks = {
        "campaign_control": (root / "control/campaigns/scope-autoindex-v1.yaml").is_file(),
        "read_model": (root / "projections/read-model/read-model.v1.json").is_file(),
        "scope_experiment_declared": SCOPE_AUTOINDEX_EXPERIMENT in EXPERIMENTS,
        "store_external": bool(store_root and store_root.resolve() != root and root not in store_root.resolve().parents),
    }
    return {"schema_version": "myis.mlflow-doctor.v1", "status": "PASS" if all(checks.values()) else "BLOCKED", "checks": checks, "experiments": list(EXPERIMENTS)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--store-root", type=Path)
    args = parser.parse_args(argv)
    result = doctor(args.repository_root, args.store_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
