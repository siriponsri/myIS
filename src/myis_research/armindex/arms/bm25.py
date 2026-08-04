"""Honest fixture-only ARM-01 wrapper around the existing kernel BM25."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ...kernel.canonical import canonical_sha256
from ...kernel.p1 import BM25Index
from ..compiler import CompiledRepresentation, CompiledUnit
from .base import ArmCapabilities, FamilyHit, FamilyRanking


FIXTURE_BACKEND_ID = "kernel_okapi_bm25_fixture_v1"


@dataclass
class BM25FixtureIndex:
    backend: BM25Index
    compiled: CompiledRepresentation
    units: dict[str, CompiledUnit]
    index_sha256: str


class BM25FixtureAdapter:
    """ARM-01 interface proof; not the future frozen bm25s scientific arm."""

    arm_id = "ARM-01"

    def capabilities(self) -> ArmCapabilities:
        return ArmCapabilities(
            arm_id=self.arm_id,
            method="lexical_bm25_fixture",
            fixture_status="runnable_fixture_backend_not_scientific_arm_lock",
            cpu_supported=True,
            gpu_supported=False,
            commercial_status="engineering_fixture_only",
            network_required=False,
            model_downloaded=False,
        )

    def build_index(self, compiled: CompiledRepresentation) -> BM25FixtureIndex:
        if compiled.arm_id != self.arm_id:
            raise ValueError("ARM-01 cannot index a representation compiled for another arm")
        rows = [
            {"doc_id": unit.unit_id, "family_id": unit.family_id, "text": unit.text}
            for unit in compiled.units
        ]
        index_payload = {
            "backend_id": FIXTURE_BACKEND_ID,
            "arm_id": self.arm_id,
            "k1": 1.2,
            "b": 0.75,
            "compiled_representation_sha256": compiled.compiled_representation_sha256,
            "unit_commitment": canonical_sha256(rows),
        }
        return BM25FixtureIndex(
            backend=BM25Index(rows, k1=1.2, b=0.75),
            compiled=compiled,
            units={unit.unit_id: unit for unit in compiled.units},
            index_sha256=canonical_sha256(index_payload),
        )

    def search(
        self,
        index: BM25FixtureIndex,
        *,
        case_id: str,
        text: str,
        top_k: int,
    ) -> FamilyRanking:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        scored_rows = index.backend.rank(text, limit=None)
        scores_by_unit = {unit_id: float(score) for unit_id, _family_id, score in scored_rows}
        unit_rows = sorted(
            (
                (unit.unit_id, unit.family_id, scores_by_unit.get(unit.unit_id, 0.0))
                for unit in index.compiled.units
            ),
            key=lambda item: (-item[2], item[0]),
        )
        unit_rank = {unit_id: rank for rank, (unit_id, _family, _score) in enumerate(unit_rows, start=1)}
        grouped: dict[str, list[tuple[float, CompiledUnit]]] = {}
        for unit_id, family_id, score in unit_rows:
            if not math.isfinite(score):
                raise ValueError("BM25 fixture score must be finite")
            grouped.setdefault(family_id, []).append((float(score), index.units[unit_id]))
        pending: list[tuple[str, float, CompiledUnit, int]] = []
        for family_id, components in sorted(grouped.items()):
            ordered = sorted(
                components,
                key=lambda item: (-item[0], item[1].publication_id, item[1].unit_id),
            )
            score = _aggregate(index.compiled.family_aggregation, [item[0] for item in ordered])
            best_unit = ordered[0][1]
            pending.append((family_id, score, best_unit, len(ordered)))
        pending.sort(key=lambda item: (-item[1], item[0], item[2].publication_id, item[2].unit_id))
        hits = tuple(
            FamilyHit(
                family_id=family_id,
                rank=rank,
                score=round(score, 15),
                publication_id=unit.publication_id,
                unit_id=unit.unit_id,
                component_count=count,
            )
            for rank, (family_id, score, unit, count) in enumerate(pending[:top_k], start=1)
        )
        # Keep the unit-rank materialization explicit: it proves all units were
        # scored before family aggregation and prevents heuristic over-fetch.
        if any(hit.unit_id not in unit_rank for hit in hits):
            raise ValueError("family ranking lost its source unit")
        return FamilyRanking(case_id=case_id, arm_id=self.arm_id, hits=hits)


def _aggregate(rule: str, values: list[float]) -> float:
    if not values:
        raise ValueError("family aggregation requires at least one unit score")
    if rule in {"maxp", "single_unit"}:
        return values[0]
    if rule == "avg_top3":
        selected = values[:3]
        return sum(selected) / len(selected)
    if rule == "top_m":
        selected = values[:2]
        return sum(selected) / len(selected)
    raise ValueError(f"unsupported family aggregation: {rule}")
