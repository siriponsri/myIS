"""Pointer-first ArmIndex Research Brain validation and deterministic indexing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from .contracts import ArmIndexContractError


PROTECTED_KEYS = frozenset({"qrels", "query_id", "family_id", "rankings", "per_query", "split_membership", "credentials"})


def validate_memory(root: Path, value: Mapping[str, Any], *, now: datetime | None = None) -> None:
    schema_path = root.resolve() / "schemas" / "armindex" / "brain-memory.v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(dict(value)), key=lambda item: list(item.path))
    if errors:
        raise ArmIndexContractError(f"Brain memory validation failed: {errors[0].message}")
    text = json.dumps(value, ensure_ascii=True).lower()
    if any(key in text for key in PROTECTED_KEYS):
        raise ArmIndexContractError("Brain memory contains a protected field marker")
    source_uri = str(value["source_uri"])
    if ":\\" not in source_uri and not source_uri.startswith(("https://", "urn:")):
        source = (root.resolve() / source_uri).resolve()
        source.relative_to(root.resolve())
        if not source.is_file():
            raise ArmIndexContractError("Brain memory source pointer is missing")
    if value["memory_type"] == "active_context":
        if value["expires_at"] is None:
            raise ArmIndexContractError("active context requires an expiration time")
        current = now or datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(str(value["expires_at"]).replace("Z", "+00:00"))
        if value["status"] == "active" and expiry <= current:
            raise ArmIndexContractError("expired active context must be archived or superseded")
    if value["supersedes"] and value["status"] != "active":
        raise ArmIndexContractError("a new superseding memory must be active")


def query_memories(records: Iterable[Mapping[str, Any]], **filters: str) -> list[dict[str, Any]]:
    allowed = {"campaign_id", "phase_id", "task_id", "research_flow_id", "memory_type", "status"}
    unknown = set(filters) - allowed - {"keyword", "arm", "model", "program", "harness", "evidence_id"}
    if unknown:
        raise ArmIndexContractError(f"unsupported Brain filters: {sorted(unknown)}")
    result = []
    for record in records:
        if any(str(record.get(key)) != value for key, value in filters.items() if key in allowed):
            continue
        list_filters = {"arm": "arm_ids", "model": "model_ids", "program": "representation_program_ids", "harness": "harness_ids", "evidence_id": "evidence_ids"}
        if any(value not in record.get(field, []) for key, field in list_filters.items() if (value := filters.get(key))):
            continue
        keyword = filters.get("keyword", "").lower()
        if keyword and keyword not in f"{record.get('title', '')} {record.get('interpretation', '')}".lower():
            continue
        result.append(dict(record))
    return sorted(result, key=lambda item: (str(item.get("created_at", "")), str(item.get("memory_id", ""))))


def build_moc(records: Iterable[Mapping[str, Any]]) -> str:
    rows = sorted(records, key=lambda item: (str(item.get("memory_type", "")), str(item.get("memory_id", ""))))
    lines = ["# ArmIndex Research Brain", "", "Generated pointer-first index. Canonical facts remain in control records and receipts.", ""]
    current_type = None
    for row in rows:
        memory_type = str(row["memory_type"])
        if memory_type != current_type:
            lines.extend([f"## {memory_type.replace('_', ' ').title()}", ""])
            current_type = memory_type
        lines.append(f"- `{row['memory_id']}` - {row['title']} (`{row['status']}`) -> `{row['source_uri']}`")
    return "\n".join(lines) + "\n"
