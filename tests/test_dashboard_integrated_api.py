from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from myis_research.dashboard.app import create_app
from myis_research.dashboard.reports import ReportCatalog
from myis_research.dashboard.tools import ToolController


ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"Origin": "http://127.0.0.1:8765", "Host": "127.0.0.1:8765"}


class FakeTools:
    def __init__(self) -> None:
        self.actions: list[tuple[str, str | None]] = []

    def status(self):
        return {"schema_version": "myis.dashboard-tools.v2", "mlflow": {"status": "stopped"}, "obsidian": {"status": "ready"}}

    def start_mlflow(self):
        self.actions.append(("start", None))
        return {"status": "ready", "url": "http://127.0.0.1:5000", "reused": False}

    def stop_mlflow(self):
        self.actions.append(("stop", None))
        return {"status": "stopped"}

    def restart_mlflow(self):
        self.actions.append(("restart", None))
        return {"status": "ready", "url": "http://127.0.0.1:5000", "reused": False}

    def open_obsidian(self, note_id="HOME"):
        self.actions.append(("obsidian", note_id))
        return {"status": "opened", "note_id": note_id}


def _client():
    tools = FakeTools()
    client = TestClient(create_app(repository_root=ROOT, test_mode=True, tool_controller=tools))
    session = client.get("/api/v1/session", headers=HEADERS)
    return client, tools, session.json()["csrf_token"]


def test_tool_controller_uses_canonical_shared_store_by_default(monkeypatch):
    monkeypatch.delenv("MYIS_MLFLOW_STORE", raising=False)
    controller = ToolController(ROOT)
    assert controller.store_root == ROOT.parents[2] / "01_Stores" / "00_myIS" / "mlflow"


def test_v2_projection_and_report_endpoints_share_one_revision():
    client, tools, _ = _client()
    snapshot = client.get("/api/v2/snapshot", headers=HEADERS).json()
    for endpoint in (
        "/api/v2/overview",
        "/api/v2/board",
        "/api/v2/results",
        "/api/v2/raid",
        "/api/v2/timeline",
        "/api/v2/governance",
        "/api/v2/phases/P1_CPU_BASELINE",
    ):
        response = client.get(endpoint, headers=HEADERS)
        assert response.status_code == 200
        if "read_model_revision" in response.json():
            assert response.json()["read_model_revision"] == snapshot["read_model_revision"]

    reports = client.get("/api/v2/reports", headers=HEADERS)
    assert reports.status_code == 200
    assert reports.json()["read_model_revision"] == snapshot["read_model_revision"]
    home = client.get("/api/v2/reports/HOME", headers=HEADERS)
    assert home.status_code == 200
    assert home.json()["sha256"] == next(item["sha256"] for item in reports.json()["reports"] if item["note_id"] == "HOME")
    assert "<script" not in home.json()["html"].lower()
    assert tools.actions == []

    phases = client.get("/api/v2/reports?note_type=phase_report", headers=HEADERS)
    assert phases.status_code == 200
    assert len(phases.json()["reports"]) == 5
    assert {item["note_type"] for item in phases.json()["reports"]} == {"phase_report"}
    rejected = client.get("/api/v2/reports?note_type=../../unsafe", headers=HEADERS)
    assert rejected.status_code == 409


def test_tool_actions_require_origin_csrf_and_fixed_input():
    client, tools, csrf = _client()
    assert client.get("/api/v2/tools", headers=HEADERS).status_code == 200
    assert client.post("/api/v2/tools/mlflow/start", headers=HEADERS).status_code == 403
    action_headers = {**HEADERS, "x-csrf-token": csrf}
    started = client.post("/api/v2/tools/mlflow/start", headers=action_headers)
    assert started.status_code == 200
    assert started.json()["url"] == "http://127.0.0.1:5000"
    rejected = client.post(
        "/api/v2/tools/obsidian/open",
        headers=action_headers,
        json={"note_id": "HOME", "path": "C:/arbitrary"},
    )
    assert rejected.status_code == 422
    opened = client.post("/api/v2/tools/obsidian/open", headers=action_headers, json={"note_id": "HOME"})
    assert opened.status_code == 200
    assert tools.actions == [("start", None), ("obsidian", "HOME")]


def test_report_catalog_rejects_paths_and_exposes_literature_by_stable_id():
    catalog = ReportCatalog(ROOT)
    assert catalog.literature("U011")["note_id"] == "LIT-U011"
    with pytest.raises(Exception, match="note_id is invalid"):
        catalog.get("../HOME")
    client, _, _ = _client()
    assert client.get("/api/v2/reports/..%2FHOME", headers=HEADERS).status_code in {404, 409}
