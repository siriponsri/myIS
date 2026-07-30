"""Pathless dashboard adapter for the generated Obsidian note projection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..notes.catalog import NOTE_ROOT, load_note_catalog, validate_note

_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")


def _note_path(repository_root: Path, note_id: str) -> Path:
    catalog = load_note_catalog(repository_root)
    for note in catalog["notes"]:
        if note["note_id"] == note_id:
            path = repository_root / NOTE_ROOT / f"{note_id}.md"
            if not path.is_file() or path.is_symlink():
                break
            return path
    raise KeyError(note_id)


def note_catalog(repository_root: Path) -> dict[str, Any]:
    catalog = load_note_catalog(repository_root)
    return {
        "schema_version": "myis.dashboard-note-catalog.v2",
        "vault": catalog["vault"],
        "notes": [
            {
                "note_id": note["note_id"],
                "note_type": note["note_type"],
                "track": note["track"],
                "phase": note["phase"],
                "task": note["task"],
                "gate": note["gate"],
                "status": note["status"],
                "evidence_level": note["evidence_level"],
                "sha256": note["sha256"],
                "obsidian_uri": note["obsidian_uri"],
            }
            for note in catalog["notes"]
        ],
    }


def note_document(repository_root: Path, note_id: str) -> dict[str, Any]:
    path = _note_path(repository_root, note_id)
    metadata = validate_note(path, repository_root)
    text = path.read_text(encoding="utf-8")
    sections: list[dict[str, Any]] = []
    current = {"heading": path.stem, "level": 0, "body": []}
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            if current["body"] or current["level"]:
                sections.append({**current, "body": "\n".join(current["body"]).strip()})
            current = {"heading": match.group(2).strip(), "level": len(match.group(1)), "body": []}
        elif not line.startswith("---"):
            current["body"].append(line)
    if current["body"]:
        sections.append({**current, "body": "\n".join(current["body"]).strip()})
    return {
        "schema_version": "myis.dashboard-note.v2",
        "note_id": note_id,
        "metadata": {key: value for key, value in metadata.items() if key != "source_paths"},
        "source_paths": metadata["source_paths"],
        "sections": sections,
    }
