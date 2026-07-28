"""FastAPI application factory with no remote or generic artifact routes."""

from __future__ import annotations

import hashlib
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

from ..identity import DISPLAY_NAME, PROGRAM_ID, RESEARCH_VERSION
from ..ledger import ImmutableJsonLedger
from .artifacts import ArtifactCatalog
from .contracts import DecisionConfirmRequest, DecisionPreviewRequest, PdfAccessRequest
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

    @app.get("/")
    def index() -> dict[str, Any]:
        return {"display_name": DISPLAY_NAME, "mode": "read-only", "artifact_mutation": False}

    @app.get("/api/v1/session")
    def create_session(response: Response) -> dict[str, str]:
        session_id, session = sessions.create()
        response.set_cookie(
            "myis_session", session_id, httponly=True, samesite="strict", secure=False, path="/"
        )
        return {"csrf_token": session.csrf}

    @app.get("/api/v1/owner-gates")
    def owner_gates(_: tuple[str, Any] = Depends(require_session)) -> dict[str, Any]:
        records = [payload for _, payload, _ in approvals.records()]
        return {"records": records, "chain": approvals.validate_chain()}

    @app.post("/api/v1/owner-gates/preview")
    def preview_decision(
        body: DecisionPreviewRequest,
        session: tuple[str, Any] = Depends(require_write_session),
    ) -> dict[str, Any]:
        git_commit = _git_commit(repository_root)
        if _git_dirty(repository_root):
            raise HTTPException(status_code=409, detail="repository must be clean before an Owner decision")
        if body.supersedes_decision_id:
            existing = [payload for _, payload, _ in approvals.records()]
            decision_ids = {item.get("decision_id") for item in existing}
            if body.supersedes_decision_id not in decision_ids:
                raise HTTPException(status_code=409, detail="superseded decision does not exist")
            if any(item.get("supersedes_decision_id") == body.supersedes_decision_id for item in existing):
                raise HTTPException(status_code=409, detail="superseded decision already has a correction")
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        decision_id = _decision_id(body.gate_id, now)
        payload = {
            "schema_version": "myis.owner-gate-decision.v1",
            "decision_id": decision_id,
            "gate_id": body.gate_id,
            "status": body.status,
            "rationale": body.rationale,
            "timestamp": timestamp,
            "actor": actor_id,
            "display_label": body.display_label,
            "evidence_manifest_hashes": list(body.evidence_manifest_hashes),
            "git_commit": git_commit,
            "scope_hash": body.scope_hash,
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
