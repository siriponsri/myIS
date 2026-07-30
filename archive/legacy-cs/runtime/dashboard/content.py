"""Curated, pathless dashboard content, flow, and tool projections."""

from __future__ import annotations

import hashlib
import re
import stat
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

DOCUMENTS = (
    ("canonical-plan", "Canonical execution plan", "plan", "PLAN.md"),
    ("research-protocol", "Full research track protocol", "process", "FULL_RESEARCH_TRACK_PLAN.md"),
    ("harness-contract", "Local harness build contract", "harness", "LOCAL_RESEARCH_HARNESS_BUILD_PLAN.md"),
    ("agent-contract", "Agent contract", "harness", "AGENTS.md"),
    ("owner-gates", "Owner decision authority", "process", "control/program.yaml"),
    ("operations", "Active layout", "process", "control/layout.v2.yaml"),
    ("toolchain", "Source of truth", "tools", "control/source-of-truth.yaml"),
    ("tool-bootstrap", "Campaign protocol", "tools", "control/campaigns/scope-autoindex-v1.yaml"),
    ("tool-lock", "Dependency lock", "tools", "pyproject.toml"),
)
FLOWS = (
    ("research-program", "Research program", "dashboard/diagrams/research-program.svg"),
    ("candidate-exposure", "Candidate exposure and pool freeze", "dashboard/diagrams/candidate-exposure.svg"),
    ("owner-gate", "Owner decision", "dashboard/diagrams/owner-gate.svg"),
    ("confirmation-boundary", "External confirmation boundary", "dashboard/diagrams/confirmation-boundary.svg"),
    ("harness-kernel", "Deterministic harness kernel", "dashboard/diagrams/harness-kernel.svg"),
    ("run-lifecycle", "Governed run lifecycle", "dashboard/diagrams/run-lifecycle.svg"),
    ("decision-ledger", "Immutable decision ledger", "dashboard/diagrams/decision-ledger.svg"),
    ("mlflow-mirror", "Rebuildable MLflow mirror", "dashboard/diagrams/mlflow-mirror.svg"),
)
CONTENT_TITLES = {
    "process": "Research Process",
    "harness": "Harness Rules",
    "tools": "Tool Governance",
}
TOOLS_SOURCE = "pyproject.toml"
TOPICS_SOURCE = "control/campaigns/scope-autoindex-v1.yaml"
_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
_UNSAFE_HTML = re.compile(r"<\s*(script|iframe|object|embed|link|style)\b|\bon[a-z]+\s*=", re.I)
_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_FORBIDDEN_SVG_TAGS = {
    "animate",
    "animatemotion",
    "animatetransform",
    "discard",
    "embed",
    "foreignobject",
    "iframe",
    "image",
    "object",
    "script",
    "set",
    "style",
    "use",
}
_UNSAFE_SVG_VALUE = re.compile(r"(?:javascript:|data:|file:|https?://|@import|url\s*\(|expression\s*\()", re.I)
_SAFE_FRAGMENT_URL = re.compile(r"^url\(\s*#[A-Za-z_][A-Za-z0-9_.:-]*\s*\)$", re.I)


def content_document(repository_root: Path, content_id: str) -> dict[str, Any]:
    registry = _registry(repository_root)
    if content_id not in CONTENT_TITLES:
        raise KeyError(content_id)
    allowed_kinds = {
        "process": {"process", "plan"},
        "harness": {"harness"},
        "tools": {"tools"},
    }[content_id]
    documents = [
        _project_markdown(repository_root, item["path"], source_id=item["content_id"], title=item["title"])
        for item in registry["documents"]
        if item["kind"] in allowed_kinds and item["content_id"] != "tool-lock"
    ]
    return {
        "schema_version": "myis.dashboard-content.v1",
        "content_id": content_id,
        "title": CONTENT_TITLES[content_id],
        "documents": documents,
    }


def flow_catalog(repository_root: Path) -> dict[str, Any]:
    registry = _registry(repository_root)
    return {
        "schema_version": "myis.dashboard-flow-catalog.v1",
        "flows": [
            {
                "flow_id": item["flow_id"],
                "title": item["title"],
                "detail_url": f"/api/v1/flows/{item['flow_id']}",
            }
            for item in registry["flows"]
        ],
    }


def flow_document(repository_root: Path, flow_id: str) -> dict[str, Any]:
    registry = _registry(repository_root)
    item = next((item for item in registry["flows"] if item["flow_id"] == flow_id), None)
    if item is None:
        raise KeyError(flow_id)
    _, digest = flow_image(repository_root, flow_id)
    return {
        "schema_version": "myis.dashboard-flow.v1",
        "flow_id": flow_id,
        "title": item["title"],
        "image_url": f"/api/v1/flows/{flow_id}/image?sha256={digest}",
        "sha256": digest,
    }


def flow_image(repository_root: Path, flow_id: str) -> tuple[bytes, str]:
    registry = _registry(repository_root)
    item = next((item for item in registry["flows"] if item["flow_id"] == flow_id), None)
    if item is None:
        raise KeyError(flow_id)
    source = _resolve_registry_source(repository_root, item["path"])
    payload = source.read_bytes()
    _validate_svg(payload)
    return payload, hashlib.sha256(payload).hexdigest()


