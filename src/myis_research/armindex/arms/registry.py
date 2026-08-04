"""Fail-closed five-arm registry for offline synthetic validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..compiler import CompiledRepresentation
from .base import ArmAdapter, ArmCapabilities, ArmUnavailableError
from .bm25 import BM25FixtureAdapter


ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
_DENSE_ARMS = {
    "ARM-02": ("dense_embedding", "commercial_capable"),
    "ARM-03": ("patent_dense_embedding", "research_non_commercial"),
    "ARM-04": ("dense_embedding", "commercial_capable"),
    "ARM-05": ("instruction_dense_embedding", "commercial_capable"),
}


@dataclass(frozen=True)
class UnavailableDenseAdapter:
    arm_id: str
    method: str
    commercial_status: str

    def capabilities(self) -> ArmCapabilities:
        return ArmCapabilities(
            arm_id=self.arm_id,
            method=self.method,
            fixture_status="declared_unresolved_model_not_downloaded",
            cpu_supported=False,
            gpu_supported=False,
            commercial_status=self.commercial_status,
            network_required=False,
            model_downloaded=False,
        )

    def build_index(self, compiled: CompiledRepresentation) -> Any:
        del compiled
        raise ArmUnavailableError(
            f"{self.arm_id} is metadata-only; model resolution/download is forbidden in this fixture"
        )

    def search(self, index: Any, *, case_id: str, text: str, top_k: int) -> Any:
        del index, case_id, text, top_k
        raise ArmUnavailableError(
            f"{self.arm_id} is metadata-only; search is blocked before model or network access"
        )


class ArmRegistry:
    def __init__(self) -> None:
        adapters: dict[str, ArmAdapter] = {"ARM-01": BM25FixtureAdapter()}
        adapters.update(
            {
                arm_id: UnavailableDenseAdapter(arm_id, method, commercial)
                for arm_id, (method, commercial) in _DENSE_ARMS.items()
            }
        )
        if tuple(adapters) != ARM_IDS:
            raise ValueError("ArmIndex fixture registry must contain five ordered arms")
        self._adapters = adapters

    def get(self, arm_id: str) -> ArmAdapter:
        try:
            return self._adapters[arm_id]
        except KeyError as error:
            raise KeyError(f"unknown ArmIndex arm: {arm_id}") from error

    def capabilities(self) -> tuple[ArmCapabilities, ...]:
        return tuple(self._adapters[arm_id].capabilities() for arm_id in ARM_IDS)
