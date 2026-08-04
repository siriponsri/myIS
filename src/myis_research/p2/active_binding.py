"""Fail-closed resolution of the active P2 control-plane sources."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

import yaml

from .contracts import P2ContractError


ACTIVE_P2_SOURCE_RECORDS = (
    "p2_budget_profile",
    "execution_boundary",
    "p2_campaign_revision",
    "p2_evaluator_compatibility",
)


def active_p2_source_uris(repository_root: Path) -> dict[str, str]:
    """Resolve every active P2 authority without historical defaults."""

    root = Path(repository_root).resolve()
    source_path = root / "control/source-of-truth.yaml"
    if source_path.is_symlink() or not source_path.is_file():
        raise P2ContractError("active P2 source-of-truth is missing or unsafe")
    try:
        source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise P2ContractError("cannot load active P2 source-of-truth") from error
    if not isinstance(source, Mapping) or source.get("schema_version") != "myis.source-of-truth.v2":
        raise P2ContractError("active P2 source-of-truth schema is invalid")
    records = source.get("records")
    if not isinstance(records, list):
        raise P2ContractError("active P2 source-of-truth records are invalid")
    by_id = {
        str(item.get("id")): item
        for item in records
        if isinstance(item, Mapping) and item.get("id")
    }
    missing = [record_id for record_id in ACTIVE_P2_SOURCE_RECORDS if record_id not in by_id]
    if missing:
        raise P2ContractError(
            f"active P2 source-of-truth is missing required records: {', '.join(missing)}"
        )
    execution = by_id["execution_boundary"].get("phase_mapping")
    if not isinstance(execution, Mapping):
        raise P2ContractError("active P2 execution phase mapping is invalid")
    values: dict[str, Any] = {
        "profile": by_id["p2_budget_profile"].get("authority"),
        "execution_envelope": execution.get("P2_SCOPE_DEVELOPMENT"),
        "campaign_revision": by_id["p2_campaign_revision"].get("authority"),
        "evaluator_compatibility": by_id["p2_evaluator_compatibility"].get("authority"),
    }
    resolved: dict[str, str] = {}
    for label, raw_uri in values.items():
        uri = _safe_uri(raw_uri, label)
        lexical = root / Path(*PurePosixPath(uri).parts)
        try:
            path = lexical.resolve(strict=True)
            path.relative_to(root)
        except (OSError, ValueError) as error:
            raise P2ContractError(
                f"active P2 {label} source escapes the repository or is missing"
            ) from error
        if (
            os.path.normcase(str(path)) != os.path.normcase(str(lexical.absolute()))
            or not path.is_file()
        ):
            raise P2ContractError(f"active P2 {label} source is missing or unsafe")
        resolved[label] = uri
    return resolved


def _safe_uri(value: Any, label: str) -> str:
    uri = str(value) if isinstance(value, str) else ""
    posix = PurePosixPath(uri)
    windows = PureWindowsPath(uri)
    if (
        not uri
        or posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or ".." in posix.parts
        or "\\" in uri
    ):
        raise P2ContractError(f"active P2 {label} source is not repository-relative")
    return posix.as_posix()
