from __future__ import annotations

from pathlib import Path

from myis_research.status_cli import (
    _active_goal,
    _gpu_state,
    _routing,
    build_owner_status,
    render_owner_status,
)


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
    assert status["routing"]["recommended_next_session"] == "AP"
    assert "P2_SCOPE_DEVELOPMENT" not in rendered
    assert "GPT-5.6 Sol High" in rendered


def test_owner_status_discovers_handoffs_and_no_active_closed_goal() -> None:
    status = build_owner_status(ROOT)
    handoffs = status["handoffs"]

    assert handoffs["latest_ap"].endswith("A2_PER_ARM_AUTOINDEX_audit_004.md")
    assert handoffs["latest_im"].endswith("A2_PER_ARM_AUTOINDEX_im_004_001.md")
    assert handoffs["latest_lo"] == "NONE"
    assert handoffs["active_goal"] == "NONE"


def test_gpu_state_uses_staged_provider_receipt() -> None:
    gpu = _gpu_state(
        {
            "status": "STAGED_NOT_LAUNCHED_MEASURED_A2_LOCKED",
            "measured_a2_started": False,
            "provider_admission_receipt": {
                "instance_id": 123456,
                "whole_workload_total_usd": 12.5,
            },
        }
    )

    assert gpu["instance"] == "123456"
    assert gpu["decision"] == "UNKNOWN"
    assert gpu["accrued_gpu_cost_usd"] == "12.5"


def test_active_numbered_goal_is_discovered_and_routes_lo(tmp_path: Path) -> None:
    goal_dir = tmp_path / "docs/goal"
    goal_dir.mkdir(parents=True)
    active = goal_dir / "A2_PER_ARM_AUTOINDEX_goal_005.md"
    active.write_text("---\nlifecycle: ACTIVE\n---\n", encoding="utf-8")
    (goal_dir / "closed.md").write_text(
        "---\nlifecycle: CLOSED\n---\n", encoding="utf-8"
    )
    (goal_dir / "blocked.md").write_text(
        "---\nlifecycle: BLOCKED\n---\n", encoding="utf-8"
    )

    discovered = _active_goal(tmp_path)
    routing = _routing({}, discovered)

    assert discovered.endswith("A2_PER_ARM_AUTOINDEX_goal_005.md")
    assert routing["recommended_next_session"] == "LO"
    assert routing["recommended_model"] == "GPT-5.6 Terra XHigh"


def test_no_active_goal_and_dynamic_im_route(tmp_path: Path) -> None:
    goal_dir = tmp_path / "docs/goal"
    goal_dir.mkdir(parents=True)
    (goal_dir / "blocked.md").write_text(
        "---\nlifecycle: BLOCKED\n---\n", encoding="utf-8"
    )

    assert _active_goal(tmp_path) == "NONE"
    routing = _routing(
        {
            "current_status": "IMPLEMENTATION_BLOCKED_MEASUREMENT_LOCKED",
            "current_route": "IM",
        },
        "NONE",
    )
    assert routing["recommended_next_session"] == "IM"
    assert routing["recommended_model"] == "GPT-5.6 Sol Medium"
