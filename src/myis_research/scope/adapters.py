from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..kernel.failures import FailureCategory, KernelFailure
from ..kernel.errors import FailureCategory as ContractFailureCategory, KernelContractError
from .models import ScopeSpec


class DapfamAdapter:
    name = "dapfam"
    max_searchable_units = 4
    max_searchable_units_per_family = 4

    def validate_units(self, units: Iterable[Mapping[str, object]]) -> None:
        rows = list(units)
        counts: dict[str, int] = {}
        for unit in rows:
            family = str(unit.get("family_id", ""))
            if not family or not str(unit.get("publication_id", "")) or not str(unit.get("source_hash", "")):
                raise KernelContractError("DAPFAM unit lost family/publication/source commitment", ContractFailureCategory.IDENTITY)
            if unit.get("searchable"):
                counts[family] = counts.get(family, 0) + 1
        if any(count > self.max_searchable_units for count in counts.values()):
            raise KernelContractError("DAPFAM record exceeds four searchable units", ContractFailureCategory.CONSTRAINT)

    def compile(self, spec: ScopeSpec, record: Mapping[str, object]) -> list[dict[str, object]]:
        from .compiler import compile_scope

        units = [unit.as_dict() for unit in compile_scope(spec, [record], adapter=self).units]
        searchable = [unit for unit in units if unit["searchable"]]
        if len(searchable) > self.max_searchable_units:
            raise KernelFailure(FailureCategory.COMPILER, "DAPFAM record exceeds four searchable units")
        if any(not unit["family_id"] or not unit["publication_id"] for unit in units):
            raise KernelFailure(FailureCategory.IDENTITY, "DAPFAM unit lost family/publication identity")
        return units


class FinePatentsAdapter:
    name = "fine-patents"

    @staticmethod
    def official_commitment(passages: Iterable[Mapping[str, object]]) -> str:
        from ..kernel.canonical import canonical_sha256

        return canonical_sha256([dict(item) for item in passages])

    def validate_generated_units(self, official: Iterable[Mapping[str, object]], generated: Iterable[Mapping[str, object]]) -> None:
        official_rows = [dict(row) for row in official]
        official_ids = [str(row.get("passage_id", "")) for row in official_rows]
        orders = [int(row.get("order", index)) for index, row in enumerate(official_rows)]
        if len(set(official_ids)) != len(official_ids) or any(not item for item in official_ids):
            raise KernelContractError("official FiNE passage IDs are not unique", ContractFailureCategory.INTEGRITY)
        if orders != list(range(len(official_rows))):
            raise KernelContractError("official FiNE passage order is not stable", ContractFailureCategory.INTEGRITY)
        for unit in generated:
            mapped = [str(item) for item in (unit.get("official_passage_ids") or [])]
            if not mapped:
                raise KernelContractError("generated FiNE unit must map to an official passage", ContractFailureCategory.PROVENANCE)
            if any(item not in official_ids for item in mapped):
                raise KernelContractError("generated FiNE unit maps to an unknown official passage", ContractFailureCategory.INTEGRITY)

    def validate_official_passages(
        self,
        official: Iterable[Mapping[str, object]],
        candidate: Iterable[Mapping[str, object]] | None = None,
        *,
        expected_passages: Iterable[Mapping[str, object]] | None = None,
    ) -> list[dict[str, object]]:
        official_rows = [dict(row) for row in official]
        candidate_rows = [dict(row) for row in (expected_passages if expected_passages is not None else candidate or [])]
        expected = [(str(row.get("passage_id")), str(row.get("text", "")), int(row.get("order", index))) for index, row in enumerate(official_rows)]
        observed = [(str(row.get("passage_id")), str(row.get("text", "")), int(row.get("order", index))) for index, row in enumerate(candidate_rows) if row.get("official", True)]
        if observed != expected:
            raise KernelContractError("FiNE official passage IDs/order/text cannot be merged, dropped, or renumbered", ContractFailureCategory.INTEGRITY)
        return candidate_rows

    def compile_additional_view(self, spec: ScopeSpec, record: Mapping[str, object], official: Iterable[Mapping[str, object]]) -> dict[str, object]:
        official_rows = [dict(row) for row in official]
        from .compiler import compile_scope

        units = [unit.as_dict() for unit in compile_scope(spec, [record], adapter=self, official_passages=official_rows).units]
        for unit in units:
            unit["official_passage_ids"] = [str(row["passage_id"]) for row in official_rows]
            unit["official_view"] = False
        return {"official_passages": official_rows, "generated_units": units}
