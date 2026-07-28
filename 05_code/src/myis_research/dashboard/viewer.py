"""Pathless allowlisted PDF access with append-only receipts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..ledger import ImmutableJsonLedger


class PdfCatalog:
    def __init__(self, allowlist_path: Path, receipt_root: Path) -> None:
        self.allowlist_path = allowlist_path
        self.receipts = ImmutableJsonLedger(receipt_root, prior_field="prior_record_hash")

    def entries(self) -> dict[str, dict[str, Any]]:
        if not self.allowlist_path.exists():
            return {}
        if self.allowlist_path.is_symlink() or not self.allowlist_path.is_file():
            raise PermissionError("PDF allowlist must be a regular file")
        payload = json.loads(self.allowlist_path.read_text(encoding="utf-8"))
        entries = payload.get("files", [])
        return {entry["artifact_id"]: entry for entry in entries}

    def resolve(self, artifact_id: str) -> tuple[Path, dict[str, Any]]:
        entry = self.entries().get(artifact_id)
        if entry is None or not entry.get("active", False):
            raise PermissionError("PDF is not approved")
        configured_root = Path(entry["approved_root"])
        if configured_root.is_symlink():
            raise PermissionError("approved PDF root cannot be a symlink")
        root = configured_root.resolve(strict=True)
        relative = Path(entry["relative_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise PermissionError("invalid PDF allowlist path")
        target = (root / relative).resolve(strict=True)
        try:
            target.relative_to(root)
        except ValueError as error:
            raise PermissionError("PDF escapes approved root") from error
        if target.suffix.casefold() != ".pdf" or not target.is_file():
            raise PermissionError("approved artifact is not a PDF")
        expected_size = int(entry["size_bytes"])
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if target.stat().st_size != expected_size or digest != entry["sha256"]:
            raise PermissionError("approved PDF bytes changed")
        return target, entry

    def append_receipt(self, *, artifact_id: str, file_sha256: str, purpose: str, actor_id: str) -> dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        receipt_id = hashlib.sha256(f"{artifact_id}\0{purpose}\0{actor_id}\0{timestamp}".encode()).hexdigest()[:24]
        record = {
            "schema_version": "myis.pdf-access-receipt.v1",
            "receipt_id": receipt_id,
            "approved_file_id": artifact_id,
            "file_sha256": file_sha256,
            "purpose": purpose,
            "timestamp": timestamp,
            "authoritative_actor_id": actor_id,
            "prior_record_hash": self.receipts.head(),
        }
        _, digest = self.receipts.append(receipt_id, record)
        return {**record, "record_sha256": digest}
