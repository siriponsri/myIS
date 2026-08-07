"""Deterministic scientific common-program compiler for a future A1.2 screen.

This module is deliberately separate from :mod:`myis_research.armindex.compiler`,
which remains a fixture-only compiler.  It accepts only structured publication
records with opaque identifiers and never reads protected stores, models, or a
network resource.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..kernel.canonical import canonical_sha256


COMPILER_API_VERSION = "myis.armindex-scientific-common-program-compiler.v11"
PROGRAM_SET_ID = "a1.2-common-five-programs-v11"
NORMALIZATION_ID = "unicode_nfkc_canonical_whitespace_preserve_case.v1"
MISSING_FIELD_SENTINEL = "[MISSING]"
P03_LOGICAL_TOKENIZER = "unicode_nfkc_whitespace.v1"
P03_WINDOW_TOKENS = 384
P03_OVERLAP_TOKENS = 64
P04_RRF_K = 60
P04_VIEW_DEPTH = 100

_FIELDS = ("title_en", "abstract_en", "claims_text")
_PROGRAM_KEYS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
_TOKEN_RE = re.compile(r"\S+")
_FAMILY_TOKEN_RE = re.compile(r"^F-[a-f0-9]{32}$")
_PUBLICATION_TOKEN_RE = re.compile(r"^P-[a-f0-9]{32}$")


class ScientificCommonProgramError(ValueError):
    """Raised when a common program cannot be compiled exactly."""


@dataclass(frozen=True)
class PublicationRecord:
    """A structured, aggregate-safe publication record for local compilation.

    ``family_token`` and ``publication_token`` must already be opaque tokens.
    ``claims`` holds structured claim elements; raw claim parsing is prohibited.
    """

    family_token: str
    publication_token: str
    publication_ordinal: int
    title_en: str | None
    abstract_en: str | None
    claims_text: str | None
    claims: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class CompiledScientificUnit:
    program_key: str
    unit_id: str
    family_token: str
    view_id: str | None
    source_publication_tokens: tuple[str, ...]
    source_ordinals: tuple[int, ...]
    text: str
    content_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompiledScientificProgram:
    program_key: str
    program_spec_sha256: str
    compiled_sha256: str
    units: tuple[CompiledScientificUnit, ...]
    family_count: int
    covered_family_count: int
    families_without_independent_claim: int
    omitted_unit_count: int
    truncation_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "program_key": self.program_key,
            "program_spec_sha256": self.program_spec_sha256,
            "compiled_sha256": self.compiled_sha256,
            "units": [unit.as_dict() for unit in self.units],
            "family_count": self.family_count,
            "covered_family_count": self.covered_family_count,
            "families_without_independent_claim": self.families_without_independent_claim,
            "omitted_unit_count": self.omitted_unit_count,
            "truncation_count": self.truncation_count,
        }


@dataclass(frozen=True)
class ViewRank:
    family_token: str
    rank: int


def common_program_specs() -> tuple[dict[str, Any], ...]:
    """Return the five logical programs with all scientific semantics explicit."""

    base = {
        "source_field_contract": {
            "fields": list(_FIELDS),
            "normalization_id": NORMALIZATION_ID,
            "missing_field_rendering": MISSING_FIELD_SENTINEL,
            "family_membership": "all_publications_sorted_by_ordinal_then_opaque_publication_token",
            "family_identity": "opaque_family_token_preserved",
            "publication_identity": "opaque_publication_token_preserved",
            "duplicate_policy": "preserve_all_source_members",
        },
        "execution_boundary": {
            "adapter_windowing_may_change_logical_unitization": False,
            "silent_truncation_allowed": False,
            "raw_claim_regex_fallback_allowed": False,
        },
    }
    specifications: list[dict[str, Any]] = [
        {
            **base,
            "program_key": "P00-TAC-DOC",
            "semantic_version": 1,
            "unitization": {"kind": "family_document", "source_fields": list(_FIELDS)},
            "rendering": {
                "publication_separator": "\n\n",
                "field_order": list(_FIELDS),
                "field_labels": {"title_en": "TITLE", "abstract_en": "ABSTRACT", "claims_text": "CLAIMS"},
            },
            "family_aggregation": {"kind": "single_unit"},
            "coverage_rule": "exactly_one_unit_per_input_family",
            "physical_view_multiplier": 1,
        },
        {
            **base,
            "program_key": "P01-TA-DOC",
            "semantic_version": 1,
            "unitization": {"kind": "family_document", "source_fields": ["title_en", "abstract_en"]},
            "rendering": {
                "publication_separator": "\n\n",
                "field_order": ["title_en", "abstract_en"],
                "field_labels": {"title_en": "TITLE", "abstract_en": "ABSTRACT"},
            },
            "family_aggregation": {"kind": "single_unit"},
            "coverage_rule": "exactly_one_unit_per_input_family",
            "physical_view_multiplier": 1,
        },
        {
            **base,
            "program_key": "P02-CLAIM1",
            "semantic_version": 1,
            "unitization": {
                "kind": "structured_independent_claim",
                "selection_scope": "family",
                "selection_order": "publication_ordinal_then_claim_ordinal_then_opaque_publication_token",
                "required_claim_fields": ["claim_ordinal", "is_independent", "text"],
                "fallback": "forbidden",
            },
            "rendering": {"field_label": "CLAIM"},
            "family_aggregation": {"kind": "maxp"},
            "coverage_rule": "one_unit_for_each_family_with_structured_independent_claim",
            "physical_view_multiplier": 1,
        },
        {
            **base,
            "program_key": "P03-PASSAGE",
            "semantic_version": 1,
            "unitization": {
                "kind": "logical_token_passage",
                "logical_tokenizer": P03_LOGICAL_TOKENIZER,
                # 384 leaves a conservative 128-token envelope for the 512-token
                # PatEmbed adapter's document prefix and special-token overhead.
                "window_tokens": P03_WINDOW_TOKENS,
                "overlap_tokens": P03_OVERLAP_TOKENS,
                "stride_tokens": P03_WINDOW_TOKENS - P03_OVERLAP_TOKENS,
                "final_window": "retain_partial_no_drop",
                "source_fields": list(_FIELDS),
                "source_stream": "family_tac_rendering",
            },
            "rendering": {
                "field_order": list(_FIELDS),
                "field_labels": {"title_en": "TITLE", "abstract_en": "ABSTRACT", "claims_text": "CLAIMS"},
                "publication_separator": "\n\n",
            },
            "family_aggregation": {"kind": "maxp"},
            "coverage_rule": "at_least_one_complete_logical_passage_per_input_family",
            "physical_view_multiplier": 1,
        },
        {
            **base,
            "program_key": "P04-SECTION-MULTIVIEW",
            "semantic_version": 1,
            "unitization": {
                "kind": "family_views",
                "views": ["title", "abstract", "claims"],
                "source_fields": {"title": "title_en", "abstract": "abstract_en", "claims": "claims_text"},
            },
            "rendering": {
                "publication_separator": "\n\n",
                "field_labels": {"title": "TITLE", "abstract": "ABSTRACT", "claims": "CLAIMS"},
            },
            "family_aggregation": {
                "kind": "view_rrf",
                "rrf_k": P04_RRF_K,
                "per_view_depth": P04_VIEW_DEPTH,
                "tie_break": "opaque_family_token_lexical",
            },
            "coverage_rule": "exactly_three_view_units_per_input_family",
            "physical_view_multiplier": 3,
        },
    ]
    return tuple(_finalize_spec(specification) for specification in specifications)


def program_set_manifest() -> dict[str, Any]:
    """Return a self-hashed manifest for binding future workload manifests."""

    body = {
        "schema_version": "myis.armindex-a1.2-common-program-set.v11",
        "program_set_id": PROGRAM_SET_ID,
        "compiler_api_version": COMPILER_API_VERSION,
        "programs": list(common_program_specs()),
    }
    return {**body, "program_set_sha256": canonical_sha256(body)}


def compiler_manifest() -> dict[str, Any]:
    """Expose exact source and configuration commitments without external state."""

    source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    body = {
        "schema_version": "myis.armindex-scientific-common-program-compiler-manifest.v11",
        "compiler_api_version": COMPILER_API_VERSION,
        "source_file": "src/myis_research/armindex/scientific_common_programs_v11.py",
        "source_file_sha256": source_sha256,
        "program_set_id": PROGRAM_SET_ID,
        "program_set_sha256": program_set_manifest()["program_set_sha256"],
        "passage_window_tokens": P03_WINDOW_TOKENS,
        "passage_overlap_tokens": P03_OVERLAP_TOKENS,
        "p04_rrf_k": P04_RRF_K,
        "p04_per_view_depth": P04_VIEW_DEPTH,
    }
    return {**body, "compiler_manifest_sha256": canonical_sha256(body)}


def compile_common_program(
    program_key: str,
    publications: Iterable[PublicationRecord | Mapping[str, Any]],
) -> CompiledScientificProgram:
    """Compile one frozen logical common program from structured publications."""

    if program_key not in _PROGRAM_KEYS:
        raise ScientificCommonProgramError(f"unknown common program: {program_key}")
    rows = _validated_rows(publications)
    grouped = _families(rows)
    spec = _spec(program_key)
    units: list[CompiledScientificUnit] = []
    without_claim = 0
    for family_token, members in grouped:
        if program_key == "P00-TAC-DOC":
            units.append(_unit(program_key, family_token, None, members, _family_text(members, _FIELDS)))
        elif program_key == "P01-TA-DOC":
            units.append(_unit(program_key, family_token, None, members, _family_text(members, _FIELDS[:2])))
        elif program_key == "P02-CLAIM1":
            selected = _first_independent_claim(members)
            if selected is None:
                without_claim += 1
            else:
                member, claim = selected
                units.append(_unit(program_key, family_token, None, (member,), f"CLAIM: {_normalized_required(claim['text'])}"))
        elif program_key == "P03-PASSAGE":
            text = _family_text(members, _FIELDS)
            for index, passage in enumerate(_passages(text), start=1):
                units.append(_unit(program_key, family_token, f"passage-{index:04d}", members, passage))
        else:
            for view_id, field_name, label in (
                ("title", "title_en", "TITLE"),
                ("abstract", "abstract_en", "ABSTRACT"),
                ("claims", "claims_text", "CLAIMS"),
            ):
                units.append(_unit(program_key, family_token, view_id, members, _family_text(members, (field_name,), labels={field_name: label})))

    units.sort(key=lambda unit: (unit.family_token, unit.view_id or "", unit.unit_id))
    family_count = len(grouped)
    covered = len({unit.family_token for unit in units})
    if program_key != "P02-CLAIM1" and covered != family_count:
        raise ScientificCommonProgramError("common program lost family coverage")
    if program_key == "P04-SECTION-MULTIVIEW" and len(units) != family_count * 3:
        raise ScientificCommonProgramError("multiview program must emit exactly three family views")
    body = {
        "program_key": program_key,
        "program_spec_sha256": spec["program_spec_sha256"],
        "units": [unit.as_dict() for unit in units],
        "family_count": family_count,
        "covered_family_count": covered,
        "families_without_independent_claim": without_claim,
        "omitted_unit_count": 0,
        "truncation_count": 0,
    }
    return CompiledScientificProgram(
        program_key=program_key,
        program_spec_sha256=spec["program_spec_sha256"],
        compiled_sha256=canonical_sha256(body),
        units=tuple(units),
        family_count=family_count,
        covered_family_count=covered,
        families_without_independent_claim=without_claim,
        omitted_unit_count=0,
        truncation_count=0,
    )


def compile_all_common_programs(
    publications: Iterable[PublicationRecord | Mapping[str, Any]],
) -> dict[str, CompiledScientificProgram]:
    """Compile all P00-P04 from the same validated immutable input sequence."""

    rows = tuple(_validated_rows(publications))
    return {key: compile_common_program(key, rows) for key in _PROGRAM_KEYS}


def fuse_p04_view_rankings(view_rankings: Mapping[str, Sequence[ViewRank | Mapping[str, Any]]]) -> tuple[tuple[str, float], ...]:
    """Fuse P04's three view rankings with RRF(k=60), then lexical ties."""

    expected = {"title", "abstract", "claims"}
    if set(view_rankings) != expected:
        raise ScientificCommonProgramError("P04 requires exactly title, abstract, and claims rankings")
    scores: dict[str, Fraction] = {}
    for view_id in sorted(expected):
        ranks = _validated_ranks(view_rankings[view_id])
        for value in ranks:
            scores[value.family_token] = scores.get(value.family_token, Fraction(0, 1)) + Fraction(1, P04_RRF_K + value.rank)
    return tuple((family, float(score)) for family, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])))


