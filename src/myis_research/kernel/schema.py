"""Dependency-free strict checks for the active JSON contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class SchemaViolation(ValueError):
    """Raised when an active contract is missing or has unknown fields."""


def exact_object(value: Any, *, required: set[str], optional: set[str] = (), name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaViolation(f"{name} must be an object")
    keys = set(value)
    unknown = keys - required - optional
    missing = required - keys
    if unknown:
        raise SchemaViolation(f"{name} has unknown fields: {sorted(unknown)}")
    if missing:
        raise SchemaViolation(f"{name} is missing fields: {sorted(missing)}")
    return dict(value)


def string(value: Any, *, field: str, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise SchemaViolation(f"{field} must be a non-empty string")
    return value


def integer(value: Any, *, field: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaViolation(f"{field} must be an integer")
    if minimum is not None and value < minimum:
        raise SchemaViolation(f"{field} must be >= {minimum}")
    return value


def sequence(value: Any, *, field: str) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise SchemaViolation(f"{field} must be an array")
    return list(value)


def mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaViolation(f"{field} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise SchemaViolation(f"{field} keys must be strings")
    return dict(value)

