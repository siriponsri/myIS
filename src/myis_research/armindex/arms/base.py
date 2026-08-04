"""Retrieval-arm interfaces used by the synthetic ArmIndex fixture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..compiler import CompiledRepresentation


class ArmUnavailableError(RuntimeError):
    """Raised before a declared but unresolved arm can execute."""


@dataclass(frozen=True)
class ArmCapabilities:
    arm_id: str
    method: str
    fixture_status: str
    cpu_supported: bool
    gpu_supported: bool
    commercial_status: str
    network_required: bool
    model_downloaded: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "method": self.method,
            "fixture_status": self.fixture_status,
            "cpu_supported": self.cpu_supported,
            "gpu_supported": self.gpu_supported,
            "commercial_status": self.commercial_status,
            "network_required": self.network_required,
            "model_downloaded": self.model_downloaded,
        }


@dataclass(frozen=True)
class FamilyHit:
    family_id: str
    rank: int
    score: float
    publication_id: str
    unit_id: str
    component_count: int


@dataclass(frozen=True)
class FamilyRanking:
    case_id: str
    arm_id: str
    hits: tuple[FamilyHit, ...]


class ArmAdapter(Protocol):
    arm_id: str

    def capabilities(self) -> ArmCapabilities: ...

    def build_index(self, compiled: CompiledRepresentation) -> Any: ...

    def search(self, index: Any, *, case_id: str, text: str, top_k: int) -> FamilyRanking: ...
