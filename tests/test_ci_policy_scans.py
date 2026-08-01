from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / ".github/scripts/check_policy.py"


def _run(root: Path, policy: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), "--repository-root", str(root), policy],
        check=False,
        capture_output=True,
        text=True,
    )


def _archive_fixture(root: Path) -> None:
    for path in (
        root / "src/myis_research/dashboard/app.py",
        root / "src/myis_research/mlflow_mirror.py",
        root / "scripts/placeholder.py",
        root / "dashboard/index.html",
        root / "dashboard/assets/app.js",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("active content\n", encoding="utf-8")


def test_repository_policy_scans_pass() -> None:
    for policy in ("p2-closure", "archive-runtime"):
        completed = _run(ROOT, policy)
        assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("relative_path", "forbidden"),
    [
        ("src/active.py", "archive/old-layout"),
        ("src/myis_research/dashboard/app.py", "Track S"),
    ],
)
def test_archive_policy_rejects_forbidden_patterns(
    tmp_path: Path,
    relative_path: str,
    forbidden: str,
) -> None:
    _archive_fixture(tmp_path)
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(forbidden + "\n", encoding="utf-8")

    completed = _run(tmp_path, "archive-runtime")

    assert completed.returncode == 1
    assert forbidden in completed.stderr


def test_archive_policy_allows_only_the_exact_layout_declaration(tmp_path: Path) -> None:
    _archive_fixture(tmp_path)
    target = tmp_path / "src/myis_research/layout.py"
    allowed = (
        'FORBIDDEN_ACTIVE = ("00_governance", "01_evidence", "02_tracks", '
        '"03_experiments", "04_outputs", "05_code", "06_frontend", '
        '"07_obsidian_note", "inbox")'
    )
    target.write_text(allowed + "\n", encoding="utf-8")
    assert _run(tmp_path, "archive-runtime").returncode == 0

    target.write_text(allowed + "\nACTIVE_PATH = '01_evidence'\n", encoding="utf-8")
    completed = _run(tmp_path, "archive-runtime")
    assert completed.returncode == 1
    assert "ACTIVE_PATH" in completed.stderr


def test_p2_policy_rejects_final_gate_vocabulary(tmp_path: Path) -> None:
    target = tmp_path / "src/myis_research/p2_cli.py"
    target.parent.mkdir(parents=True)
    target.write_text("D2_OPEN_FINAL\n", encoding="utf-8")

    completed = _run(tmp_path, "p2-closure")

    assert completed.returncode == 1
    assert "P2 readiness CLI must not open final gates" in completed.stderr


def test_policy_scan_fails_closed_when_a_target_is_missing(tmp_path: Path) -> None:
    completed = _run(tmp_path, "p2-closure")

    assert completed.returncode == 2
    assert "required scan target is missing" in completed.stderr


def test_workflow_invokes_policy_scanner_directly() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/cpu-contract.yml").read_text(encoding="utf-8"))
    steps = {step.get("name"): step for step in workflow["jobs"]["contract"]["steps"]}
    expected = {
        "Keep P2 selection and protected stores closed": "p2-closure",
        "Reject archive runtime coupling": "archive-runtime",
    }
    for step_name, policy in expected.items():
        command = steps[step_name]["run"]
        assert command == (
            "uv run --no-sync python .github/scripts/check_policy.py "
            f"--repository-root . {policy}"
        )
        assert "rg " not in command
        assert not command.lstrip().startswith("if ")
