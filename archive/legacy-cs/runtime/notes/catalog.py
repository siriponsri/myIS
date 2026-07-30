"""Validate and build the Git-tracked Obsidian research-note projection."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

NOTE_ROOT = Path("projections/obsidian")
CATALOG_SCHEMA = "myis.research-note-catalog.v1"
NOTE_SCHEMA = "myis.research-note.v1"
VAULT_NAME = "myIS Research Notes"
ALLOWED_NOTE_TYPES = {
    "status", "phase_task", "method", "experiment", "result", "failure",
    "decision_pointer", "paper_claim_candidate", "glossary", "handoff",
}
REQUIRED_FIELDS = {
    "schema_version", "note_id", "note_type", "track", "phase", "task", "gate",
    "status", "evidence_level", "git_commit", "source_paths", "agent_generated",
}
FORBIDDEN_SOURCE_MARKERS = ("qrels", "per_query", "membership", "confirmation_ids")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _frontmatter(text: str) -> dict[str, Any]:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("note must begin with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("note frontmatter terminator is missing")
    payload = yaml.safe_load(text[4:end])
    if not isinstance(payload, dict):
        raise ValueError("note frontmatter must be a mapping")
    return payload


def obsidian_uri(relative_path: str) -> str:
    return f"obsidian://open?vault={quote(VAULT_NAME)}&file={quote(relative_path)}"


def validate_note(path: Path, repository_root: Path | None = None) -> dict[str, Any]:
    root = repository_root or path.parents[2]
    raw = path.read_bytes()
    if len(raw) > 512_000:
        raise ValueError(f"note exceeds 512 KiB: {path}")
    text = raw.decode("utf-8")
    metadata = _frontmatter(text)
    missing = REQUIRED_FIELDS - set(metadata)
    if missing:
        raise ValueError(f"note missing required fields: {sorted(missing)}")
    if metadata["schema_version"] != NOTE_SCHEMA or metadata["note_type"] not in ALLOWED_NOTE_TYPES:
        raise ValueError("unsupported research-note schema or type")
    if not isinstance(metadata["source_paths"], list):
        raise ValueError("source_paths must be a list")
    for source in metadata["source_paths"]:
        if not isinstance(source, str) or any(marker in source.casefold() for marker in FORBIDDEN_SOURCE_MARKERS):
            raise ValueError("protected source marker entered note metadata")
    if any(marker in text.casefold() for marker in ("<script", "<iframe", "onerror=")):
        raise ValueError("unsafe HTML is not allowed in notes")
    try:
        path.relative_to(root / NOTE_ROOT)
    except ValueError as error:
        raise ValueError("note is outside the generated-note projection") from error
    return {
        **metadata,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "obsidian_uri": obsidian_uri(path.relative_to(root).as_posix()),
    }


def load_note_catalog(repository_root: Path) -> dict[str, Any]:
    note_dir = repository_root / NOTE_ROOT
    paths = sorted(note_dir.glob("*.md"), key=lambda path: (path.stem != "handoff", path.stem))
    notes = [validate_note(path, repository_root) for path in paths]
    return {"schema_version": CATALOG_SCHEMA, "vault": VAULT_NAME, "notes": notes}


def _source_hash(root: Path, relative: str) -> str:
    path = root / relative
    return _sha256(path) if path.is_file() else ""


def build_notes(repository_root: Path) -> dict[str, Any]:
    """Write safe status/method notes from repository pointers only."""
    note_dir = repository_root / NOTE_ROOT
    note_dir.mkdir(parents=True, exist_ok=True)
    commit = _git_commit(repository_root)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    handoff_hash = _source_hash(repository_root, "HANDOFF.md")
    notes = {
        "handoff": (
            "handoff", "C-S", "F1", "F1.1", "G1", "waiting_gate", "governance", ["HANDOFF.md"],
            "# Handoff สำหรับ Owner\n\nงาน implementation รอบนี้เสร็จในขอบเขต CPU-local และเอกสาร governance แล้ว แต่ `G1` ยัง pending และยังไม่มี scientific run\n\nOwner ต้องตรวจ blockers, เลือก compute และตัดสินใจว่าจะขอ G1 หรือไม่\n",
        ),
        "current-status": (
            "status", "C-S", "F1", "F1.1", "G1", "waiting_gate", "governance", ["HANDOFF.md"],
            f"# สถานะปัจจุบัน / Current status\n\nงานอยู่ที่ `F1.1` และ `G1 pending` งาน CPU ตอนนี้เป็นการเตรียมและทดสอบ fixture เท่านั้น ยังไม่มี measured B0/B1/B2 และยังไม่เปิด GPU หรือ protected data\n\nหลักฐาน: `HANDOFF.md` SHA-256 `{handoff_hash}` และ Git revision `{commit}`\n\nOwner ต้องตรวจ G1 evidence และเลือก compute option เมื่อ package พร้อม\n",
        ),
        "f1-1-cpu-sprint": (
            "phase_task", "C", "F1", "F1.1", "G1", "cpu_preparation", "fixture",
            ["src/myis_research/harness/f1_baselines.py", "tests/test_f1_cpu_scaffold.py"],
            "# CPU Sprint F1.1\n\nสร้าง contract สำหรับ model provenance, cloud transfer, runtime map และ synthetic B0/B1/B2 replay โดยไม่ทำ scientific run\n\nผลตรวจ: fixture replay deterministic, model mismatch ถูก block, cloud transfer ก่อน G1 เป็น NOT_AUTHORIZED และไม่มี protected payload ถูกเปิดอ่าน\n",
        ),
        "track-s-protocol": (
            "method", "S", "S0", "S0.1", "G4", "protocol_repair_complete", "governance",
            ["control/campaigns/scope-autoindex-v1.yaml", "src/myis_research/harness/track_s.py"],
            "# Track S v0.1 protocol repair\n\nคงเส้นทาง `Track C -> frozen C1 -> Track S` และกำหนด A3 ให้ใช้ full SkillOpt core เดียวกับ A2 พร้อม typed overlay ที่จำกัด\n\nกฎหลัก: OUT ต้องดีขึ้นอย่างเคร่งครัด, ALL/IN ต้องไม่ต่ำกว่า signed margins และ finalist ใช้คะแนนสูงสุด โดย tie ใช้ `11 -> 23 -> 47`\n\nยังไม่เปิดการทดลอง: engine provenance, S-MARGIN values และ CoreWeave preflight ยังเป็น blocker\n",
        ),
    }
    for note_id, (note_type, track, phase, task, gate, status, evidence, sources, body) in notes.items():
        fields = "\n".join([
            "---", f"schema_version: {NOTE_SCHEMA}", f"note_id: {note_id}", f"note_type: {note_type}",
            f"track: {track}", f"phase: {phase}", f"task: {task}", f"gate: {gate}", f"status: {status}",
            f"evidence_level: {evidence}", f"git_commit: {commit}", "manifest_sha256: \"\"", "source_paths:",
            *[f"  - {source}" for source in sources], "agent_generated: true", f"updated_at: \"{now}\"",
            "tags: [myis, research]", "---", body,
        ])
        (note_dir / f"{note_id}.md").write_text(fields, encoding="utf-8", newline="\n")
    return load_note_catalog(repository_root)
