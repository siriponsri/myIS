"""Synthetic-only tests for the isolated A1.2 scientific common-program compiler."""

from __future__ import annotations

from copy import deepcopy

import pytest

from myis_research.armindex.scientific_common_programs_v11 import (
    P03_OVERLAP_TOKENS,
    P03_WINDOW_TOKENS,
    P04_RRF_K,
    P04_VIEW_DEPTH,
    ScientificCommonProgramError,
    compile_all_common_programs,
    compile_common_program,
    compiler_manifest,
    fuse_p04_view_rankings,
    program_set_manifest,
)

FAMILY_A = "F-" + "a" * 32
FAMILY_B = "F-" + "b" * 32
PUBLICATION_A1 = "P-" + "a" * 31 + "1"
PUBLICATION_B1 = "P-" + "b" * 31 + "1"
PUBLICATION_B2 = "P-" + "b" * 31 + "2"


def _rows() -> list[dict[str, object]]:
    return [
        {
            "family_token": FAMILY_B,
            "publication_token": PUBLICATION_B2,
            "publication_ordinal": 2,
            "title_en": "Later title",
            "abstract_en": "Later abstract",
            "claims_text": "2. A dependent claim.",
            "claims": [{"claim_ordinal": 2, "is_independent": False, "text": "A dependent claim."}],
        },
        {
            "family_token": FAMILY_A,
            "publication_token": PUBLICATION_A1,
            "publication_ordinal": 1,
            "title_en": "Alpha title",
            "abstract_en": "Alpha abstract",
            "claims_text": "1. Alpha claim.",
            "claims": [{"claim_ordinal": 1, "is_independent": True, "text": "Alpha independent claim."}],
        },
        {
            "family_token": FAMILY_B,
            "publication_token": PUBLICATION_B1,
            "publication_ordinal": 1,
            "title_en": "Earlier title",
            "abstract_en": None,
            "claims_text": "1. B first claim.",
            "claims": [{"claim_ordinal": 1, "is_independent": True, "text": "B independent claim."}],
        },
    ]


def test_program_manifest_and_compiler_manifest_are_self_hashed_and_complete() -> None:
    programs = program_set_manifest()
    compiler = compiler_manifest()

    assert [program["program_key"] for program in programs["programs"]] == [
        "P00-TAC-DOC", "P01-TA-DOC", "P02-CLAIM1", "P03-PASSAGE", "P04-SECTION-MULTIVIEW",
    ]
    assert len(programs["program_set_sha256"]) == 64
    assert compiler["program_set_sha256"] == programs["program_set_sha256"]
    assert len(compiler["source_file_sha256"]) == 64
    assert len(compiler["compiler_manifest_sha256"]) == 64


def test_all_programs_are_input_order_deterministic_and_preserve_coverage() -> None:
    forward = compile_all_common_programs(_rows())
    reverse = compile_all_common_programs(reversed(_rows()))

    assert {key: value.compiled_sha256 for key, value in forward.items()} == {
        key: value.compiled_sha256 for key, value in reverse.items()
    }
    assert forward["P00-TAC-DOC"].covered_family_count == 2
    assert forward["P01-TA-DOC"].covered_family_count == 2
    assert forward["P03-PASSAGE"].covered_family_count == 2
    assert forward["P04-SECTION-MULTIVIEW"].covered_family_count == 2
    assert len(forward["P04-SECTION-MULTIVIEW"].units) == 6
    assert forward["P02-CLAIM1"].families_without_independent_claim == 0


def test_p00_and_p01_are_one_ordered_document_per_family_with_explicit_missing_field() -> None:
    p00 = compile_common_program("P00-TAC-DOC", _rows())
    p01 = compile_common_program("P01-TA-DOC", _rows())

    family_b_p00 = next(unit for unit in p00.units if unit.family_token == FAMILY_B)
    family_b_p01 = next(unit for unit in p01.units if unit.family_token == FAMILY_B)
    assert family_b_p00.source_publication_tokens == (PUBLICATION_B1, PUBLICATION_B2)
    assert family_b_p00.text.index("Earlier title") < family_b_p00.text.index("Later title")
    assert "ABSTRACT: [MISSING]" in family_b_p00.text
    assert "CLAIMS:" in family_b_p00.text
    assert "CLAIMS:" not in family_b_p01.text


def test_p02_requires_structured_independence_and_never_uses_numbering_regex() -> None:
    rows = _rows()
    rows[0]["claims"] = []
    rows[2]["claims"] = [{"claim_ordinal": 1, "is_independent": False, "text": "1. Numbered but dependent."}]

    result = compile_common_program("P02-CLAIM1", rows)
    assert result.covered_family_count == 1
    assert result.families_without_independent_claim == 1
    assert result.units[0].family_token == FAMILY_A

    invalid = deepcopy(_rows())
    invalid[0]["claims"] = [{"claim_ordinal": 2, "text": "Unmarked claim."}]
    with pytest.raises(ScientificCommonProgramError, match="structured independent-claim"):
        compile_common_program("P02-CLAIM1", invalid)


def test_original_or_malformed_identifiers_fail_closed() -> None:
    original_family = deepcopy(_rows())
    original_family[0]["family_token"] = "US1234567A1"
    with pytest.raises(ScientificCommonProgramError, match="opaque tokens"):
        compile_common_program("P00-TAC-DOC", original_family)

    original_publication = deepcopy(_rows())
    original_publication[0]["publication_token"] = "publication-123"
    with pytest.raises(ScientificCommonProgramError, match="opaque tokens"):
        compile_common_program("P00-TAC-DOC", original_publication)


def test_p03_uses_fixed_conservative_logical_passages_without_drop_or_truncation() -> None:
    long_text = " ".join(f"token{index}" for index in range(P03_WINDOW_TOKENS + 17))
    rows = _rows()
    rows[1]["claims_text"] = long_text
    result = compile_common_program("P03-PASSAGE", rows)
    alpha = [unit for unit in result.units if unit.family_token == FAMILY_A]

    assert len(alpha) == 2
    assert len(alpha[0].text.split()) == P03_WINDOW_TOKENS
    assert alpha[0].text.split()[-P03_OVERLAP_TOKENS:] == alpha[1].text.split()[:P03_OVERLAP_TOKENS]
    assert "token400" in alpha[-1].text
    assert result.omitted_unit_count == 0
    assert result.truncation_count == 0


def test_p04_rrf_uses_k60_depth100_and_lexical_ties() -> None:
    equal = {
        "title": [{"family_token": FAMILY_B, "rank": 1}, {"family_token": FAMILY_A, "rank": 2}],
        "abstract": [{"family_token": FAMILY_A, "rank": 1}, {"family_token": FAMILY_B, "rank": 2}],
        "claims": [],
    }
    fused = fuse_p04_view_rankings(equal)

    assert P04_RRF_K == 60
    assert fused[0][0] == FAMILY_A
    assert fused[0][1] == fused[1][1]
    too_deep = {"title": [{"family_token": FAMILY_A, "rank": P04_VIEW_DEPTH + 1}], "abstract": [], "claims": []}
    with pytest.raises(ScientificCommonProgramError, match="frozen depth"):
        fuse_p04_view_rankings(too_deep)
