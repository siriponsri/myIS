from __future__ import annotations

import pytest

from myis_research.kernel import RunManifest, canonical_json, sha256_hex
from myis_research.kernel.errors import FailureCategory, KernelContractError
from myis_research.scope import FinePatentsAdapter, compile_scope, parse_scope_spec


def scope_spec(*, views: list[dict] | None = None) -> dict:
    return {
        "schema_version": "myis.scope-dsl.v1",
        "spec_id": "spec-fixture-v01",
        "parent_spec_id": None,
        "hypothesis_id": "hyp-i01-001",
        "compiler_api_version": "1.0.0",
        "description": {"title": "fixture", "purpose": "contract"},
        "fields": [
            {"field_id": "family_id", "source": "family_id", "role": "identity"},
            {"field_id": "publication_id", "source": "publication_id", "role": "identity"},
            {"field_id": "title", "source": "title", "role": "text"},
            {"field_id": "abstract", "source": "abstract", "role": "text"},
        ],
        "claims": {"source": "claims"},
        "graph": {},
        "views": views
        or [
            {
                "view_id": "tac",
                "kind": "document",
                "source_fields": ["title", "abstract"],
                "family_field": "family_id",
                "publication_field": "publication_id",
                "span_scheme": "field-v1",
                "compiler_version": "1.0.0",
                "normalization_version": "1.0.0",
            }
        ],
        "aggregation": {"unit": "family", "rule": "maxp"},
        "constraints": {
            "require_source_grounding": True,
            "abstractive_summaries": False,
            "query_specific_vocabulary": False,
            "adapter_limits": {"dapfam": 4},
        },
    }


def test_canonical_bytes_and_manifest_are_stable_and_immutable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert sha256_hex({"b": 2, "a": 1}) == sha256_hex({"a": 1, "b": 2})
    first = RunManifest({"run_id": "r1", "units": [{"id": "u1"}]})
    second = RunManifest({"units": [{"id": "u1"}], "run_id": "r1"})
    assert first.sha256 == second.sha256
    with pytest.raises(TypeError):
        first.payload["run_id"] = "r2"  # type: ignore[index]


def test_scope_compilation_is_byte_stable() -> None:
    rows = [
        {"family_id": "f2", "publication_id": "p2", "title": "B", "abstract": "second"},
        {"family_id": "f1", "publication_id": "p1", "title": "A", "abstract": "first"},
    ]
    first = compile_scope(scope_spec(), rows)
    second = compile_scope(scope_spec(), list(reversed(rows)))
    assert first.as_dict() == second.as_dict()
    assert first.output_hash == sha256_hex([unit.as_dict() for unit in first.units])


def test_dapfam_four_unit_limit_is_adapter_specific() -> None:
    views = [
        {
            "view_id": f"v{i}",
            "kind": "document",
            "source_fields": ["title"],
            "family_field": "family_id",
            "publication_field": "publication_id",
            "span_scheme": "field-v1",
            "compiler_version": "1.0.0",
            "normalization_version": "1.0.0",
        }
        for i in range(5)
    ]
    with pytest.raises(KernelContractError) as error:
        compile_scope(scope_spec(views=views), [{"family_id": "f1", "publication_id": "p1", "title": "text"}])
    assert error.value.category is FailureCategory.CONSTRAINT


def test_fine_preserves_official_passage_universe_and_maps_generated_units() -> None:
    official = [
        {"passage_id": "P0", "text": "alpha", "order": 0},
        {"passage_id": "P1", "text": "beta", "order": 1},
    ]
    generated = [
        {
            "family_id": "f1",
            "publication_id": "p1",
            "title": "generated",
            "abstract": "view",
            "official_passage_ids": ["P0"],
        }
    ]
    compiled = compile_scope(scope_spec(), generated, adapter="fine", official_passages=official)
    assert compiled.units[0].official_passage_ids == ("P0",)
    assert FinePatentsAdapter.official_commitment(official) == FinePatentsAdapter.official_commitment(official)


@pytest.mark.parametrize(
    "bad_official",
    [
        [{"passage_id": "P0", "text": "alpha beta", "order": 0}],  # drop
        [
            {"passage_id": "P0", "text": "alpha", "order": 0},
            {"passage_id": "P1", "text": "beta", "order": 2},
        ],  # renumber
        [{"passage_id": "P0+P1", "text": "alpha beta", "order": 0}],  # merge
    ],
)
def test_fine_merge_drop_and_renumber_fail_closed(bad_official: list[dict]) -> None:
    adapter = FinePatentsAdapter()
    expected = [
        {"passage_id": "P0", "text": "alpha", "order": 0},
        {"passage_id": "P1", "text": "beta", "order": 1},
    ]
    with pytest.raises(KernelContractError) as error:
        adapter.validate_official_passages(expected, expected_passages=bad_official)
    assert error.value.category is FailureCategory.INTEGRITY


def test_scope_schema_rejects_unknown_fields_and_global_four_unit_field() -> None:
    payload = scope_spec()
    payload["unexpected"] = True
    with pytest.raises(Exception):
        parse_scope_spec(payload)
    payload = scope_spec()
    payload["constraints"]["max_searchable_units_per_record"] = 4
    with pytest.raises(Exception):
        parse_scope_spec(payload)