def _validated_rows(publications: Iterable[PublicationRecord | Mapping[str, Any]]) -> list[PublicationRecord]:
    rows: list[PublicationRecord] = []
    seen_publications: set[str] = set()
    for raw in publications:
        if isinstance(raw, PublicationRecord):
            row = raw
        elif isinstance(raw, Mapping):
            allowed = {"family_token", "publication_token", "publication_ordinal", *_FIELDS, "claims"}
            if set(raw) != allowed:
                raise ScientificCommonProgramError("publication record fields do not match the scientific input contract")
            row = PublicationRecord(
                family_token=str(raw["family_token"]),
                publication_token=str(raw["publication_token"]),
                publication_ordinal=raw["publication_ordinal"],
                title_en=raw["title_en"],
                abstract_en=raw["abstract_en"],
                claims_text=raw["claims_text"],
                claims=tuple(raw["claims"]),
            )
        else:
            raise ScientificCommonProgramError("publication record must be a mapping or PublicationRecord")
        if (
            _FAMILY_TOKEN_RE.fullmatch(row.family_token) is None
            or _PUBLICATION_TOKEN_RE.fullmatch(row.publication_token) is None
            or not isinstance(row.publication_ordinal, int)
            or row.publication_ordinal < 0
        ):
            raise ScientificCommonProgramError("opaque tokens and a non-negative publication ordinal are required")
        if row.publication_token in seen_publications:
            raise ScientificCommonProgramError("publication tokens must be globally unique")
        seen_publications.add(row.publication_token)
        if any(value is not None and not isinstance(value, str) for value in (row.title_en, row.abstract_en, row.claims_text)):
            raise ScientificCommonProgramError("source text fields must be strings or null")
        _validate_claims(row.claims)
        rows.append(row)
    if not rows:
        raise ScientificCommonProgramError("at least one publication record is required")
    return sorted(rows, key=lambda row: (row.family_token, row.publication_ordinal, row.publication_token))


