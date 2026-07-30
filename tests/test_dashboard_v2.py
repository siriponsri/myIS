from pathlib import Path

from fastapi.testclient import TestClient

from myis_research.dashboard.app import create_app


def test_dashboard_presents_read_model_and_frontend():
    client = TestClient(create_app(repository_root=Path(__file__).resolve().parents[1], test_mode=True))
    headers = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}
    session = client.get("/api/v1/session", headers=headers)
    assert session.status_code == 200
    model = client.get("/api/v1/read-model", headers=headers)
    assert model.status_code == 200
    assert model.json()["schema_version"] == "myis.read-model.v1"
    page = client.get("/", headers=headers)
    assert page.status_code == 200
    assert "presentation" in page.text
