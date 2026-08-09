"""Build the strict aggregate-safe A1.2 v16 return archive.

The measured runner writes an Owner-local staging directory containing opaque
ranking rows and rich local receipts.  This builder is the only bridge that
turns that staging state into the 51-member archive accepted by
``a1_2_safe_return_v16``.  It deliberately drops scores and all local control
metadata from the returned payload.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import tarfile
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256
from .a1_2_safe_return_v16 import (
    ARM_IDS,
    MANIFEST_NAME,
    PROGRAM_IDS,
    validate_safe_return_archive,
)

CELL_IDS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in PROGRAM_IDS)
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
TOKEN_RE = re.compile(r"^[FQ]-[a-f0-9]{32}$")
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")


class SafeReturnBuilderV16Error(ValueError):
    """Raised for incomplete or unsafe Owner-local runner output."""


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise SafeReturnBuilderV16Error(f"{role} must be a lowercase SHA-256")
    return value


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SafeReturnBuilderV16Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise SafeReturnBuilderV16Error(f"{role} must be a JSON object")
    return value


def _read_ranking(path: Path, *, cell: str) -> tuple[str, set[str]]:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise SafeReturnBuilderV16Error(f"ranking is unavailable for {cell}") from error
    if len(lines) != 150:
        raise SafeReturnBuilderV16Error(f"ranking row count is not 150 for {cell}")
    work_tokens: set[str] = set()
    normalized: list[str] = []
    for line in lines:
        try:
            value = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise SafeReturnBuilderV16Error(f"ranking row is invalid for {cell}") from error
        if not isinstance(value, Mapping) or set(value) != {"work_token", "family_tokens"}:
            raise SafeReturnBuilderV16Error(f"ranking row is not aggregate-safe for {cell}")
        work = value["work_token"]
        families = value["family_tokens"]
        if not isinstance(work, str) or TOKEN_RE.fullmatch(work) is None or not work.startswith("Q-") or work in work_tokens:
            raise SafeReturnBuilderV16Error(f"ranking work-token domain is invalid for {cell}")
        if not isinstance(families, list) or len(families) != 100 or len(set(families)) != 100 or any(not isinstance(item, str) or TOKEN_RE.fullmatch(item) is None or not item.startswith("F-") for item in families):
            raise SafeReturnBuilderV16Error(f"ranking family-token domain is invalid for {cell}")
        work_tokens.add(work)
        normalized.append(json.dumps({"work_token": work, "family_tokens": families}, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return "\n".join(normalized) + "\n", work_tokens


def _member_name(kind: str, cell: str) -> str:
    arm, program = cell.split("--", 1)
    program_name = program.replace("-", "_")
    return f"{kind}s/{arm}--{program_name}.{'jsonl' if kind == 'ranking' else 'json'}"


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    if path.exists():
        if path.read_text(encoding="ascii") != payload:
            raise SafeReturnBuilderV16Error(f"immutable file differs: {path.name}")
        return
    path.write_text(payload, encoding="ascii", newline="")


def _tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.mode = 0o644
    return info


def build_safe_return_archive(
    *,
    runner_output_root: Path,
    attempt_id: str,
    archive_path: Path,
    transfer_manifest_sha256: str,
    split_commitment_sha256: str,
    ephemeral_token_map_sha256: str,
    checkpoint_sha256_by_cell: Mapping[str, str],
) -> dict[str, Any]:
    """Package one complete v16 runner attempt and validate it before return."""

    if not isinstance(attempt_id, str) or ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise SafeReturnBuilderV16Error("attempt_id is invalid")
    for value, role in ((transfer_manifest_sha256, "transfer manifest"), (split_commitment_sha256, "split commitment"), (ephemeral_token_map_sha256, "token map")):
        _hash(value, role=role)
    if set(checkpoint_sha256_by_cell) != set(CELL_IDS):
        raise SafeReturnBuilderV16Error("checkpoint map must cover all 25 cells")
    for cell, value in checkpoint_sha256_by_cell.items():
        if cell not in CELL_IDS:
            raise SafeReturnBuilderV16Error("checkpoint map contains an unknown cell")
        _hash(value, role=f"checkpoint {cell}")
    root = runner_output_root.resolve(strict=True)
    attempt_root = (root / attempt_id).resolve(strict=True)
    if not attempt_root.is_dir() or attempt_root.is_symlink() or not attempt_root.is_relative_to(root):
        raise SafeReturnBuilderV16Error("runner output root is unsafe")
    ranking_root = attempt_root / "rankings"
    receipt_root = attempt_root / "receipts"
    if not ranking_root.is_dir() or not receipt_root.is_dir():
        raise SafeReturnBuilderV16Error("runner output is incomplete")

    with tempfile.TemporaryDirectory(prefix=f".safe-return-{attempt_id}-") as temporary:
        staging = Path(temporary)
        members: list[dict[str, Any]] = []
        all_work_tokens: set[str] | None = None
        for cell in CELL_IDS:
            source = ranking_root / f"{cell}.jsonl"
            payload, work_tokens = _read_ranking(source, cell=cell)
            if all_work_tokens is None:
                all_work_tokens = work_tokens
            elif work_tokens != all_work_tokens:
                raise SafeReturnBuilderV16Error("ranking cells do not share one work-token set")
            ranking_name = _member_name("ranking", cell)
            target = staging / ranking_name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding="ascii", newline="")
            members.append({"kind": "ranking", "arm_id": cell.split("--", 1)[0], "program_id": cell.split("--", 1)[1], "relative_path": ranking_name, "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(), "size_bytes": len(payload.encode("ascii"))})

            local_receipt = _load(receipt_root / f"{cell}.json", role=f"runner receipt {cell}")
            if local_receipt.get("status") != "PASS" or local_receipt.get("cell_id") != cell or local_receipt.get("ranking_file_sha256") != members[-1]["sha256"]:
                raise SafeReturnBuilderV16Error(f"runner receipt does not bind ranking for {cell}")
            receipt_name = _member_name("receipt", cell)
            receipt_body = {"schema_version": "myis.armindex-a1.2-safe-return-resource-receipt.v16", "attempt_id": attempt_id, "arm_id": members[-1]["arm_id"], "program_id": members[-1]["program_id"], "status": "PASS", "checkpoint_sha256": checkpoint_sha256_by_cell[cell], "ranking_sha256": members[-1]["sha256"]}
            receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
            _write_json(staging / receipt_name, receipt)
            receipt_bytes = (staging / receipt_name).read_bytes()
            members.append({"kind": "receipt", "arm_id": members[-1]["arm_id"], "program_id": members[-1]["program_id"], "relative_path": receipt_name, "sha256": hashlib.sha256(receipt_bytes).hexdigest(), "size_bytes": len(receipt_bytes)})
        if all_work_tokens is None or len(all_work_tokens) != 150:
            raise SafeReturnBuilderV16Error("work-token set is incomplete")
        manifest_body = {"schema_version": "myis.armindex-a1.2-safe-return-manifest.v16", "attempt_id": attempt_id, "status": "PASS", "transfer_manifest_sha256": transfer_manifest_sha256, "split_commitment_sha256": split_commitment_sha256, "ephemeral_token_map_sha256": ephemeral_token_map_sha256, "work_token_set_sha256": canonical_sha256({"work_tokens": sorted(all_work_tokens)}), "members": members}
        manifest = {**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}
        _write_json(staging / MANIFEST_NAME, manifest)
        destination = archive_path.resolve()
        if destination.exists():
            raise SafeReturnBuilderV16Error("archive output already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_archive = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
        try:
            with temporary_archive.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed, tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for path in sorted(staging.rglob("*")):
                    if path.is_file():
                        bundle.add(path, arcname=path.relative_to(staging).as_posix(), recursive=False, filter=_tar_filter)
            os.replace(temporary_archive, destination)
        finally:
            temporary_archive.unlink(missing_ok=True)
    facts = validate_safe_return_archive(destination)
    return {"status": "PASS", "attempt_id": attempt_id, "cells": facts["cells"], "rows": facts["rows"], "top_k": facts["top_k"], "archive_sha256": facts["archive_sha256"], "archive_bytes": facts["archive_bytes"]}


__all__ = ["SafeReturnBuilderV16Error", "build_safe_return_archive"]