def _validate_claims(claims: Sequence[Mapping[str, Any]]) -> None:
    ordinals: set[int] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != {"claim_ordinal", "is_independent", "text"}:
            raise ScientificCommonProgramError("claims must use the structured independent-claim contract")
        ordinal = claim["claim_ordinal"]
        if not isinstance(ordinal, int) or ordinal < 1 or ordinal in ordinals:
            raise ScientificCommonProgramError("claim ordinals must be unique positive integers")
        if not isinstance(claim["is_independent"], bool) or not isinstance(claim["text"], str) or not claim["text"].strip():
            raise ScientificCommonProgramError("structured claims require boolean independence and nonempty text")
        ordinals.add(ordinal)


def _families(rows: Sequence[PublicationRecord]) -> tuple[tuple[str, tuple[PublicationRecord, ...]], ...]:
    grouped: dict[str, list[PublicationRecord]] = {}
    for row in rows:
        grouped.setdefault(row.family_token, []).append(row)
    return tuple((family, tuple(members)) for family, members in sorted(grouped.items()))


def _spec(program_key: str) -> dict[str, Any]:
    return next(spec for spec in common_program_specs() if spec["program_key"] == program_key)


def _finalize_spec(specification: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(specification)
    return {**body, "program_spec_sha256": canonical_sha256(body)}


def _normalized_optional(value: str | None) -> str:
    if value is None or not value.strip():
        return MISSING_FIELD_SENTINEL
    return _normalized_required(value)


def _normalized_required(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _family_text(
    members: Sequence[PublicationRecord],
    fields: Sequence[str],
    *,
    labels: Mapping[str, str] | None = None,
) -> str:
    field_labels = labels or {"title_en": "TITLE", "abstract_en": "ABSTRACT", "claims_text": "CLAIMS"}
    publication_texts = []
    for member in members:
        pieces = []
        for field_name in fields:
            pieces.append(f"{field_labels[field_name]}: {_normalized_optional(getattr(member, field_name))}")
        publication_texts.append("\n".join(pieces))
    return "\n\n".join(publication_texts)


def _first_independent_claim(members: Sequence[PublicationRecord]) -> tuple[PublicationRecord, Mapping[str, Any]] | None:
    candidates: list[tuple[int, int, str, PublicationRecord, Mapping[str, Any]]] = []
    for member in members:
        for claim in member.claims:
            if claim["is_independent"]:
                candidates.append((member.publication_ordinal, int(claim["claim_ordinal"]), member.publication_token, member, claim))
    if not candidates:
        return None
    _publication_ordinal, _claim_ordinal, _publication_token, member, claim = min(candidates)
    return member, claim


def _passages(text: str) -> tuple[str, ...]:
    tokens = _TOKEN_RE.findall(text)
    if not tokens:
        raise ScientificCommonProgramError("P03 requires a nonempty rendered family stream")
    passages = []
    for start in range(0, len(tokens), P03_WINDOW_TOKENS - P03_OVERLAP_TOKENS):
        window = tokens[start : start + P03_WINDOW_TOKENS]
        if not window:
            break
        passages.append(" ".join(window))
        if start + P03_WINDOW_TOKENS >= len(tokens):
            break
    return tuple(passages)


def _unit(
    program_key: str,
    family_token: str,
    view_id: str | None,
    members: Sequence[PublicationRecord],
    text: str,
) -> CompiledScientificUnit:
    if not text:
        raise ScientificCommonProgramError("compiled scientific unit cannot be empty")
    source_publications = tuple(member.publication_token for member in members)
    source_ordinals = tuple(member.publication_ordinal for member in members)
    semantic = {
        "program_key": program_key,
        "family_token": family_token,
        "view_id": view_id,
        "source_publication_tokens": source_publications,
        "source_ordinals": source_ordinals,
        "content_sha256": canonical_sha256(text),
    }
    return CompiledScientificUnit(
        program_key=program_key,
        unit_id="unit-" + canonical_sha256(semantic)[:24],
        family_token=family_token,
        view_id=view_id,
        source_publication_tokens=source_publications,
        source_ordinals=source_ordinals,
        text=text,
        content_sha256=canonical_sha256(text),
    )


def _validated_ranks(values: Sequence[ViewRank | Mapping[str, Any]]) -> tuple[ViewRank, ...]:
    parsed: list[ViewRank] = []
    seen_families: set[str] = set()
    seen_ranks: set[int] = set()
    if len(values) > P04_VIEW_DEPTH:
        raise ScientificCommonProgramError("P04 per-view ranking exceeds the frozen depth")
    for raw in values:
        value = raw if isinstance(raw, ViewRank) else ViewRank(**raw)
        if (
            _FAMILY_TOKEN_RE.fullmatch(value.family_token) is None
            or not isinstance(value.rank, int)
            or not 1 <= value.rank <= P04_VIEW_DEPTH
        ):
            raise ScientificCommonProgramError("P04 ranks must be within the frozen depth")
        if value.family_token in seen_families or value.rank in seen_ranks:
            raise ScientificCommonProgramError("P04 view rankings require unique families and ranks")
        seen_families.add(value.family_token)
        seen_ranks.add(value.rank)
        parsed.append(value)
    return tuple(parsed)
