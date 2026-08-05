from __future__ import annotations

import json
from pathlib import Path

from myis_research.armindex.a1_2_cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_a12_cli_validates_launch_locked_scaffold(capsys) -> None:
    assert main(["validate", "--repository-root", str(ROOT)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "a1_2_contract_scaffold_complete_launch_locked"
    assert payload["model_lock_count"] == 5
    assert payload["launch_ready"] is False
    assert payload["measured_execution"] is False
    assert payload["gpu_used"] is False
    assert payload["charged_usd"] == 0
