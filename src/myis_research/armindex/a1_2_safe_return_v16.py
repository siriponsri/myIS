"""Strict aggregate-safe validator for the A1.2 v16 remote return archive.

The archive is deliberately narrower than a worker log: it carries only the
opaque ranking rows required for Owner-local evaluation and one hash-bound
resource receipt per program-arm cell.  Identity mapping and metric
calculation happen only after this validator passes in the protected store.
"""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from ..kernel.canonical import canonical_sha256

ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
CELL_IDS = tuple((arm, program) for arm in ARM_IDS for program in PROGRAM_IDS)
WORK_TOKEN_RE = re.compile(r"^Q-[a-f0-9]{32}$")
FAMILY_TOKEN_RE = re.compile(r"^F-[a-f0-9]{32}$")
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
MAX_MEMBER_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MANIFEST_NAME = "safe-return-manifest.v16.json"
MANIFEST_SCHEMA = "myis.armindex-a1.2-safe-return-manifest.v16"
RECEIPT_SCHEMA = "myis.armindex-a1.2-safe-return-resource-receipt.v16"


class SafeReturnV16Error(ValueError):
    """Raised when a remote return is not exactly the frozen safe shape."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes, *, name: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SafeReturnV16Error(f"{name} must be ASCII JSON") from error
    if not isinstance(value, dict):
        raise SafeReturnV16Error(f"{name} must be a JSON object")
    return value


def _path(name: str) -> PurePosixPath:
    value = PurePosixPath(name)
    if value.is_absolute() or ".." in value.parts or "" in value.parts:
        raise SafeReturnV16Error("archive contains an unsafe member path")
    return value


def _hash(value: object, *, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise SafeReturnV16Error(f"{label} must be a lowercase SHA-256")
    return value


def _cell_path(kind: str, arm: str, program: str) -> str:
    safe_program = program.replace("-", "_")
    return f"{kind}s/{arm}--{safe_program}.{'jsonl' if kind == 'ranking' else 'json'}"


def _work_set_hash(tokens: set[str]) -> str:
    return canonical_sha256({"work_tokens": sorted(tokens)})


def _validate_ranking(data: bytes, *, arm: str, program: str) -> tuple[set[str], int]:
    if len(data) > MAX_MEMBER_BYTES:
        raise SafeReturnV16Error("ranking member exceeds the safe size limit")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as error:
        raise SafeReturnV16Error("ranking member is not ASCII text") from error
    rows = [line for line in text.splitlines() if line.strip()]
    if len(rows) != 150:
        raise SafeReturnV16Error("ranking cell does not contain exactly 150 rows")
    work_tokens: set[str] = set()
    for line in rows:
        value = _json(line.encode("ascii"), name="ranking row")
        if set(value) != {"work_token", "family_tokens"}:
            raise SafeReturnV16Error("ranking row has non-aggregate fields")
        work = value["work_token"]
        if not isinstance(work, str) or WORK_TOKEN_RE.fullmatch(work) is None or work in work_tokens:
            raise SafeReturnV16Error("ranking work-token domain is invalid")
        family_tokens = value["family_tokens"]
        if not isinstance(family_tokens, list) or len(family_tokens) != 100:
            raise SafeReturnV16Error("ranking row must contain exactly 100 family tokens")
        if len(set(family_tokens)) != 100 or any(
            not isinstance(token, str) or FAMILY_TOKEN_RE.fullmatch(token) is None
            for token in family_tokens
        ):
            raise SafeReturnV16Error("ranking family-token domain is invalid")
        work_tokens.add(work)
    return work_tokens, len(rows)


def _validate_receipt(data: bytes, *, attempt_id: str, arm: str, program: str, ranking_sha: str) -> None:
    value = _json(data, name="resource receipt")
    expected_keys = {
        "schema_version", "attempt_id", "arm_id", "program_id", "status",
        "checkpoint_sha256", "ranking_sha256", "receipt_sha256",
    }
    if set(value) != expected_keys:
        raise SafeReturnV16Error("resource receipt has non-aggregate fields")
    if value.get("schema_version") != RECEIPT_SCHEMA or value.get("status") != "PASS":
        raise SafeReturnV16Error("resource receipt schema or status is invalid")
    if value.get("attempt_id") != attempt_id or value.get("arm_id") != arm or value.get("program_id") != program:
        raise SafeReturnV16Error("resource receipt cell binding is invalid")
    _hash(value.get("checkpoint_sha256"), label="checkpoint_sha256")
    if value.get("ranking_sha256") != ranking_sha:
        raise SafeReturnV16Error("resource receipt ranking binding is invalid")
    observed = value.get("receipt_sha256")
    if observed != canonical_sha256({key: item for key, item in value.items() if key != "receipt_sha256"}):
        raise SafeReturnV16Error("resource receipt self-hash mismatch")


def validate_safe_return_archive(archive_path: Path) -> dict[str, Any]:
    """Validate all archive bytes before any opaque-token identity mapping."""

    archive = archive_path.resolve()
    if not archive.is_file() or archive.is_symlink():
        raise SafeReturnV16Error("safe-return archive is missing or unsafe")
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        if not members or len(members) != len({member.name for member in members}):
            raise SafeReturnV16Error("archive members are empty or duplicated")
        total = 0
        payloads: dict[str, bytes] = {}
        for member in members:
            path = _path(member.name)
            if not member.isreg() or path.as_posix() != member.name:
                raise SafeReturnV16Error("archive contains a non-regular member")
            if any(fragment in member.name.casefold() for fragment in ("log", "qrel", "membership", "query_id", "provider", "model", "embedding", "cache", "checkpoint")):
                raise SafeReturnV16Error("archive contains a forbidden member name")
            if member.size > MAX_MEMBER_BYTES:
                raise SafeReturnV16Error("archive member exceeds the safe size limit")
            stream = tar.extractfile(member)
            if stream is None:
                raise SafeReturnV16Error("archive member cannot be read")
            data = stream.read(MAX_MEMBER_BYTES + 1)
            if len(data) != member.size or len(data) > MAX_MEMBER_BYTES:
                raise SafeReturnV16Error("archive member size is invalid")
            if b"\x00" in data:
                raise SafeReturnV16Error("archive member contains binary data")
            total += len(data)
            if total > MAX_TOTAL_BYTES:
                raise SafeReturnV16Error("archive exceeds the total safe size limit")
            payloads[member.name] = data
        if MANIFEST_NAME not in payloads:
            raise SafeReturnV16Error("safe-return manifest is missing")
        manifest = _json(payloads[MANIFEST_NAME], name="safe-return manifest")
        required = {"schema_version", "attempt_id", "status", "transfer_manifest_sha256", "split_commitment_sha256", "ephemeral_token_map_sha256", "work_token_set_sha256", "members", "manifest_sha256"}
        if set(manifest) != required or manifest.get("schema_version") != MANIFEST_SCHEMA or manifest.get("status") != "PASS":
            raise SafeReturnV16Error("safe-return manifest schema is invalid")
        attempt_id = manifest.get("attempt_id")
        if not isinstance(attempt_id, str) or ATTEMPT_RE.fullmatch(attempt_id) is None:
            raise SafeReturnV16Error("safe-return attempt identity is invalid")
        for key in ("transfer_manifest_sha256", "split_commitment_sha256", "ephemeral_token_map_sha256"):
            _hash(manifest.get(key), label=key)
        if manifest.get("manifest_sha256") != canonical_sha256({key: item for key, item in manifest.items() if key != "manifest_sha256"}):
            raise SafeReturnV16Error("safe-return manifest self-hash mismatch")
        members_spec = manifest.get("members")
        if not isinstance(members_spec, list) or len(members_spec) != 50:
            raise SafeReturnV16Error("safe-return manifest must bind exactly 50 cell members")
        expected_specs: list[tuple[str, str, str]] = []
        for arm, program in CELL_IDS:
            expected_specs.extend((("ranking", arm, program), ("receipt", arm, program)))
        observed_specs: list[tuple[str, str, str]] = []
        observed_member_names: set[str] = set()
        all_work_tokens: set[str] | None = None
        for spec in members_spec:
            if not isinstance(spec, dict) or set(spec) != {"kind", "arm_id", "program_id", "relative_path", "sha256", "size_bytes"}:
                raise SafeReturnV16Error("safe-return member manifest has non-aggregate fields")
            kind, arm, program = spec["kind"], spec["arm_id"], spec["program_id"]
            if (kind, arm, program) not in expected_specs:
                raise SafeReturnV16Error("safe-return member topology is invalid")
            relative = spec["relative_path"]
            if not isinstance(relative, str) or relative != _cell_path(kind, arm, program) or relative in observed_member_names:
                raise SafeReturnV16Error("safe-return member path is invalid")
            if relative not in payloads:
                raise SafeReturnV16Error("safe-return member is missing from archive")
            _hash(spec.get("sha256"), label="safe-return member hash")
            if spec["size_bytes"] != len(payloads[relative]) or spec["sha256"] != _sha256(payloads[relative]):
                raise SafeReturnV16Error("safe-return member bytes do not match manifest")
            observed_member_names.add(relative)
            observed_specs.append((kind, arm, program))
            if kind == "ranking":
                work_tokens, _ = _validate_ranking(payloads[relative], arm=arm, program=program)
                if all_work_tokens is None:
                    all_work_tokens = work_tokens
                elif work_tokens != all_work_tokens:
                    raise SafeReturnV16Error("ranking cells do not share one work-token set")
            else:
                _validate_receipt(payloads[relative], attempt_id=attempt_id, arm=arm, program=program, ranking_sha=_sha256(payloads[_cell_path("ranking", arm, program)]))
        if sorted(observed_specs) != sorted(expected_specs) or set(payloads) != {MANIFEST_NAME, *observed_member_names}:
            raise SafeReturnV16Error("archive has missing or extra safe-return members")
        if all_work_tokens is None or len(all_work_tokens) != 150 or manifest["work_token_set_sha256"] != _work_set_hash(all_work_tokens):
            raise SafeReturnV16Error("safe-return work-token commitment is invalid")
    return {"status": "PASS", "attempt_id": attempt_id, "cells": 25, "rows": 150, "top_k": 100, "archive_sha256": _sha256(archive.read_bytes()), "archive_bytes": archive.stat().st_size}


__all__ = ["SafeReturnV16Error", "validate_safe_return_archive"]
