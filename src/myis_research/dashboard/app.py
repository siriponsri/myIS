"""Loopback-only read-model dashboard for the active P0-P4 campaign."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

from ..identity import DISPLAY_NAME, PROGRAM_ID, PROTOCOL_VERSION, RESEARCH_VERSION
from ..ledger import ImmutableJsonLedger, record_sha256
from ..projections.read_model import build_read_model
from .security import LoopbackSecurityMiddleware, SessionStore


ACTIVE_DECISIONS = ("D2_OPEN_FINAL", "D3_SUBMIT_RELEASE")
FRONTEND_FILES = {"index.html", "assets/tokens.css", "assets/dashboard.css", "assets/dashboard.js"}


def create_app(*, repository_root: Path, port: int = 8765, actor_sid_override: str | None = None, test_mode: bool = False) -> FastAPI:
    root = repository_root.resolve()
    app = FastAPI(title=DISPLAY_NAME, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(LoopbackSecurityMiddleware, origin=f"http://127.0.0.1:{port}", test_mode=test_mode)
    sessions = SessionStore()
    previews: dict[str, dict[str, Any]] = {}
    ledger = ImmutableJsonLedger(root / "control" / "decisions" / "records", prior_field="prior_record_hash")

    def session(request: Request) -> tuple[str, Any]:
        return sessions.require(request)

    def write_session(request: Request) -> tuple[str, Any]:
        return sessions.require(request, csrf=True)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "program_id": PROGRAM_ID, "protocol_version": PROTOCOL_VERSION, "research_version": RESEARCH_VERSION}

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
    def read_model(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return build_read_model(root)

    @app.get("/api/v1/dashboard")
    @app.get("/api/v1/dashboard-snapshot")
    def dashboard(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        return _dashboard_projection(build_read_model(root))

    @app.get("/api/v1/owner-inbox")
    def owner_inbox(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = build_read_model(root)
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
        model = build_read_model(root)
        return {"schema_version": "myis.decisions.v3", "active_decisions": list(ACTIVE_DECISIONS), "decisions": model.get("decisions", []), "micro_gates": False}

    @app.get("/api/v1/presentation")
    @app.get("/api/v1/presentation-topics")
    def presentation(_: tuple[str, Any] = Depends(session)) -> dict[str, Any]:
        model = build_read_model(root)
        campaign = model.get("campaigns", [{}])[0]
        return {"schema_version": "myis.presentation.v3", "title": campaign.get("title", "SCOPE / AutoIndex"), "sections": [
            {"id": "question", "title_th": "โจทย์วิจัย", "title_en": "Research question", "body": "Can a grounded AutoIndex-style representation compiler improve family-level patent retrieval with a fixed retriever?"},
            {"id": "flow", "title_th": "ลำดับการทำงาน", "title_en": "Execution flow", "body": "P0 Foundation → P1 CPU baseline → P2 SCOPE development → P3 Final → P4 Publication"},
            {"id": "status", "title_th": "สถานะจากข้อมูลจริง", "title_en": "Evidence status", "body": {"phase": _current_phase(model), "runs": len(model.get("runs", [])), "metrics": len(model.get("metrics", [])), "readiness": model.get("publication_readiness", {}).get("status", "blocked")}},
        ]}

    @app.post("/api/v1/owner-decisions/preview")
    @app.post("/api/v1/owner-gates/preview")
    def preview(body: dict[str, Any], _: tuple[str, Any] = Depends(write_session)) -> dict[str, Any]:
        decision_id = body.get("decision_id")
        if decision_id not in ACTIVE_DECISIONS:
            raise HTTPException(422, "only D2_OPEN_FINAL and D3_SUBMIT_RELEASE are writable")
        if body.get("status") not in {"approved", "deferred", "rejected"}:
            raise HTTPException(422, "status must be approved, deferred, or rejected")
        token = secrets.token_urlsafe(32)
        record = {"schema_version": "myis.decision-record.v2", "decision_id": decision_id, "status": body["status"], "campaign_id": "scope-autoindex-v1", "scope": body.get("scope", {}), "rationale": str(body.get("rationale", "")), "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "prior_record_hash": ledger.head()}
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
    phases = model.get("phases", [])
    for phase in phases:
        if phase.get("status") not in {"complete", "measured"}:
            return str(phase.get("phase_id", "P0_FOUNDATION"))
    return "P4_PUBLICATION"


def _dashboard_projection(model: dict[str, Any]) -> dict[str, Any]:
    runs = model.get("runs", [])
    tasks = model.get("tasks", [])
    done = [f"{task.get('task_id')} {task.get('title')}" for task in tasks if task.get("status") in {"complete", "measured"}]
    next_items = [f"{task.get('task_id')} {task.get('title')}" for task in tasks if task.get("status") in {"executable", "in_progress", "planned"}][:4]
    waiting_owner = [gate.get("gate_id") for gate in model.get("gates", []) if gate.get("status") == "waiting_owner"]
    return {
        "schema_version": "myis.dashboard-projection.v3",
        "projection_revision": model.get("projection_revision"),
        "campaign": (model.get("campaigns") or [{}])[0],
        "standing_authorization": "D1_START_CAMPAIGN",
        "current_phase": _current_phase(model),
        "phases": model.get("phases", []),
        "tasks": tasks,
        "gates": model.get("gates", []),
        "experiments": model.get("experiments", []),
        "runs": runs,
        "metrics": model.get("metrics", []),
        "cost": model.get("cost", {}),
        "evidence": model.get("evidence", []),
        "datasets": model.get("datasets", []),
        "publication_readiness": model.get("publication_readiness", {}),
        "owner_decisions": list(ACTIVE_DECISIONS),
        "done": done,
        "next": next_items,
        "waiting_owner": waiting_owner,
        "waiting_command": [] if runs else ["P1_CPU_EXECUTION_ENVELOPE"],
    }
