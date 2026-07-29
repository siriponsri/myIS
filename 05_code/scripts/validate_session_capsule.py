"""Validate one append-only myIS research-session capsule without writing it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from myis_research.session_capsules import SessionCapsuleValidationError, validate_session_capsule


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capsule", type=Path, help="repository-relative or absolute capsule path")
    arguments = parser.parse_args()
    path = arguments.capsule if arguments.capsule.is_absolute() else ROOT / arguments.capsule
    try:
        report = validate_session_capsule(path, ROOT)
    except SessionCapsuleValidationError as error:
        print(f"SESSION_CAPSULE_VALID=false: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report.as_dict(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
