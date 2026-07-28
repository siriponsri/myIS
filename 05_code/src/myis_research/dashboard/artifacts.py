"""Validated, pathless metadata projection for dashboard artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FORBIDDEN_CLASSIFICATIONS = {
    "confirmation",
    "prospective_confirmation",
    "protected",
    "credentials",
    "qrels",
    "split_membership",
    "per_query_confirmation",
}


class ArtifactCatalog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def public_entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if set(payload) != {"schema_version", "artifacts"}:
            raise ValueError("artifact catalog contains unknown fields")
        if payload["schema_version"] != "myis.dashboard-artifact-catalog.v1":
            raise ValueError("unsupported artifact catalog schema")
        output = []
        for entry in payload["artifacts"]:
            allowed = {
                "artifact_id",
                "title",
                "artifact_class",
                "classification",
                "sha256",
                "size_bytes",
                "manifest_sha256",
            }
            if set(entry) != allowed:
                raise ValueError("artifact projection contains unknown fields")
            if entry["classification"].casefold() in FORBIDDEN_CLASSIFICATIONS:
                raise PermissionError("protected artifacts cannot enter the dashboard catalog")
            for field in ("sha256", "manifest_sha256"):
                value = entry[field]
                if len(value) != 64:
                    raise ValueError(f"{field} must be SHA-256")
                int(value, 16)
            output.append(dict(entry))
        return sorted(output, key=lambda item: item["artifact_id"])
