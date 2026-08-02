"""Fail-closed policy scans used by the CPU contract workflow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable


@dataclass(frozen=True)
class Scan:
    pattern: re.Pattern[str]
    targets: tuple[str, ...]
    suffixes: frozenset[str] | None
    failure_message: str
    allowed_lines: frozenset[tuple[str, str]] = frozenset()


POLICIES = {
    "p2-closure": (
        Scan(
            pattern=re.compile(r"final-872|D2_OPEN_FINAL|D3_SUBMIT_RELEASE"),
            targets=("src/myis_research/p2_cli.py",),
            suffixes=None,
            failure_message="P2 readiness CLI must not open final gates",
        ),
    ),
    "archive-runtime": (
        Scan(
            pattern=re.compile(r"archive/old-layout|archive\\old-layout|01_evidence"),
            targets=("src", "scripts", "dashboard"),
            suffixes=frozenset({".py", ".sh", ".js", ".html"}),
            failure_message="archive coupling or retired active path found",
            allowed_lines=frozenset(
                {
                    (
                        "src/myis_research/layout.py",
                        'FORBIDDEN_ACTIVE = ("00_governance", "01_evidence", "02_tracks", "03_experiments", "04_outputs", "05_code", "06_frontend", "07_obsidian_note")',
                    ),
                    (
                        "src/myis_research/layout.py",
                        'FORBIDDEN_ACTIVE = ("00_governance", "01_evidence", "02_tracks", "03_experiments", "04_outputs", "05_code", "06_frontend", "07_obsidian_note", "inbox")',
                    ),
                }
            ),
        ),
        Scan(
            pattern=re.compile(r"G[0-8]|F1/G1|Track [CS]"),
            targets=(
                "src/myis_research/dashboard/app.py",
                "src/myis_research/mlflow_mirror.py",
                "dashboard/index.html",
                "dashboard/assets",
            ),
            suffixes=frozenset({".py", ".js", ".html", ".css"}),
            failure_message="retired gate vocabulary found in active dashboard or MLflow runtime",
        ),
    ),
}


class PolicyScanError(RuntimeError):
    """Raised when a scan cannot inspect every required target."""


def _iter_files(root: Path, target_name: str, suffixes: frozenset[str] | None) -> Iterable[Path]:
    target = root / target_name
    if not target.exists():
        raise PolicyScanError(f"required scan target is missing: {target_name}")
    if target.is_symlink():
        raise PolicyScanError(f"required scan target must not be a symlink: {target_name}")
    if target.is_file():
        if suffixes is None or target.suffix in suffixes:
            yield target
        return
    if not target.is_dir():
        raise PolicyScanError(f"required scan target is not a regular file or directory: {target_name}")
    for path in sorted(target.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            continue
        if path.is_file() and (suffixes is None or path.suffix in suffixes):
            yield path


def run_policy(root: Path, policy_name: str) -> list[str]:
    findings: list[str] = []
    for scan in POLICIES[policy_name]:
        for target_name in scan.targets:
            for path in _iter_files(root, target_name, scan.suffixes):
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except (OSError, UnicodeError) as error:
                    relative = path.relative_to(root).as_posix()
                    raise PolicyScanError(f"cannot read required scan target: {relative}") from error
                relative = path.relative_to(root).as_posix()
                for line_number, line in enumerate(lines, start=1):
                    if scan.pattern.search(line) and (relative, line) not in scan.allowed_lines:
                        findings.append(f"{relative}:{line_number}:{line}")
        if findings:
            findings.append(scan.failure_message)
            break
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("policy", choices=sorted(POLICIES))
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    try:
        findings = run_policy(root, args.policy)
    except PolicyScanError as error:
        print(f"policy scan failed closed: {error}", file=sys.stderr)
        return 2
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    print(f"policy scan passed: {args.policy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
