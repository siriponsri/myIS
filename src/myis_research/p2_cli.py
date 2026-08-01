"""Safe P2 readiness CLI; it intentionally has no measured-run command."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .p2.contracts import P2ContractError, load_p2_request
from .p2.fixture import (
    DEFAULT_RECEIPT_PATH,
    P2FixtureError,
    fixture_what_if,
    run_fixture_pilot,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-p2")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--request", type=Path, required=True)
    preflight.add_argument("--repository-root", type=Path, default=Path.cwd())
    preflight.add_argument("--require-stores", action="store_true")
    preflight.add_argument("--what-if", action="store_true")
    fixture = subparsers.add_parser("fixture-pilot")
    fixture.add_argument("--repository-root", type=Path, default=Path.cwd())
    fixture.add_argument("--output", type=Path)
    fixture.add_argument("--require-stores", action="store_true")
    fixture.add_argument("--what-if", action="store_true")
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    if args.command == "fixture-pilot":
        output = args.output or root / DEFAULT_RECEIPT_PATH
        if args.require_stores:
            parser.exit(3, "P2 fixture blocked: --require-stores is forbidden for fixture execution\n")
        try:
            payload = (
                fixture_what_if(root, output)
                if args.what_if
                else run_fixture_pilot(root, output)
            )
        except (P2ContractError, P2FixtureError) as error:
            parser.exit(3, f"P2 fixture blocked: {error}\n")
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
        return 0
    try:
        request, profile = load_p2_request(
            args.request,
            root,
            require_store=args.require_stores,
        )
    except P2ContractError as error:
        parser.exit(3, f"P2 preflight blocked: {error}\n")
    stores = {name: bool(os.environ.get(name)) for name in ("MYIS_STORE", "MYIS_MLFLOW_STORE")}
    payload = {
        "status": "ready_for_owner_preflight",
        "command": args.command,
        "what_if": bool(args.what_if),
        "phase_id": request["phase_id"],
        "arm": request["arm"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "runtime": profile.payload["runtime"],
        "resources": profile.payload["resources"],
        "runtime_pilot_status": "preflight_only",
        "selection_access": 0,
        "stores_configured": stores,
        "repository_root": str(root),
        "measured_execution": False,
    }
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
