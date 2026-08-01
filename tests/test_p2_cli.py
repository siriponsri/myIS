from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.p2.fixture import FIXTURE_ID
from myis_research.p2_cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_fixture_pilot_what_if_is_explicitly_non_measured(capsys) -> None:
    output_path = ROOT / "outputs/fixtures/p2/p2-fixture-pilot-v1.receipt.json"

    assert main([
        "fixture-pilot",
        "--repository-root",
        str(ROOT),
        "--output",
        str(output_path),
        "--what-if",
    ]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "arm": "R1",
        "candidate_count": 0,
        "command": "fixture-pilot",
        "fixture_id": FIXTURE_ID,
        "fixture_selection_exposures": 1,
        "isolated_workspaces": 2,
        "measured_execution": False,
        "measured_execution_performed": False,
        "measured_runs": 0,
        "output": "outputs/fixtures/p2/p2-fixture-pilot-v1.receipt.json",
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "profile_id": "p2-r1-primary-v1",
        "profile_sha256": "d5d9d48d8a754168b257367493b8e65fbfcfefc1901408c96336e524c6308e4c",
        "protected_data_accessed": False,
        "real_selection_opened": False,
        "schema_version": "myis.p2-fixture-what-if.v1",
        "selection_accesses": 0,
        "status": "fixture_only_planned",
        "synthetic_candidates": 32,
        "synthetic_iterations": 5,
        "synthetic_shortlist": 4,
        "task_id": "P2.1",
        "what_if": True,
    }


def test_fixture_pilot_cli_emits_only_sanitized_summary(monkeypatch, capsys) -> None:
    expected = {
        "status": "PASS",
        "fixture_status": "passed",
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
    }

    monkeypatch.setattr("myis_research.p2_cli.run_fixture_pilot", lambda root, output: expected)
    assert main(["fixture-pilot", "--repository-root", str(ROOT)]) == 0
    assert json.loads(capsys.readouterr().out) == expected


def test_fixture_pilot_cli_rejects_store_access() -> None:
    with pytest.raises(SystemExit) as error:
        main(["fixture-pilot", "--repository-root", str(ROOT), "--require-stores"])
    assert error.value.code == 3


def test_fixture_pilot_cli_rejects_output_outside_repository() -> None:
    with pytest.raises(SystemExit) as error:
        main([
            "fixture-pilot",
            "--repository-root",
            str(ROOT),
            "--output",
            str(ROOT.parent / "outside.receipt.json"),
        ])
    assert error.value.code == 3
