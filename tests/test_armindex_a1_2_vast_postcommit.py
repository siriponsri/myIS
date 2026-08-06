from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a1_2_vast import A12VastError
from myis_research.armindex.a1_2_vast_postcommit import (
    validate_postcommit_revision,
)


ROOT = Path(__file__).resolve().parents[1]


def test_postcommit_validator_preserves_v2_and_keeps_launch_locked() -> None:
    result = validate_postcommit_revision(ROOT, require_clean=False)

    assert result["status"] == "prepared_postcommit_launch_locked"
    assert result["launch_allowed"] is False
    assert result["adopted_for_execution"] is False
    assert result["measured_execution"] is False
    assert result["gpu_reserved"] is False
    assert result["charged_usd"] == 0
    assert result["planning_rate_usd_per_four_gpu_instance_hour"] == 0.6
    assert result["estimated_instance_hours"] == "2-4"
    assert result["estimated_raw_worker_usd"] == "1.20-2.40"
    assert len(result["git_commit"]) >= 40
    assert len(result["git_tree"]) >= 40


def test_postcommit_validator_rejects_a_dirty_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "myis_research.armindex.a1_2_vast_postcommit._git",
        lambda _root, *arguments: " M changed" if arguments[0] == "status" else "a" * 40,
    )

    with pytest.raises(A12VastError, match="repository must be clean"):
        validate_postcommit_revision(ROOT)


def test_v3_owner_runbook_uses_postcommit_commands() -> None:
    runbook = (
        ROOT / "docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md"
    ).read_text(encoding="utf-8")

    assert "a1_2_vast_postcommit validate" in runbook
    assert "a1_2_vast_postcommit build-frozen-bundle" in runbook
    assert "launch_allowed=false" in runbook
    assert "adopted_for_execution=false" in runbook
    assert "USD 0.60 per hour for the complete four-RTX3090 instance" in runbook
    assert "USD 1.20-2.40" in runbook
    assert "BLOCKED_BUDGET" in runbook
