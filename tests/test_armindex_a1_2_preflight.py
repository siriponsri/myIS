from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_cli import main
from myis_research.armindex.a1_2_preflight import A12PreflightError, run_a1_2_preflight


ROOT = Path(__file__).resolve().parents[1]


def test_preflight_without_owner_inputs_is_fail_closed_and_aggregate_safe(tmp_path: Path) -> None:
    result = run_a1_2_preflight(ROOT)
    assert result.status == "blocked_owner_input"
    assert result.receipt["launch_ready"] is False
    assert result.receipt["cpu_only"] is True
    assert result.receipt["protected_data_accessed"] is False
    assert result.receipt["credentials_accessed"] is False
    assert set(result.receipt["real_counters"].values()) == {0}
    assert "live_quote_and_provider_instance" in result.receipt["blockers"]


def test_preflight_cli_writes_blocked_receipt(capsys, tmp_path: Path) -> None:
    receipt = tmp_path / "preflight.json"
    assert main(["preflight", "--repository-root", str(ROOT), "--receipt", str(receipt)]) == 3
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked_owner_input"
    assert "token_value" not in json.dumps(payload, ensure_ascii=True).lower()
    output = json.loads(capsys.readouterr().out)
    assert output["receipt"] == str(receipt)


def test_preflight_rejects_repository_as_owner_root() -> None:
    with pytest.raises(A12PreflightError, match="outside the repository"):
        run_a1_2_preflight(ROOT, ROOT)
