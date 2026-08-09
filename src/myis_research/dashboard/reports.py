"""Hash-verified, ID-only access to generated Obsidian reports."""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from ..projections.read_model import build_read_model, canonical_json, sha256


_NOTE_ID_RE = re.compile(r"^note_id:\s*(.+)$", re.MULTILINE)
_PROPERTY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
_UNSAFE_MARKUP_RE = re.compile(r"<(?:script|iframe|object|embed|style|link|meta)\b", re.IGNORECASE)
_WIKILINK_RE = re.compile(r"!?(?:\[\[)([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
_REPORT_NOTE_TYPES = frozenset({
    "home", "project_map", "phase_report", "task_report", "result_report",
    "advisor_update", "literature_proxy", "literature_synthesis",
    "history_report", "decision", "risk", "failed_attempt", "presentation",
    "glossary", "generated_file",
})


class ReportCatalogError(RuntimeError):
    """Raised when the generated vault cannot be exposed safely."""


class ReportCatalog:
    def __init__(
        self,
        repository_root: Path,
        *,
        read_model_provider: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        self.repository_root = repository_root.resolve(strict=True)
        self.vault_root = (self.repository_root / "obsidian_report").resolve(strict=True)
        self.vault_root.relative_to(self.repository_root)
        self._read_model_provider = read_model_provider or (lambda: build_read_model(self.repository_root))

    def list(self, *, note_type: str | None = None, campaign: str | None = None) -> dict[str, Any]:
        if note_type is not None and note_type not in _REPORT_NOTE_TYPES:
            raise ReportCatalogError("note_type is not allowlisted")
        if campaign not in {None, "historical", "armindex"}:
            raise ReportCatalogError("campaign is not allowlisted")
        manifest = self._manifest()
        reports = []
        for entry in manifest["files"]:
            report = self._entry(entry, include_content=False)
            if note_type is not None and report["note_type"] != note_type:
                continue
            phase_id = str(report.get("phase_id") or "")
            if campaign == "armindex" and not phase_id.startswith("A"):
                continue
            if campaign == "historical" and not phase_id.startswith("P"):
                continue
            # Preserve the historical phase/task filter contract; active
            # reports are available through the explicit ArmIndex campaign filter.
            if campaign is None and note_type == "phase_report" and not phase_id.startswith("P"):
                continue
            if campaign is None and note_type == "task_report" and phase_id.startswith("A"):
                continue
            reports.append(report)
        return {
            "schema_version": "myis.dashboard-report-catalog.v2",
            "read_model_revision": manifest["read_model_revision"],
            "read_model_sha256": manifest["read_model_sha256"],
            "manifest_sha256": manifest["manifest_sha256"],
            "reports": sorted(reports, key=lambda item: (item["note_type"], item["note_id"])),
        }

    def get(self, note_id: str) -> dict[str, Any]:
        if not isinstance(note_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,127}", note_id):
            raise ReportCatalogError("note_id is invalid")
        manifest = self._manifest()
        entry = next((item for item in manifest["files"] if item.get("note_id") == note_id), None)
        if entry is None:
            raise ReportCatalogError("note_id is not in the generated manifest")
        return {
            "schema_version": "myis.dashboard-report-detail.v2",
            "read_model_revision": manifest["read_model_revision"],
            "manifest_sha256": manifest["manifest_sha256"],
            **self._entry(entry, include_content=True),
        }

    def literature(self, paper_id: str | None = None) -> dict[str, Any]:
        if paper_id is None:
            return self.list(note_type="literature_proxy")
        if not re.fullmatch(r"U\d{3}", paper_id):
            raise ReportCatalogError("paper_id is invalid")
        return self.get(f"LIT-{paper_id}")

    def advisor_updates(self) -> dict[str, Any]:
        return self.list(note_type="advisor_update")

    def _manifest(self) -> Mapping[str, Any]:
        path = self.vault_root / "00_System/Generated/generated-manifest.json"
        if path.is_symlink() or not path.is_file():
            raise ReportCatalogError("generated report manifest is missing or unsafe")
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ReportCatalogError("generated report manifest is invalid") from error
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema_version") != "myis.obsidian-generated-manifest.v2"
            or not isinstance(manifest.get("files"), list)
        ):
            raise ReportCatalogError("generated report manifest contract is invalid")
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        if sha256(canonical_json(unsigned)) != manifest.get("manifest_sha256"):
            raise ReportCatalogError("generated report manifest hash is invalid")
        model = self._read_model_provider()
        for key in ("read_model_revision", "read_model_sha256", "source_commit", "projection_schema_version"):
            if manifest.get(key) != model.get(key):
                raise ReportCatalogError("generated report vault is stale")
        note_ids = [item.get("note_id") for item in manifest["files"] if isinstance(item, dict)]
        if any(not isinstance(item, str) for item in note_ids) or len(note_ids) != len(set(note_ids)):
            raise ReportCatalogError("generated report manifest has invalid note IDs")
        return manifest

    def _entry(self, entry: Mapping[str, Any], *, include_content: bool) -> dict[str, Any]:
        if set(entry) != {"note_id", "relative_path", "sha256", "managed_by"}:
            raise ReportCatalogError("generated report entry contract is invalid")
        relative = Path(str(entry["relative_path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise ReportCatalogError("generated report path is unsafe")
        try:
            note = (self.vault_root / relative).resolve(strict=True)
            note.relative_to(self.vault_root)
        except (OSError, ValueError) as error:
            raise ReportCatalogError("generated report path escapes the vault") from error
        if note.is_symlink() or not note.is_file() or hashlib.sha256(note.read_bytes()).hexdigest() != entry["sha256"]:
            raise ReportCatalogError("generated report hash does not match the manifest")
        text = note.read_text(encoding="utf-8")
        properties, body = _split_note(text)
        generated_file = str(entry["note_id"]).startswith("FILE-") and "note_id" not in properties
        if not generated_file and (properties.get("note_id") != entry["note_id"] or properties.get("managed_by") != "myis-report"):
            raise ReportCatalogError("generated report properties do not match the manifest")
        result: dict[str, Any] = {
            "note_id": entry["note_id"],
            "title": _title(body, str(entry["note_id"])),
            "note_type": properties.get("note_type", "generated_file"),
            "phase_id": properties.get("phase_id"),
            "task_id": properties.get("task_id"),
            "status": properties.get("workflow_status", properties.get("status")),
            "evidence_maturity": properties.get("evidence_maturity"),
            "claim_level": properties.get("claim_level"),
            "safe_to_present": properties.get("safe_to_present", "false") == "true",
            "sha256": entry["sha256"],
            "stale": False,
        }
        if include_content:
            result["html"] = render_safe_markdown(body)
        return result


def _split_note(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return {}, text
    frontmatter, body = text[4:].split("\n---\n", 1)
    properties: dict[str, str] = {}
    for line in frontmatter.splitlines():
        match = _PROPERTY_RE.fullmatch(line)
        if not match:
            continue
        value = match.group(2).strip()
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = value
        properties[match.group(1)] = "" if decoded is None else str(decoded).lower() if isinstance(decoded, bool) else str(decoded)
    return properties, body.strip()


def _title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def render_safe_markdown(markdown: str) -> str:
    """Render a deliberately small Markdown subset after escaping all HTML."""

    if _UNSAFE_MARKUP_RE.search(markdown):
        raise ReportCatalogError("generated report contains unsafe markup")
    lines = markdown.splitlines()
    rendered: list[str] = []
    list_open = False
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("- "):
            if not list_open:
                rendered.append("<ul>")
                list_open = True
            rendered.append(f"<li>{_inline(line[2:])}</li>")
            continue
        if list_open:
            rendered.append("</ul>")
            list_open = False
        if not line:
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1)) + 1
            rendered.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
        elif line.startswith("> "):
            rendered.append(f"<blockquote>{_inline(line[2:])}</blockquote>")
        else:
            rendered.append(f"<p>{_inline(line)}</p>")
    if list_open:
        rendered.append("</ul>")
    return "".join(rendered)


def _inline(value: str) -> str:
    escaped = html.escape(value, quote=True)
    escaped = _WIKILINK_RE.sub(lambda match: html.escape(match.group(2) or match.group(1)), escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped
