"""Compatibility names for the single active SCOPE-DSL v1 runtime.

Older callers imported ``parse_scope`` from this module.  The implementation
now delegates to the strict Pydantic v1 contract; no second parser/compiler is
kept active.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import ScopeSpec, parse_scope_spec


def parse_scope(payload: Mapping[str, Any]) -> ScopeSpec:
    return parse_scope_spec(payload)


def compile_scope(spec: ScopeSpec | Mapping[str, Any], record: Mapping[str, Any]) -> list[dict[str, Any]]:
    from .compiler import compile_scope as compile_strict

    compiled = compile_strict(spec, [record])
    return [unit.as_dict() for unit in compiled.units]
