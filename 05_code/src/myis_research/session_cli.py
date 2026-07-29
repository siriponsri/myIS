"""Low-dev commands for validating and finding immutable session capsules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .session_capsules import (
    SessionCapsuleValidationError,
    latest_valid_session,
    validate_all_session_capsules,
    validate_session_capsule,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-sessions", description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one capsule against its recorded Git revision")
    validate.add_argument("capsule", type=Path)
    commands.add_parser("validate-all", help="classify all capsules and correction coverage")
    latest = commands.add_parser("latest-valid", help="return only the latest individually valid capsule")
    latest.add_argument("--phase")
    latest.add_argument("--task")
    latest.add_argument("--gate")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repository_root.resolve()
    try:
        if args.command == "validate":
            capsule = args.capsule if args.capsule.is_absolute() else root / args.capsule
            result = validate_session_capsule(capsule, root).as_dict()
        elif args.command == "validate-all":
            result = validate_all_session_capsules(root)
        else:
            result = latest_valid_session(root, phase_id=args.phase, task_id=args.task, gate_id=args.gate)
            if result is None:
                result = {"schema_version": "myis.session-capsule-latest.v1", "status": "NOT_FOUND"}
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 1
            result = {"schema_version": "myis.session-capsule-latest.v1", "status": "PASS", "session": result}
    except SessionCapsuleValidationError as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
