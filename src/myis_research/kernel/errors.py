"""Typed fail-closed error categories."""

from __future__ import annotations

from enum import StrEnum


class FailureCategory(StrEnum):
    SCHEMA = "schema"
    IDENTITY = "identity"
    PROVENANCE = "provenance"
    CONSTRAINT = "constraint"
    INTEGRITY = "integrity"
    DETERMINISM = "determinism"
    PROTECTED_BOUNDARY = "protected_boundary"


class KernelContractError(ValueError):
    """A contract violation that must stop execution."""

    def __init__(self, message: str, category: FailureCategory = FailureCategory.SCHEMA) -> None:
        super().__init__(message)
        self.category = category
