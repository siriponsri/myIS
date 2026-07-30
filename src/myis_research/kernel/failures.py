from __future__ import annotations

from enum import StrEnum


class FailureCategory(StrEnum):
    SOURCE = "source"
    IDENTITY = "identity"
    SPLIT_LEAKAGE = "split_leakage"
    PARSER = "parser"
    COMPILER = "compiler"
    EVALUATOR = "evaluator"
    PROTECTED_BOUNDARY = "protected_boundary"
    RESOURCE = "resource"
    PROVENANCE = "provenance"


class KernelFailure(ValueError):
    def __init__(self, category: FailureCategory, message: str):
        self.category = category
        super().__init__(f"{category.value}: {message}")
