"""FastAPI application factory with no remote or generic artifact routes."""

from __future__ import annotations

import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse

from ..identity import DISPLAY_NAME, PROGRAM_ID, RESEARCH_VERSION
from ..ledger import ImmutableJsonLedger
from .artifacts import ArtifactCatalog
from .content import content_document, flow_catalog, flow_document, flow_image, tool_catalog
from .contracts import DecisionConfirmRequest, DecisionPreviewRequest, PdfAccessRequest
from .progress import (
    build_dashboard_snapshot,
    parse_plan,
    scope_sha256,
    validate_decision_scope,
    validated_owner_gate_ledger,
)
from .security import (
    LoopbackSecurityMiddleware,
    SessionStore,
    assert_local_single_user_session,
    assert_private_root_acl,
    authoritative_actor_id,
    windows_account_sid,
)
from .viewer import PdfCatalog


@dataclass
class Preview:
    payload: dict[str, Any]
    session_id: str
    expires_at: float


def create_app(
    *,
    repository_root: Path,
    port: int = 8765,
    actor_sid_override: str | None = None,
    test_mode: bool = False,
) -> FastAPI:
    repository_root = repository_root.resolve()
    origin = f"http://127.0.0.1:{port}"
    approvals = ImmutableJsonLedger(repository_root / "00_governance/approvals", prior_field="prior_record_hash")
    private_root = repository_root / "01_evidence/private/dashboard"
    backend_sid = actor_sid_override or windows_account_sid()
    if not test_mode:
        assert_local_single_user_session()
        assert_private_root_acl(private_root, expected_owner_sid=backend_sid)
    actor_id = authoritative_actor_id(private_root, sid_override=backend_sid)
    artifact_catalog = ArtifactCatalog(private_root / "artifact-catalog.json")
    pdfs = PdfCatalog(private_root / "pdf-allowlist.json", private_root / "access-receipts")
    sessions = SessionStore()
    previews: dict[str, Preview] = {}
    pdf_tokens: dict[str, tuple[str, Path, float]] = {}

    app = FastAPI(title=DISPLAY_NAME, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(LoopbackSecurityMiddleware, origin=origin, test_mode=test_mode)

    def require_session(request: Request) -> tuple[str, Any]:
        return sessions.require(request)

    def require_write_session(request: Request) -> tuple[str, Any]:
        return sessions.require(request, csrf=True)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "program_id": PROGRAM_ID, "research_version": RESEARCH_VERSION}

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/")
    def index():
        frontend = _frontend_file(repository_root, "index.html")
        if frontend is not None:
            return FileResponse(frontend, media_type="text/html")
        return {"display_name": DISPLAY_NAME, "mode": "read-only", "artifact_mutation": False}

    @app.get("/assets/{asset_name}")
    def frontend_asset(asset_name: str):
        media_types = {"dashboard.css": "text/css", "dashboard.js": "text/javascript"}
        if asset_name not in media_types:
            raise HTTPException(status_code=404, detail="frontend asset is not allowlisted")
        frontend = _frontend_file(repository_root, f"assets/{asset_name}")
        if frontend is None:
            raise HTTPException(status_code=404, detail="frontend asset is unavailable")
        return FileResponse(frontend, media_type=media_types[asset_name])

    @app.get("/api/v1/session")
    def create_session(response: Response) -> dict[str, str]:
        session_id, session = sessions.create()
        response.set_cookie(
            "myis_session", session_id, httponly=True, samesite="strict", secure=False, path="/"
        )
        return {"csrf_token": session.csrf}

    @app.get("/api/v1/owner-gates")
    def owner_gates(_: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        plan = parse_plan(repository_root / "PLAN.md")
        return _projection_response(
            lambda: validated_owner_gate_ledger(approvals.root, plan)
        )

    @app.get("/api/v1/dashboard-snapshot")
    def dashboard_snapshot(_: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        return _projection_response(lambda: build_dashboard_snapshot(repository_root))

    @app.get("/api/v1/content/{content_id}")
    def content(content_id: str, _: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        try:
            return _projection_response(lambda: content_document(repository_root, content_id))
        except KeyError as error:
            raise HTTPException(status_code=404, detail="content view is not allowlisted") from error

    @app.get("/api/v1/flows")
    def flows(_: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        return _projection_response(lambda: flow_catalog(repository_root))

    @app.get("/api/v1/flows/{flow_id}")
    def flow(flow_id: str, _: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        try:
            return _projection_response(lambda: flow_document(repository_root, flow_id))
        except KeyError as error:
            raise HTTPException(status_code=404, detail="flow is not allowlisted") from error

    @app.get("/api/v1/flows/{flow_id}/image")
    def flow_svg(
        flow_id: str,
        expected_sha256: str = Query(alias="sha256", min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"),
        _: tuple[str, Any] = Depends(require_session),
    ):
        try:
            payload, digest = _projection_response(lambda: flow_image(repository_root, flow_id))
        except KeyError as error:
            raise HTTPException(status_code=404, detail="flow is not allowlisted") from error
        if not secrets.compare_digest(digest, expected_sha256):
            raise HTTPException(status_code=409, detail="flow image hash changed; refresh the flow detail")
        return Response(
            content=payload,
            media_type="image/svg+xml",
            headers={"X-Content-SHA256": digest},
        )

    @app.get("/api/v1/tools")
    def tools(_: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        return _projection_response(lambda: tool_catalog(repository_root))

    @app.post("/api/v1/owner-gates/preview")
    def preview_decision(
        body: DecisionPreviewRequest,
        session: tuple[str, Any] = Depends(require_write_session),
    ) -> dict[str, Any]:
        git_commit = _git_commit(repository_root)
        if _git_dirty(repository_root):
            raise HTTPException(status_code=409, detail="repository must be clean before an Owner decision")
        plan = parse_plan(repository_root / "PLAN.md")
        scope = body.scope.model_dump(mode="json", exclude_none=True)
        try:
            validate_decision_scope(plan, body.gate_id, scope)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if body.supersedes_decision_id:
            existing = [payload for _, payload, _ in approvals.records()]
            decisions = {item.get("decision_id"): item for item in existing}
            if body.supersedes_decision_id not in decisions:
                raise HTTPException(status_code=409, detail="superseded decision does not exist")
            prior_gate = _normalized_gate_id(str(decisions[body.supersedes_decision_id].get("gate_id", "")))
            if prior_gate != body.gate_id:
                raise HTTPException(status_code=409, detail="a correction must use the original gate ID")
            if any(item.get("supersedes_decision_id") == body.supersedes_decision_id for item in existing):
                raise HTTPException(status_code=409, detail="superseded decision already has a correction")
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        decision_id = _decision_id(body.gate_id, now)
        payload = {
            "schema_version": "myis.owner-gate-decision.v2",
            "decision_id": decision_id,
            "gate_id": body.gate_id,
            "status": body.status,
            "rationale": body.rationale,
            "timestamp": timestamp,
            "actor": actor_id,
            "display_label": body.display_label,
            "evidence_manifest_hashes": list(body.evidence_manifest_hashes),
            "git_commit": git_commit,
            "scope": scope,
            "scope_hash": scope_sha256(scope),
            "prior_record_hash": approvals.head(),
            "supersedes_decision_id": body.supersedes_decision_id,
        }
        token = secrets.token_urlsafe(32)
        previews[token] = Preview(payload, session[0], time() + 300)
        return {"preview_token": token, "record": payload, "expires_in_seconds": 300}

    @app.post("/api/v1/owner-gates/confirm")
    def confirm_decision(
        body: DecisionConfirmRequest,
        session: tuple[str, Any] = Depends(require_write_session),
    ) -> dict[str, Any]:
        preview = previews.pop(body.preview_token, None)
        if preview is None or preview.expires_at < time() or preview.session_id != session[0]:
            raise HTTPException(status_code=409, detail="preview is missing, expired, or session-bound")
        if _git_dirty(repository_root) or _git_commit(repository_root) != preview.payload["git_commit"]:
            raise HTTPException(status_code=409, detail="Git state changed; create a new preview")
        if approvals.head() != preview.payload["prior_record_hash"]:
            raise HTTPException(status_code=409, detail="ledger changed; create a new preview")
        path, digest = approvals.append(preview.payload["decision_id"], preview.payload)
        return {"decision_id": preview.payload["decision_id"], "record_sha256": digest, "path": path.name}

    @app.get("/api/v1/artifacts")
    def artifacts(_: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        entries = pdfs.entries()
        return {
            "artifacts": artifact_catalog.public_entries(),
            "approved_pdfs": [
                {
                    "artifact_id": key,
                    "sha256": value["sha256"],
                    "size_bytes": value["size_bytes"],
                    "mime_type": "application/pdf",
                    "license_privacy_decision_id": value["license_privacy_decision_id"],
                }
                for key, value in sorted(entries.items())
                if value.get("active", False)
            ]
        }

    @app.post("/api/v1/pdf-access/confirm")
    def confirm_pdf_access(
        body: PdfAccessRequest,
        session: tuple[str, Any] = Depends(require_write_session),
    ) -> dict[str, Any]:
        target, entry = pdfs.resolve(body.artifact_id)
        receipt = pdfs.append_receipt(
            artifact_id=body.artifact_id,
            file_sha256=entry["sha256"],
            purpose=body.purpose,
            actor_id=actor_id,
        )
        token = secrets.token_urlsafe(32)
        pdf_tokens[token] = (session[0], target, time() + 60)
        return {"stream_token": token, "expires_in_seconds": 60, "receipt_id": receipt["receipt_id"]}

    @app.get("/api/v1/pdf/{token}")
    def stream_pdf(token: str, session: tuple[str, Any] = Depends(require_session)):
        record = pdf_tokens.pop(token, None)
        if record is None or record[0] != session[0] or record[2] < time():
            raise HTTPException(status_code=404, detail="PDF token is invalid")
        return FileResponse(record[1], media_type="application/pdf", filename="approved-document.pdf")

    return app


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _decision_id(gate_id: str, timestamp: datetime) -> str:
    normalized = timestamp.astimezone(timezone.utc)
    return f"{gate_id}-{normalized.strftime('%Y%m%dT%H%M%S%fZ')}"


def _git_dirty(root: Path) -> bool:
    return bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )


def _frontend_file(repository_root: Path, relative_path: str) -> Path | None:
    allowed = {"index.html", "assets/dashboard.css", "assets/dashboard.js"}
    if relative_path not in allowed:
        return None
    frontend_root = repository_root / "06_forntend/dashboard"
    target = frontend_root / relative_path
    if not target.exists():
        return None
    if frontend_root.is_symlink() or target.is_symlink() or not target.is_file():
        raise HTTPException(status_code=409, detail="frontend files must be regular non-symlink files")
    resolved_root = frontend_root.resolve(strict=True)
    resolved_target = target.resolve(strict=True)
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as error:
        raise HTTPException(status_code=409, detail="frontend file escapes the allowlisted root") from error
    return resolved_target


def _projection_response(factory: Any) -> Any:
    try:
        return factory()
    except (OSError, PermissionError, ValueError, subprocess.SubprocessError) as error:
        raise HTTPException(status_code=409, detail=f"dashboard projection unavailable: {error}") from error


def _normalized_gate_id(value: str) -> str | None:
    for gate_id in (f"G{index}" for index in range(9)):
        if value == gate_id or value.endswith(f"-{gate_id}"):
            return gate_id
    return None
