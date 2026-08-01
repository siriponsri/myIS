"""Safe P2 readiness CLI; it intentionally has no measured-run command."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .p2.contracts import P2ContractError, load_p2_request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-p2")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "fixture-pilot"):
        command = subparsers.add_parser(name)
        command.add_argument("--request", type=Path, required=True)
        command.add_argument("--repository-root", type=Path, default=Path.cwd())
        command.add_argument("--require-stores", action="store_true")
        command.add_argument("--what-if", action="store_true")
    args = parser.parse_args(argv)
    try:
        request, profile = load_p2_request(
            args.request,
            args.repository_root,
            require_store=args.require_stores and args.command == "preflight",
        )
    except P2ContractError as error:
        parser.exit(3, f"P2 preflight blocked: {error}\n")
    root = args.repository_root.resolve()
    stores = {name: bool(os.environ.get(name)) for name in ("MYIS_STORE", "MYIS_MLFLOW_STORE")}
    payload = {
        "status": "fixture_only" if args.command == "fixture-pilot" else "ready_for_owner_preflight",
        "command": args.command,
        "what_if": bool(args.what_if),
        "phase_id": request["phase_id"],
        "arm": request["arm"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "runtime": profile.payload["runtime"],
        "resources": profile.payload["resources"],
        "runtime_pilot_status": "declared_not_measured" if args.command == "fixture-pilot" else "preflight_only",
        "selection_access": 0,
        "stores_configured": stores,
        "repository_root": str(root),
        "measured_execution": False,
    }
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
