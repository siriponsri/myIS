from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonical_sha256


class RunManifest:
    """Immutable hash-bound wrapper for a run payload."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        body = dict(payload)
        self.payload = MappingProxyType(body)
        self.sha256 = canonical_sha256(body)

    def as_dict(self) -> dict[str, Any]:
        return dict(self.payload)
