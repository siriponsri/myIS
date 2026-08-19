"""Loopback-only read-model dashboard for the active P0-P4 campaign."""

from __future__ import annotations

import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

from ..identity import DISPLAY_NAME, PROGRAM_ID, PROTOCOL_VERSION, RESEARCH_VERSION
from ..ledger import ImmutableJsonLedger, record_sha256
from ..projections.read_model import build_read_model
from ..observatory import ObservatoryError, build_evidence_graph, load_observatory_registry
from .contract import DASHBOARD_API_CONTRACT
from .security import LoopbackSecurityMiddleware, SessionStore
from .reports import ReportCatalog, ReportCatalogError
from .tools import ToolController, ToolControllerError


ACTIVE_DECISIONS = ("D2_OPEN_FINAL", "D3_SUBMIT_RELEASE")
FRONTEND_FILES = {"index.html", "assets/tokens.css", "assets/dashboard.css", "assets/dashboard.js"}


def create_app(
    *,
    repository_root: Path,
    port: int = 8765,
    actor_sid_override: str | None = None,
    test_mode: bool = False,
    tool_controller: ToolController | None = None,
    launch_token: str | None = None,
) -> FastAPI:
    root = repository_root.resolve()
    app = FastAPI(title=DISPLAY_NAME, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(LoopbackSecurityMiddleware, origin=f"http://127.0.0.1:{port}", test_mode=test_mode)
    sessions = SessionStore()
    previews: dict[str, dict[str, Any]] = {}
    ledger = ImmutableJsonLedger(root / "control" / "decisions" / "records", prior_field="prior_record_hash")
    tools = tool_controller or ToolController(root)
    model_lock = threading.Lock()
    model_cache: dict[str, Any] = {}

    def read_model_snapshot() -> dict[str, Any]:
        """Build one validated read model for this dashboard process.

        The model is a synchronized projection artifact. Keeping one snapshot
        per app instance prevents every API endpoint from replaying the full
        historical contract lineage and guarantees that a response family
        shares one revision.
        """

        cached = model_cache.get("value")
        if cached is not None:
            return cached
        with model_lock:
            cached = model_cache.get("value")
            if cached is None:
                cached = build_read_model(root)
                model_cache["value"] = cached
        return cached

    reports = ReportCatalog(root, read_model_provider=read_model_snapshot)

    def session(request: Request) -> tuple[str, Any]:
        return sessions.require(request)

    def write_session(request: Request) -> tuple[str, Any]:
        return sessions.require(request, csrf=True)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        payload = {
            "status": "ok",
            "program_id": PROGRAM_ID,
            "protocol_version": PROTOCOL_VERSION,
            "research_version": RESEARCH_VERSION,
            "api_contract": DASHBOARD_API_CONTRACT,
        }
        if launch_token is not None:
            payload["launch_token"] = launch_token
        return payload

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_frontend(root, "index.html"), media_type="text/html")

    @app.get("/favicon.ico")
    def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/assets/{asset_name}")
    def asset(asset_name: str) -> FileResponse:
        path = _frontend(root, f"assets/{asset_name}")
        media = {"tokens.css": "text/css", "dashboard.css": "text/css", "dashboard.js": "text/javascript"}
        if asset_name not in media:
            raise HTTPException(404, "asset not allowlisted")
        return FileResponse(path, media_type=media[asset_name])

    @app.get("/api/v1/session")
    def create_session(response: Response) -> dict[str, str]:
        session_id, state = sessions.create()
        response.set_cookie("myis_session", session_id, httponly=True, samesite="strict", secure=False, path="/")
        return {"csrf_token": state.csrf}

    @app.get("/api/v1/read-model")
    @app.get("/api/v2/snapshot")
    def read_model(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return read_model_snapshot()

    @app.get("/api/v1/dashboard")
    @app.get("/api/v1/dashboard-snapshot")
    @app.get("/api/v2/overview")
    def dashboard(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _dashboard_projection(read_model_snapshot())

    @app.get("/api/v1/owner-inbox")
    def owner_inbox(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        projection = _dashboard_projection(model)
        return {
            "schema_version": "myis.owner-inbox.v3",
            "current_phase": projection["current_phase"],
            "standing_authorization": "D1_START_CAMPAIGN",
            "next_action": projection["next"][0] if projection["next"] else "รอข้อมูลจากขั้นก่อนหน้า",
            "owner_decisions": list(ACTIVE_DECISIONS),
            "waiting_owner": projection["waiting_owner"],
            "waiting_command": projection["waiting_command"],
            "recent_decisions": model.get("decisions", [])[-5:],
        }

    @app.get("/api/v1/owner-decisions")
    @app.get("/api/v1/owner-gates")
    def owner_decisions(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {"schema_version": "myis.decisions.v3", "active_decisions": list(ACTIVE_DECISIONS), "decisions": model.get("decisions", []), "micro_gates": False}

    @app.get("/api/v1/presentation")
    @app.get("/api/v1/presentation-topics")
    def presentation(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {"schema_version": "myis.presentation.v3", "title": "ArmIndex", "sections": [
            {"id": "question", "title_th": "โจทย์วิจัย", "title_en": "Research question", "body": "Can retriever-conditioned representation programs and a deterministic multi-arm harness improve structured-document retrieval under explicit quality, latency, and cost constraints?"},
            {"id": "flow", "title_th": "ลำดับการทำงาน", "title_en": "Execution flow", "body": "A0 Migration → A1 Screening → A2 Per-arm AutoIndex → A3 Transfer and HarnessOpt → A4 Production and Selection → A5 Final → A6 Full-DAPFAM materialization and scalability → A7 Publication"},
            {"id": "status", "title_th": "สถานะจากข้อมูลจริง", "title_en": "Evidence status", "body": {"phase": _current_phase(model), "runs": len(model.get("runs", [])), "metrics": len(model.get("metrics", [])), "readiness": model.get("publication_readiness", {}).get("status", "blocked")}},
        ]}

    @app.get("/api/v2/board")
    def board(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        armindex_tasks = [task for phase in model.get("armindex", {}).get("phases", []) for task in phase.get("tasks", [])]
        return {
            "schema_version": "myis.dashboard-board.v2",
            "read_model_revision": model["read_model_revision"],
            "tasks": armindex_tasks,
            "wip_limit": 3,
            "wip_count": sum(item.get("status") == "in_progress" for item in armindex_tasks),
        }

    @app.get("/api/v2/phases/{phase_id}")
    def phase_detail(phase_id: str, _: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        active_phases = model.get("armindex", {}).get("phases", [])
        phase = next((item for item in active_phases if item.get("phase_id") == phase_id), None)
        if phase is None:
            phase = next((item for item in model["phases"] if item.get("phase_id") == phase_id), None)
        if phase is None:
            raise HTTPException(404, "phase_id is not in the active A0-A7 or historical P0-P4 registry")
        return {"schema_version": "myis.dashboard-phase.v2", "read_model_revision": model["read_model_revision"], "phase": phase}

    @app.get("/api/v2/results")
    def results(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {"schema_version": "myis.dashboard-results.v2", "read_model_revision": model["read_model_revision"], "results": model["results"], "interpretations": model["interpretations"]}

    @app.get("/api/v2/armindex")
    def armindex(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {"schema_version": "myis.dashboard-armindex.v1", "read_model_revision": model["read_model_revision"], "armindex": model["armindex"]}

    @app.get("/api/v2/observatory")
    def observatory(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {"schema_version": "myis.dashboard-observatory.v1", "read_model_revision": model["read_model_revision"], "observatory": model.get("observatory", {})}

    @app.get("/api/v2/observatory/registry")
    def observatory_registry(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        try:
            registry = load_observatory_registry(root)
        except ObservatoryError as error:
            raise HTTPException(404, str(error)) from error
        return {"schema_version": "myis.dashboard-observatory-registry.v1", "read_model_revision": model["read_model_revision"], "registry": registry}

    @app.get("/api/v2/observatory/graph")
    def observatory_graph(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        try:
            registry = load_observatory_registry(root)
            graph = build_evidence_graph(registry)
        except ObservatoryError as error:
            raise HTTPException(404, str(error)) from error
        return {"schema_version": "myis.dashboard-observatory-graph.v1", "read_model_revision": model["read_model_revision"], "graph": graph.as_dict()}

    @app.get("/api/v2/presentation/{audience}")
    def presentation_v2(audience: str, _: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        if audience not in {"owner", "advisor", "peer"}:
            raise HTTPException(404, "audience is not allowlisted")
        model = read_model_snapshot()
        presentation = model["presentation"]
        screens = [
            screen
            for screen in presentation.get("screens", [])
            if audience in screen.get("audience", []) and screen.get("safe_to_present") is True
        ]
        return {
            "schema_version": "myis.dashboard-presentation.v2",
            "read_model_revision": model["read_model_revision"],
            "audience": audience,
            "presentation": {**presentation, "screens": screens},
        }

    @app.get("/api/v2/raid")
    def raid(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {"schema_version": "myis.dashboard-raid.v2", "read_model_revision": model["read_model_revision"], "items": model["raid"]}

    @app.get("/api/v2/timeline")
    def timeline(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {
            "schema_version": "myis.dashboard-timeline.v2",
            "read_model_revision": model["read_model_revision"],
            "milestones": model["milestones"],
        }

    @app.get("/api/v2/governance")
    def governance(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = read_model_snapshot()
        return {
            "schema_version": "myis.dashboard-governance.v2",
            "read_model_revision": model["read_model_revision"],
            "gates": model["gates"],
            "decisions": model["decisions"],
            "raid": model["raid"],
            "resources": model["resources"],
        }

    @app.get("/api/v2/tools")
    def tool_status(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return tools.status()

    @app.post("/api/v2/tools/mlflow/start")
    def start_mlflow(_: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        return _tool_action(tools.start_mlflow)

    @app.post("/api/v2/tools/mlflow/stop")
    def stop_mlflow(_: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        return _tool_action(tools.stop_mlflow)

    @app.post("/api/v2/tools/mlflow/restart")
    def restart_mlflow(_: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        return _tool_action(tools.restart_mlflow)

    @app.post("/api/v2/tools/obsidian/open")
    def open_obsidian(body: dict[str, Any], _: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        if set(body) - {"note_id"}:
            raise HTTPException(422, "only note_id is accepted")
        return _tool_action(lambda: tools.open_obsidian(str(body.get("note_id", "HOME"))))

    @app.get("/api/v2/reports")
    def report_list(note_type: str | None = None, campaign: str | None = None, _: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _report_action(lambda: reports.list(note_type=note_type, campaign=campaign))

    @app.get("/api/v2/reports/{note_id}")
    def report_detail(note_id: str, _: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _report_action(lambda: reports.get(note_id))

    @app.get("/api/v2/literature")
    def literature(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _report_action(reports.literature)

    @app.get("/api/v2/literature/{paper_id}")
    def literature_detail(paper_id: str, _: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _report_action(lambda: reports.literature(paper_id))

    @app.get("/api/v2/advisor-updates")
    def advisor_updates(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _report_action(reports.advisor_updates)

    @app.post("/api/v1/owner-decisions/preview")
    @app.post("/api/v1/owner-gates/preview")
    def preview(body: dict[str, Any], _: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        decision_id = body.get("decision_id")
        if decision_id not in ACTIVE_DECISIONS:
            raise HTTPException(422, "only D2_OPEN_FINAL and D3_SUBMIT_RELEASE are writable")
        if body.get("status") not in {"approved", "deferred", "rejected"}:
            raise HTTPException(422, "status must be approved, deferred, or rejected")
        token = secrets.token_urlsafe(32)
        record = {"schema_version": "myis.decision-record.v2", "decision_id": decision_id, "status": body["status"], "campaign_id": "armindex-multiretriever-v2", "scope": body.get("scope", {}), "rationale": str(body.get("rationale", "")), "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "prior_record_hash": ledger.head()}
        record["record_sha256"] = record_sha256(record)
        previews[token] = record
        return {"preview_token": token, "record": record, "expires_in_seconds": 300}

    @app.post("/api/v1/owner-decisions/confirm")
    @app.post("/api/v1/owner-gates/confirm")
    def confirm(body: dict[str, Any], _: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        if body.get("confirm") is not True:
            raise HTTPException(422, "explicit confirm=true is required")
        record = previews.pop(str(body.get("preview_token")), None)
        if record is None:
            raise HTTPException(409, "preview missing or expired")
        decision_id = str(record["decision_id"])
        path, digest = ledger.append(decision_id, record)
        return {"decision_id": decision_id, "record_sha256": digest, "path": path.name}

    return app


def _tool_action(action: Any) -> dict[str, Any]:
    try:
        return action()
    except ToolControllerError as error:
        raise HTTPException(409, str(error)) from error


def _report_action(action: Any) -> dict[str, Any]:
    try:
        return action()
    except ReportCatalogError as error:
        raise HTTPException(409, str(error)) from error


def _frontend(root: Path, relative: str) -> Path:
    if relative not in FRONTEND_FILES:
        raise HTTPException(404, "frontend file not allowlisted")
    path = (root / "dashboard" / relative).resolve(strict=True)
    dashboard = (root / "dashboard").resolve(strict=True)
    path.relative_to(dashboard)
    if path.is_symlink() or not path.is_file():
        raise HTTPException(409, "frontend file must be a regular file")
    return path


def _current_phase(model: dict[str, Any]) -> str:
    armindex = model.get("armindex", {})
    if isinstance(armindex, dict) and armindex.get("current_phase"):
        return str(armindex["current_phase"])
    phases = model.get("phases", [])
    for phase in phases:
        if phase.get("status") not in {"complete", "measured"}:
            return str(phase.get("phase_id", "P0_FOUNDATION"))
    return "P4_PUBLICATION"


def _dashboard_projection(model: dict[str, Any]) -> dict[str, Any]:
    runs = model.get("runs", [])
    armindex = model.get("armindex", {})
    phases = armindex.get("phases", []) if isinstance(armindex, dict) else []
    tasks = [task for phase in phases for task in phase.get("tasks", [])]
    done = [f"{task.get('task_id')} {task.get('title')}" for task in tasks if task.get("status") in {"complete", "measured"}]
    next_items = [f"{task.get('task_id')} {task.get('title')}" for task in tasks if task.get("status") in {"executable", "in_progress", "planned"}][:4]
    waiting_owner = [gate.get("gate_id") for gate in model.get("gates", []) if gate.get("status") == "waiting_owner"]
    return {
        "schema_version": "myis.dashboard-projection.v3",
        "projection_revision": model.get("projection_revision"),
        "campaign": next((item for item in model.get("campaigns", []) if item.get("authority_status") == "active"), {}),
        "standing_authorization": "D1_START_CAMPAIGN",
        "current_phase": _current_phase(model),
        "phases": phases,
        "tasks": tasks,
        "gates": model.get("gates", []),
        "experiments": model.get("experiments", []),
        "runs": runs,
        "metrics": model.get("metrics", []),
        "p2_readiness": model.get("p2_readiness", {}),
        "armindex": armindex,
        "observatory": model.get("observatory", {}),
        "cost": model.get("cost", {}),
        "evidence": model.get("evidence", []),
        "datasets": model.get("datasets", []),
        "publication_readiness": model.get("publication_readiness", {}),
        "owner_decisions": list(ACTIVE_DECISIONS),
        "done": done,
        "next": next_items,
        "waiting_owner": waiting_owner,
        "waiting_command": [],
        "historical": {"scope_p2": model.get("p2_readiness", {}), "p1_runs": len(runs)},
    }
