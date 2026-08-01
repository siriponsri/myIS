from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from myis_research.dashboard.app import create_app


ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}


def test_dashboard_exposes_p2_readiness_without_metrics_or_selection() -> None:
    client = TestClient(create_app(repository_root=ROOT, test_mode=True))
    assert client.get("/api/v1/session", headers=HEADERS).status_code == 200
    snapshot = client.get("/api/v2/snapshot", headers=HEADERS).json()
    p2 = snapshot["p2_readiness"]
    assert p2["status"] == "ready_planned_not_measured"
    assert p2["budget_profile_id"] == "p2-r1-primary-v1"
    assert p2["measured_runs"] == 0
    assert p2["selection_accesses"] == 0
    assert p2["freeze_barrier"]["status"] == "not_started"
    fixture = p2["fixture_pilot"]
    assert fixture["executed"] is True
    assert fixture["status"] == "passed"
    assert fixture["evidence_class"] == "fixture"
    assert fixture["scientific_authority"] is False
    assert fixture["synthetic_candidates"] == 32
    assert fixture["synthetic_iterations"] == 5
    assert fixture["synthetic_shortlist"] == 4
    assert fixture["fixture_selection_exposures"] == 1
    assert fixture["protected_data_accessed"] is False
    assert fixture["measured_execution_performed"] is False
    review = p2["official_review"]
    assert review["status"] == "accepted_static_contract_review"
    assert review["round_count"] == 3
    assert review["final_round"] == 3
    assert review["final_verdict"] == "accept"
    assert review["reviewed_commit"] == "81bb15bdf5753fb8c5b30d25aab51be1ec0b798f"
    assert review["fixture_pilot_executed"] is False
    assert review["protected_data_accessed"] is False
    assert review["measured_execution_performed"] is False
    overview = client.get("/api/v2/overview", headers=HEADERS).json()
    assert overview["p2_readiness"] == p2


def test_dashboard_frontend_mentions_p2_freeze_and_budget_state() -> None:
    source = (ROOT / "dashboard/assets/dashboard.js").read_text(encoding="utf-8")
    assert "renderP2Readiness" in source
    assert "selection_exposure_limit" in source
    assert "max_wall_clock_seconds" in source
    assert "network_model_download" in source
    assert "official_review" in source
    assert "fixture_pilot" in source
    assert "Real candidates" in source
    assert "Owner-local measured preflight" in source
