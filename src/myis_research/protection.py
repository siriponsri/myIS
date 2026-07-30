"""Fail-closed protected-surface and aggregate-only boundary checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePath
from typing import Any, Iterable, Mapping


class DataScope(StrEnum):
    FIXTURE = "fixture"
    ADAPTATION = "adaptation"
    SELECTION = "selection"
    CONFIRMATION_REQUEST = "confirmation_request"


PROTECTED_PATH_PARTS = {
    "qrels",
    "confirmation",
    "held-out",
    "held_out",
    "split-membership",
    "split_membership",
    "per-query-confirmation",
    "per_query_confirmation",
    "credentials",
    "secrets",
}

PROTECTED_PAYLOAD_KEYS = {
    "query_id",
    "query_ids",
    "confirmation_ids",
    "qrels",
    "split_membership",
    "per_query",
    "per_query_outcomes",
    "protected_payload",
    "credentials",
    "api_key",
    "secret",
    "password",
}

C1_EDITABLE_SURFACES = (
    "routes.enabled",
    "routes.quota",
    "fusion",
    "fusion_k",
    "weights",
    "retrieval_depth",
    "rerank_depth",
)

C1_PROTECTED_SURFACES = (
    "query_views",
    "candidate_budget",
    "stopping",
    "prompt",
    "encoder",
    "reranker_instructions",
    "evaluator",
    "split",
    "confirmation",
    "corpus",
    "governance",
    "manifest_validation",
)


@dataclass(frozen=True)
class PatchSurfacePolicy:
    editable_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]

    def validate(self) -> None:
        editable = {_normalize_path(path) for path in self.editable_paths}
        protected = {_normalize_path(path) for path in self.protected_paths}
        if editable & protected:
            raise ValueError(f"editable and protected paths overlap: {sorted(editable & protected)}")
        if len(editable) != len(self.editable_paths) or len(protected) != len(self.protected_paths):
            raise ValueError("patch surfaces must be unique")

    def validate_changed_paths(self, changed_paths: Iterable[str]) -> None:
        self.validate()
        editable = tuple(_normalize_path(path).rstrip("/") for path in self.editable_paths)
        protected = tuple(_normalize_path(path).rstrip("/") for path in self.protected_paths)
        violations = []
        for raw_path in changed_paths:
            path = _normalize_path(raw_path)
            if _matches_prefix(path, protected) or not _matches_prefix(path, editable):
                violations.append(raw_path)
        if violations:
            raise PermissionError(f"patch changes paths outside the editable surface: {sorted(violations)}")


def c1_patch_surface_policy() -> PatchSurfacePolicy:
    """Return the exact C1 tuning boundary from the frozen Track C protocol."""

    return PatchSurfacePolicy(C1_EDITABLE_SURFACES, C1_PROTECTED_SURFACES)


def _normalize_path(path: str) -> str:
    normalized = PurePath(path.replace("\\", "/")).as_posix().lstrip("./")
    return normalized.casefold()


def _matches_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)


def assert_agent_scope(scope: str | DataScope) -> DataScope:
    try:
        resolved = scope if isinstance(scope, DataScope) else DataScope(scope.casefold())
    except ValueError as error:
        raise PermissionError(f"unsupported agent data scope: {scope!r}") from error
    if resolved not in {DataScope.FIXTURE, DataScope.ADAPTATION, DataScope.SELECTION, DataScope.CONFIRMATION_REQUEST}:
        raise PermissionError("protected confirmation data cannot enter the agent workspace")
    return resolved


def assert_path_not_protected(path: str) -> None:
    parts = set(_normalize_path(path).split("/"))
    if parts & PROTECTED_PATH_PARTS:
        raise PermissionError(f"protected path is inaccessible to the agent: {path}")


def _is_hash_key(key: str) -> bool:
    normalized = key.casefold()
    return normalized.endswith("_sha256") or normalized.endswith("_hash") or normalized.endswith("_commitment")


def assert_aggregate_only(value: Any, *, path: str = "$") -> None:
    """Reject confirmation IDs, qrels, per-query rows, or credentials recursively."""

    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = key.casefold()
            if normalized in PROTECTED_PAYLOAD_KEYS and not _is_hash_key(normalized):
                raise ValueError(f"protected payload key is forbidden at {path}.{key}")
            assert_aggregate_only(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_aggregate_only(item, path=f"{path}[{index}]")


def assert_hash_only_mapping(values: Mapping[str, str], *, name: str) -> None:
    if not values:
        raise ValueError(f"{name} cannot be empty")
    for key, value in values.items():
        if not key.strip() or len(value) != 64:
            raise ValueError(f"{name} must contain named SHA-256 values")
        try:
            int(value, 16)
        except ValueError as error:
            raise ValueError(f"{name} must contain named SHA-256 values") from error
