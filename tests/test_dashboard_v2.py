from pathlib import Path

from fastapi.testclient import TestClient

from myis_research.dashboard.app import create_app
from myis_research.dashboard.contract import DASHBOARD_API_CONTRACT


def test_dashboard_presents_read_model_and_frontend():
    client = TestClient(create_app(repository_root=Path(__file__).resolve().parents[1], test_mode=True))
    headers = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}
    session = client.get("/api/v1/session", headers=headers)
    assert session.status_code == 200
    model = client.get("/api/v1/read-model", headers=headers)
    assert model.status_code == 200
    assert model.json()["schema_version"] == "myis.read-model.v2"
    assert model.json()["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model.json()["runs"] == []
    assert model.json()["metrics"] == []
    assert model.json()["evidence"] == []
    assert model.headers["cache-control"] == "no-store, max-age=0"
    assert "default-src 'self'" in model.headers["content-security-policy"]
    page = client.get("/", headers=headers)
    assert page.status_code == 200
    assert 'href="#main-content"' in page.text
    assert 'id="main-content" class="shell" tabindex="-1"' in page.text
    assert 'role="tablist"' in page.text
    assert 'data-tab="results"' in page.text
    assert 'data-tab="governance"' in page.text
    assert 'data-tab="reports"' in page.text
    assert 'data-tab="tools"' in page.text
    assert 'data-board-mode="pm"' in page.text
    assert 'id="phase-detail"' in page.text
    assert 'id="milestone-timeline"' in page.text
    assert 'id="interpretation-ledger"' in page.text
    assert 'id="gate-grid"' in page.text
    assert 'id="audience"' in page.text


def test_v1_read_aliases_remain_migration_compatible_with_v2_contract():
    client = TestClient(create_app(repository_root=Path(__file__).resolve().parents[1], test_mode=True))
    headers = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}
    assert client.get("/api/v1/session", headers=headers).status_code == 200

    legacy_model = client.get("/api/v1/read-model", headers=headers)
    active_model = client.get("/api/v2/snapshot", headers=headers)
    legacy_overview = client.get("/api/v1/dashboard", headers=headers)
    active_overview = client.get("/api/v2/overview", headers=headers)

    assert legacy_model.status_code == active_model.status_code == 200
    assert legacy_model.json() == active_model.json()
    assert legacy_model.json()["schema_version"] == "myis.read-model.v2"
    assert legacy_overview.status_code == active_overview.status_code == 200
    assert legacy_overview.json() == active_overview.json()


def test_dashboard_frontend_only_targets_fixed_v2_actions():
    root = Path(__file__).resolve().parents[1]
    script = (root / "dashboard" / "assets" / "dashboard.js").read_text(encoding="utf-8")
    styles = (root / "dashboard" / "assets" / "dashboard.css").read_text(encoding="utf-8")
    assert "/api/v2/reports" in script
    assert '"/api/v2/tools"' in script
    assert '"/api/v2/tools/mlflow/start"' in script
    assert '"/api/v2/tools/obsidian/open"' in script
    assert "encodeURIComponent(noteId)" in script
    assert "window.open(result.url, \"_blank\", \"noopener\")" in script
    assert '$("main-content").focus()' in script
    assert "renderOutputsResults" in script
    assert "renderGovernance" in script
    assert "renderMilestones" in script
    assert "presentation?.screens" in script
    assert "@media print" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert "button, input, select { min-height: 40px; }" in styles

    visible_source = (root / "dashboard" / "index.html").read_text(encoding="utf-8") + script
    for protected_term in ("qrels", "query ids", "split membership", "per-query"):
        assert protected_term not in visible_source.lower()


def test_dashboard_rejects_invalid_host_origin_and_csrf():
    client = TestClient(create_app(repository_root=Path(__file__).resolve().parents[1], test_mode=True))
    assert client.get("/healthz", headers={"Host": "example.test"}).status_code == 400

    headers = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}
    session = client.get("/api/v1/session", headers=headers)
    assert session.status_code == 200
    body = {"decision_id": "D2_OPEN_FINAL", "status": "deferred", "rationale": "test"}
    wrong_origin = client.post(
        "/api/v1/owner-decisions/preview",
        headers={**headers, "Origin": "http://example.test"},
        json=body,
    )
    assert wrong_origin.status_code == 403
    missing_csrf = client.post("/api/v1/owner-decisions/preview", headers=headers, json=body)
    assert missing_csrf.status_code == 403
    preview = client.post(
        "/api/v1/owner-decisions/preview",
        headers={**headers, "x-csrf-token": session.json()["csrf_token"]},
        json=body,
    )
    assert preview.status_code == 200


def test_dashboard_health_advertises_v2_contract_and_optional_child_token():
    root = Path(__file__).resolve().parents[1]
    headers = {"Host": "127.0.0.1:8765"}
    response = TestClient(create_app(repository_root=root, test_mode=True)).get("/healthz", headers=headers)
    assert response.status_code == 200
    assert response.json()["api_contract"] == DASHBOARD_API_CONTRACT
    assert "launch_token" not in response.json()

    child_response = TestClient(
        create_app(repository_root=root, test_mode=True, launch_token="child-token")
    ).get("/healthz", headers=headers)
    assert child_response.status_code == 200
    assert child_response.json()["api_contract"] == DASHBOARD_API_CONTRACT
    assert child_response.json()["launch_token"] == "child-token"


def test_dashboard_presentation_is_a_ten_screen_shared_model_story():
    root = Path(__file__).resolve().parents[1]
    client = TestClient(create_app(repository_root=root, test_mode=True))
    headers = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}
    assert client.get("/api/v1/session", headers=headers).status_code == 200
    snapshot = client.get("/api/v2/snapshot", headers=headers).json()
    for audience in ("owner", "advisor", "peer"):
        response = client.get(f"/api/v2/presentation/{audience}", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["read_model_revision"] == snapshot["read_model_revision"]
        screens = body["presentation"]["screens"]
        assert len(screens) == 10
        assert [screen["order"] for screen in screens] == list(range(1, 11))
        assert all(audience in screen["audience"] and screen["safe_to_present"] for screen in screens)
