"""Validate the minimal active layout and archive cutover."""

from __future__ import annotations

import json
from pathlib import Path

from myis_research.layout import validate


if __name__ == "__main__":
    result = validate(Path.cwd())
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
