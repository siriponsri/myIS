"""Materialize the adopted P2 measured-control artifacts deterministically."""

from __future__ import annotations

import argparse
from pathlib import Path

from myis_research.kernel.canonical import canonical_json
from myis_research.p2.base_candidates import (
    ADAPTIVE_POLICY_URI,
    BASE_SET_URI,
    PROPOSER_CONTRACT_URI,
    build_adaptive_policy,
    build_base_candidate_set,
    build_proposer_contract,
)
from myis_research.p2.measured_contracts import validate_measured_artifact


def build(repository_root: Path, *, check: bool) -> list[str]:
    root = Path(repository_root).resolve()
    artifacts = {
        BASE_SET_URI: build_base_candidate_set(root, committed_hashes=False),
        ADAPTIVE_POLICY_URI: build_adaptive_policy(),
        PROPOSER_CONTRACT_URI: build_proposer_contract(),
    }
    changed: list[str] = []
    for relative, payload in artifacts.items():
        validate_measured_artifact(payload, root)
        encoded = canonical_json(payload) + "\n"
        target = root / relative
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current == encoded:
            continue
        changed.append(relative)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(encoded, encoding="utf-8", newline="\n")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    changed = build(args.repository_root, check=args.check)
    if changed:
        print("P2 measured controls differ: " + ", ".join(changed))
        return 1 if args.check else 0
    print("P2 measured controls are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
