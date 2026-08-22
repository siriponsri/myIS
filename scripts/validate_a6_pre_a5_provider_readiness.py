"""Validate the non-executable A6 v2 provider-readiness plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a6_materialization import validate_a6_pre_a5_provider_readiness_plan


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json"
DEFAULT_PLAN = ROOT / "control/armindex/a6/a6-pre-a5-provider-readiness.v2.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    args = parser.parse_args()
    plan = validate_a6_pre_a5_provider_readiness_plan(load_json(args.plan), load_json(args.contract))
    print(json.dumps({"status": "PASS_A6_PRE_A5_PROVIDER_READINESS_VALIDATED", "plan_sha256": plan["plan_sha256"], "execution_permitted": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
