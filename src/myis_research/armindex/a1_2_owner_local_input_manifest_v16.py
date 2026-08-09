"""Materialize the Owner-local v16 measured-input manifest.

The v15 compiler remains the authority for compiled bytes.  This module only
binds their relative paths and hashes to the five-gate v16 runner interface;
it never copies protected data into the repository or into a remote bundle.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256

ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
PROGRAM_IDS = ("P00-TAC-DOC", "P01-TA-DOC", "P02-CLAIM1", "P03-PASSAGE", "P04-SECTION-MULTIVIEW")
EXECUTABLE_PROGRAM_IDS = {program: ("P02-FIRST-CLAIM" if program == "P02-CLAIM1" else program) for program in PROGRAM_IDS}
CELL_IDS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in PROGRAM_IDS)
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
FORBIDDEN_PATH = re.compile(r"(?:qrels|membership|query[_-]?ids?|credential|secret|token[_-]?map|embedding|provider[_-]?payload|model[_-]?weights)", re.IGNORECASE)
MANIFEST_SCHEMA = "myis.armindex-a1.2-owner-local-measured-input-manifest.v16"


class OwnerLocalInputManifestV16Error(ValueError):
    """Raised when v15 compiled inputs cannot be bound safely."""


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise OwnerLocalInputManifestV16Error(f"{role} hash is invalid")
    return value


def _safe_relative(root: Path, relative: object, *, role: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts or FORBIDDEN_PATH.search(relative):
        raise OwnerLocalInputManifestV16Error(f"{role} path is unsafe")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except OSError as error:
        raise OwnerLocalInputManifestV16Error(f"{role} is unavailable") from error
    if candidate.is_symlink() or not resolved.is_file() or not resolved.is_relative_to(root) or metadata.st_mode & 0o170000 != 0o100000:
        raise OwnerLocalInputManifestV16Error(f"{role} is unsafe")
    return resolved


def _write(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="ascii") != payload:
            raise OwnerLocalInputManifestV16Error("immutable input manifest differs")
        return
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_input_manifest(
    *,
    root: Path,
    output: Path,
    attempt_id: str,
    gates: Mapping[str, str],
    work_token_path: str,
    cells: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind exactly 25 compiled v15 cells without exposing protected values."""

    owner_root = root.resolve(strict=True)
    if not owner_root.is_dir() or owner_root.is_symlink() or not isinstance(attempt_id, str) or ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise OwnerLocalInputManifestV16Error("Owner-local root or attempt identity is invalid")
    required_gates = ("provider_admission", "execution_adoption", "watchdog_ttl", "protected_boundary", "frozen_bindings")
    if not isinstance(gates, Mapping) or any(gates.get(name) != "PASS" for name in required_gates):
        raise OwnerLocalInputManifestV16Error("all v16 admission gates must be PASS")
    if len(cells) != 25:
        raise OwnerLocalInputManifestV16Error("exactly 25 compiled cells are required")
    work = _safe_relative(owner_root, work_token_path, role="work-token")
    if _hash(file_sha256(work), role="work-token") != file_sha256(work):
        raise OwnerLocalInputManifestV16Error("work-token hash calculation failed")
    observed: set[str] = set()
    normalized_cells: list[dict[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, Mapping):
            raise OwnerLocalInputManifestV16Error("cell binding is invalid")
        required = {"cell_id", "arm_id", "program_id", "binding_path", "corpus_path", "query_path"}
        if set(cell) != required:
            raise OwnerLocalInputManifestV16Error("cell binding keys are invalid")
        cell_id, arm, program = cell["cell_id"], cell["arm_id"], cell["program_id"]
        if cell_id not in CELL_IDS or cell_id != f"{arm}--{program}" or cell_id in observed or arm not in ARM_IDS or program not in PROGRAM_IDS:
            raise OwnerLocalInputManifestV16Error("cell topology is invalid")
        binding = _safe_relative(owner_root, cell["binding_path"], role=f"binding {cell_id}")
        corpus = _safe_relative(owner_root, cell["corpus_path"], role=f"corpus {cell_id}")
        query = _safe_relative(owner_root, cell["query_path"], role=f"query {cell_id}")
        normalized_cells.append({"cell_id": cell_id, "arm_id": arm, "program_id": program, "executable_program_id": EXECUTABLE_PROGRAM_IDS[program], "binding_path": Path(cell["binding_path"]).as_posix(), "binding_sha256": file_sha256(binding), "corpus_path": Path(cell["corpus_path"]).as_posix(), "corpus_sha256": file_sha256(corpus), "query_path": Path(cell["query_path"]).as_posix(), "query_sha256": file_sha256(query)})
        observed.add(cell_id)
    if observed != set(CELL_IDS):
        raise OwnerLocalInputManifestV16Error("cell topology is incomplete")
    body = {"schema_version": MANIFEST_SCHEMA, "status": "READY", "attempt_id": attempt_id, "gates": dict(gates), "cells": sorted(normalized_cells, key=lambda item: CELL_IDS.index(item["cell_id"])), "work_tokens": {"path": Path(work_token_path).as_posix(), "sha256": file_sha256(work), "count": 150}}
    manifest = {**body, "manifest_sha256": canonical_sha256(body)}
    _write(output.resolve(), manifest)
    return {"status": "PASS", "attempt_id": attempt_id, "cells": 25, "work_token_count": 150, "manifest_sha256": manifest["manifest_sha256"], "manifest_path": output.resolve().as_posix()}


__all__ = ["OwnerLocalInputManifestV16Error", "build_input_manifest"]
