"""Strict SCOPE-DSL parsing and dataset adapters."""

from .dsl import ScopeSpec, compile_scope as compile_simple_scope, parse_scope
from .models import ScopeSpec as StrictScopeSpec, parse_scope_spec
from .compiler import CompiledScope, CompiledUnit, compile_scope
from .adapters import DapfamAdapter, FinePatentsAdapter

__all__ = ["ScopeSpec", "StrictScopeSpec", "parse_scope", "parse_scope_spec", "compile_scope", "compile_simple_scope", "CompiledScope", "CompiledUnit", "DapfamAdapter", "FinePatentsAdapter"]
