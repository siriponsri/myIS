from __future__ import annotations

from pathlib import Path

from myis_research.status_cli import build_owner_status, render_owner_status


ROOT = Path(__file__).resolve().parents[1]


def test_owner_status_renders_current_a2_canonical_boundary() -> None:
    status = build_owner_status(ROOT)
    rendered = render_owner_status(status)

    assert status["project"]["phase"] == "A2_PER_ARM_AUTOINDEX"
    assert status["project"]["task"] == "A2.1 / FROZEN_FIVE_ARM_EXECUTION"
    assert status["project"]["scientific_authority"] is False
    assert status["boundaries"]["candidate_evaluations"] == 0
    assert status["boundaries"]["measured_a2_runs"] == 0
    assert status["budget"]["phase_ceiling_usd"] == 35
    assert status["budget"]["campaign_ceiling_usd"] == 150
    assert status["budget"]["status"] == "UNKNOWN_DO_NOT_SPEND"
    assert status["gpu_vast"]["instance"] == "NONE"
    assert "P2_SCOPE_DEVELOPMENT" not in rendered
    assert "GPT-5.6 Sol High" in rendered


def test_owner_status_discovers_handoffs_and_no_active_closed_goal() -> None:
    status = build_owner_status(ROOT)
    handoffs = status["handoffs"]

    assert handoffs["latest_ap"].endswith("A2_PER_ARM_AUTOINDEX_audit_004.md")
    assert handoffs["latest_im"].endswith("A2_PER_ARM_AUTOINDEX_im_004_001.md")
    assert handoffs["latest_lo"] == "NONE"
    assert handoffs["active_goal"] == "NONE"
