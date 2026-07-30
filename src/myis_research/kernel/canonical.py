"""Canonical serialization and commitments; no runtime-specific fallbacks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_json(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_bytes(value)


def sha256_hex(value: Any) -> str:
    return canonical_sha256(value)


canonical_hash = canonical_sha256


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, value: Any, length: int = 16) -> str:
    if not prefix or not prefix.replace("-", "").isalnum():
        raise ValueError("prefix must be a simple identifier")
    return f"{prefix}-{canonical_sha256(value)[:length]}"
