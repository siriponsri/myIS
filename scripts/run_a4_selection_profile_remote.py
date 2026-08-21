"""Run one frozen A4 profile over Selection-125 on the authorized worker."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

# The measured dense adapter fail-closes unless offline mode is active.  Set
# these in the entrypoint as well as the supervisor environment so the guard
# remains effective when the worker is launched through a remote shell.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from myis_research.armindex.a4_remote_ranker import run_a4_selection_profile_ranker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    run_a4_selection_profile_ranker(args.request, assets_root=args.assets_root, result_path=args.result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
