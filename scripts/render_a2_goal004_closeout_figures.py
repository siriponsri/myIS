"""Render A2 Goal 004 publication figures from the validated closeout projection."""

from __future__ import annotations

import argparse
from pathlib import Path

from myis_research.armindex.a2_goal004_closeout_figures import (
    render_a2_goal004_closeout_figures,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = render_a2_goal004_closeout_figures(args.repository_root)
    print(result["manifest_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