def tool_catalog(repository_root: Path) -> dict[str, Any]:
    registry = _registry(repository_root)
    source = _resolve_registry_source(repository_root, registry["tools"]["source"])
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"tools"} or not isinstance(payload["tools"], dict):
        raise ValueError("tools.lock.yaml has an unsupported shape")
    output = []
    for tool_id, item in sorted(payload["tools"].items()):
        if not isinstance(tool_id, str) or not isinstance(item, dict):
            raise ValueError("tools.lock.yaml tool entries must be mappings")
        output.append(
            {
                "tool_id": tool_id,
                "version": _public_scalar(item.get("version")),
                "commit": _public_scalar(item.get("commit")),
                "license": _public_scalar(item.get("license")),
                "adoption": _public_scalar(item.get("adoption")),
                "repository": _public_scalar(item.get("repository")),
            }
        )
    return {
        "schema_version": "myis.dashboard-tool-catalog.v1",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "tools": output,
        "documents": content_document(repository_root, "tools")["documents"],
    }


def _registry(repository_root: Path) -> dict[str, Any]:
    expected = {
        "schema_version": "myis.dashboard-content-registry.v1",
        "documents": [
            {"content_id": content_id, "title": title, "kind": kind, "path": path}
            for content_id, title, kind, path in DOCUMENTS
        ],
        "flows": [
            {"flow_id": flow_id, "title": title, "path": path}
            for flow_id, title, path in FLOWS
        ],
        "tools": {"source": TOOLS_SOURCE},
        "presentation": {"source": TOPICS_SOURCE},
    }
    relative_path = "dashboard/content_registry.yaml"
    if not (repository_root / relative_path).exists():
        raise ValueError("dashboard content registry is missing")
    path = _resolve_regular_file(repository_root, relative_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload != expected:
        raise ValueError("dashboard content registry drifted from the backend exact allowlist")
    return expected


def _project_markdown(
    repository_root: Path, relative_path: str, *, source_id: str, title: str
) -> dict[str, Any]:
    source = _resolve_registry_source(repository_root, relative_path)
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    if _UNSAFE_HTML.search(text):
        raise ValueError(f"allowlisted dashboard content contains unsafe HTML: {relative_path}")
    sections: list[dict[str, Any]] = []
    current = {"heading": source.name, "level": 0, "body": []}
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            if current["body"] or current["level"] != 0:
                sections.append(
                    {**current, "body": "\n".join(current["body"]).strip()}
                )
            current = {"heading": match.group(2).strip(), "level": len(match.group(1)), "body": []}
        else:
            current["body"].append(line)
    if current["body"] or current["level"] != 0:
        sections.append({**current, "body": "\n".join(current["body"]).strip()})
    return {
        "source_id": source_id,
        "title": title,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sections": sections,
    }


def _resolve_registry_source(repository_root: Path, relative_path: str) -> Path:
    allowed = {item[3] for item in DOCUMENTS} | {item[2] for item in FLOWS}
    if relative_path not in allowed:
        raise PermissionError("dashboard source is not allowlisted")
    return _resolve_regular_file(repository_root, relative_path)


def _resolve_regular_file(repository_root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise PermissionError("dashboard source path is invalid")
    lexical_root = repository_root.absolute()
    if _is_link_or_reparse(lexical_root):
        raise PermissionError("dashboard repository root cannot be a link or reparse point")
    lexical_target = lexical_root
    for part in relative.parts:
        lexical_target = lexical_target / part
        if _is_link_or_reparse(lexical_target):
            raise PermissionError("dashboard source path contains a link or reparse point")
    root = lexical_root.resolve(strict=True)
    target = lexical_target.resolve(strict=True)
    try:
        target.relative_to(root)
    except ValueError as error:
        raise PermissionError("dashboard source escapes the repository") from error
    if not target.is_file():
        raise PermissionError("dashboard source must be a regular non-symlink file")
    return target


def _is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _validate_svg(payload: bytes) -> None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("allowlisted flow SVG must be UTF-8") from error
    lowered = text.casefold()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise ValueError("allowlisted flow SVG cannot declare a DTD or entity")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("allowlisted flow SVG is not valid XML") from error
    namespace, local_name = _qualified_name(root.tag)
    if local_name != "svg" or namespace not in {None, _SVG_NAMESPACE}:
        raise ValueError("allowlisted flow image must have an SVG root")
    for element in root.iter():
        namespace, local_name = _qualified_name(element.tag)
        if namespace not in {None, _SVG_NAMESPACE}:
            raise ValueError("allowlisted flow SVG uses an external element namespace")
        if local_name.casefold() in _FORBIDDEN_SVG_TAGS:
            raise ValueError("allowlisted flow SVG contains an unsafe element")
        for attribute, value in element.attrib.items():
            _, attribute_name = _qualified_name(attribute)
            normalized_name = attribute_name.casefold()
            normalized_value = value.strip()
            if normalized_name.startswith("on"):
                raise ValueError("allowlisted flow SVG contains an event handler")
            if normalized_name in {"href", "src"} and not normalized_value.startswith("#"):
                raise ValueError("allowlisted flow SVG contains an external reference")
            if _UNSAFE_SVG_VALUE.search(normalized_value) and not _SAFE_FRAGMENT_URL.fullmatch(
                normalized_value
            ):
                raise ValueError("allowlisted flow SVG contains an unsafe attribute value")


def _qualified_name(value: str) -> tuple[str | None, str]:
    if value.startswith("{") and "}" in value:
        namespace, local_name = value[1:].split("}", 1)
        return namespace, local_name
    return None, value


def _public_scalar(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("public tool metadata must be scalar")
    text = str(value)
    if len(text) > 500 or _UNSAFE_HTML.search(text):
        raise ValueError("public tool metadata is unsafe")
    return text
