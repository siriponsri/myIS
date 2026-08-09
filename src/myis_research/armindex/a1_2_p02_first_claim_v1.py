"""Additive pre-measurement P02-FIRST-CLAIM repair and coverage audit.

The original v11 P02 program remains immutable lineage.  This module only
defines deterministic claim-boundary segmentation and aggregate-only coverage
evidence for its Owner-authorized executable successor.  It never classifies
claim dependency or independence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

CONTRACT_PATH = Path("control/armindex/a1.2/p02-first-claim-repair.v1.json")
SOURCE_CONTRACT_PATH = Path("control/assets/dapfam-p1-source.v1.json")
PARSER_VERSION = "p02-first-claim-boundary-parser-v1"
SCHEMA_VERSION = "myis.armindex-a1.2-p02-first-claim-repair-receipt.v1"

# This is a boundary parser only. No dependency-reference expression exists in
# this module, and no absence-of-reference inference is made.
CLAIM_BOUNDARY_RE = re.compile(
    r"(?:^|\n|;\s*)\s*(?P<number>[0-9]{1,4})(?:\s*[.:\-)\]]\s+|\s{2,})",
    re.MULTILINE,
)


class P02FirstClaimError(ValueError):
    """Fail-closed P02 repair error without protected payloads."""


@dataclass(frozen=True)
class ClaimSegment:
    """One ordered boundary segment without dependency semantics."""

    claim_ordinal: int
    text: str
    source_number: int | None
    boundary_mode: str


def _source_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFKC", value).strip()


def segment_claims_text(value: Any) -> tuple[ClaimSegment, ...]:
    """Segment frozen ``claims_text`` without dependency inference or fallback.

    An unmarked nonempty source is explicitly one primary parser segment.  This
    is a declared parser mode, not a fallback to another representation field.
    When numeric boundaries exist, only strictly increasing source markers are
    accepted and empty boundary bodies are skipped in source order.
    """

    text = _source_text(value)
    if not text:
        return ()
    matches = list(CLAIM_BOUNDARY_RE.finditer(text))
    accepted: list[tuple[int, int, int]] = []
    last_number = 0
    for match in matches:
        number = int(match.group("number"))
        if number <= last_number:
            continue
        accepted.append((number, match.start(), match.end()))
        last_number = number
    if not accepted:
        return (ClaimSegment(1, text, None, "single_unmarked_segment"),)

    segments: list[ClaimSegment] = []
    for index, (number, _start, body_start) in enumerate(accepted):
        body_end = accepted[index + 1][1] if index + 1 < len(accepted) else len(text)
        body = text[body_start:body_end].strip(" .;\t\r\n")
        if body:
            segments.append(
                ClaimSegment(
                    claim_ordinal=len(segments) + 1,
                    text=body,
                    source_number=number,
                    boundary_mode="numbered_boundary_segment",
                )
            )
    return tuple(segments)


def first_claim_segment(value: Any) -> ClaimSegment:
    """Return the first successfully parsed segment in source order."""

    segments = segment_claims_text(value)
    if not segments:
        raise P02FirstClaimError("claims_text has no successfully parsed claim segment")
    return segments[0]


def _scan_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_role: str,
    id_field: str,
    selected_ids: set[str] | None = None,
) -> dict[str, Any]:
    row_count = 0
    selected_row_count = 0
    available_count = 0
    failure_count = 0
    segment_count = 0
    observed_ids: set[str] = set()
    modes: Counter[str] = Counter()
    manifest = hashlib.sha256()
    for row_index, row in enumerate(rows):
        row_count += 1
        source_id = row.get(id_field)
        if not isinstance(source_id, str) or not source_id:
            raise P02FirstClaimError(f"{source_role} source identifier is missing")
        if selected_ids is not None and source_id not in selected_ids:
            continue
        if source_id in observed_ids:
            raise P02FirstClaimError(f"{source_role} source identifier is duplicated")
        observed_ids.add(source_id)
        selected_row_count += 1
        segments = segment_claims_text(row.get("claims_text"))
        if not segments:
            failure_count += 1
            manifest.update(f"{source_role}:{row_index}:FAIL\n".encode("ascii"))
            continue
        available_count += 1
        segment_count += len(segments)
        first = segments[0]
        modes[first.boundary_mode] += 1
        first_sha256 = hashlib.sha256(first.text.encode("utf-8")).hexdigest()
        manifest.update(
            (
                f"{source_role}:{row_index}:{len(segments)}:{first.claim_ordinal}:"
                f"{first.source_number or 0}:{first.boundary_mode}:{first_sha256}\n"
            ).encode("ascii")
        )
    if selected_ids is not None and observed_ids != selected_ids:
        raise P02FirstClaimError(f"{source_role} selected membership is incomplete")
    return {
        "source_role": source_role,
        "source_row_count": row_count,
        "required_row_count": len(selected_ids) if selected_ids is not None else row_count,
        "selected_row_count": selected_row_count,
        "available_count": available_count,
        "parse_failure_count": failure_count,
        "segment_count": segment_count,
        "coverage_fraction": available_count / selected_row_count if selected_row_count else 0.0,
        "first_segment_boundary_modes": dict(sorted(modes.items())),
        "output_manifest_sha256": manifest.hexdigest(),
    }


def _read_membership(path: Path) -> set[str]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise P02FirstClaimError("protected REP-DEV membership is missing or invalid") from error
    if (
        not isinstance(value, Mapping)
        or value.get("schema_version")
        != "myis.armindex-a1.2-rep-harness-protected-membership.v1"
        or not isinstance(value.get("rep_dev"), list)
    ):
        raise P02FirstClaimError("protected REP-DEV membership schema is invalid")
    identifiers = {str(item) for item in value["rep_dev"]}
    if len(identifiers) != 150 or len(value["rep_dev"]) != 150:
        raise P02FirstClaimError("protected REP-DEV membership must contain exactly 150 unique queries")
    unsigned = {key: item for key, item in value.items() if key != "protected_membership_sha256"}
    if value.get("protected_membership_sha256") != canonical_sha256(unsigned):
        raise P02FirstClaimError("protected REP-DEV membership self-hash mismatch")
    return identifiers


def _validate_contract(root: Path) -> dict[str, Any]:
    try:
        value = json.loads((root / CONTRACT_PATH).read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise P02FirstClaimError("P02 repair contract is missing or invalid") from error
    if not isinstance(value, dict):
        raise P02FirstClaimError("P02 repair contract must be an object")
    unsigned = {key: item for key, item in value.items() if key != "contract_sha256"}
    if value.get("contract_sha256") != canonical_sha256(unsigned):
        raise P02FirstClaimError("P02 repair contract self-hash mismatch")
    parser = value.get("parser")
    if (
        value.get("status") != "FROZEN_ADDITIVE_PRE_MEASUREMENT_REPAIR"
        or not isinstance(parser, Mapping)
        or parser.get("version") != PARSER_VERSION
        or parser.get("source_uri") != Path(__file__).relative_to(root).as_posix()
        or parser.get("source_sha256") != file_sha256(Path(__file__))
        or value.get("independence_or_dependency_semantics") != "FORBIDDEN"
        or value.get("fallback_policy")
        != {"alternate_fields_allowed": False, "raw_whole_claims_fallback_allowed": False}
    ):
        raise P02FirstClaimError("P02 repair contract drifted")
    return value


def audit(
    repository_root: Path,
    *,
    cache_root: Path,
    protected_membership_path: Path,
) -> dict[str, Any]:
    root = repository_root.resolve()
    contract = _validate_contract(root)
    layout = resolve_cache(cache_root, root)
    rep_dev = _read_membership(protected_membership_path.resolve(strict=True))
    corpus_paths = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
    query_paths = tuple(path for path in layout.files["queries"] if path.suffix == ".arrow")

    def scan() -> dict[str, Any]:
        return {
            "corpus": _scan_rows(
                iter_arrow_rows(corpus_paths, ("relevant_id", "claims_text")),
                source_role="corpus",
                id_field="relevant_id",
            ),
            "rep_dev_queries": _scan_rows(
                iter_arrow_rows(query_paths, ("query_id", "claims_text")),
                source_role="rep_dev_queries",
                id_field="query_id",
                selected_ids=rep_dev,
            ),
        }

    first, replay = scan(), scan()
    if first != replay:
        raise P02FirstClaimError("P02 claim segmentation replay is not deterministic")
    query = first["rep_dev_queries"]
    corpus = first["corpus"]
    if query["available_count"] != 150 or query["parse_failure_count"] != 0:
        raise P02FirstClaimError("P02 REP-DEV availability is below the required 100 percent")
    if corpus["available_count"] != corpus["required_row_count"] or corpus["parse_failure_count"] != 0:
        raise P02FirstClaimError("P02 corpus coverage is incomplete")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": "a1.2-p02-first-claim-repair-20260808-v1",
        "status": "PASS",
        "evidence_class": "pre_measurement_owner_local_input_validation",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe additive P02-FIRST-CLAIM parser and coverage evidence only. It contains no claim text, query identifier, membership, qrels, retrieval outcome, ranking, provider value, execution authorization, or scientific result.",
        "repair_contract": {
            "uri": CONTRACT_PATH.as_posix(),
            "file_sha256": file_sha256(root / CONTRACT_PATH),
            "contract_sha256": contract["contract_sha256"],
        },
        "parser": {
            "source_uri": Path(__file__).relative_to(root).as_posix(),
            "version": PARSER_VERSION,
            "source_sha256": file_sha256(Path(__file__)),
            "boundary_regex_sha256": hashlib.sha256(CLAIM_BOUNDARY_RE.pattern.encode("utf-8")).hexdigest(),
            "dependency_or_independence_classification": False,
        },
        "source": {
            "uri": SOURCE_CONTRACT_PATH.as_posix(),
            "file_sha256": file_sha256(root / SOURCE_CONTRACT_PATH),
            "dataset_revision": layout.contract["dataset"]["revision"],
            "input_hashes": layout.input_hashes,
        },
        "semantics": {
            "source_field": "claims_text",
            "representation": "first_successfully_parsed_claim_segment_in_source_order",
            "single_unmarked_source_mode": "one_declared_primary_parser_segment",
            "independence_or_dependency_status": "not_inferred_not_asserted_not_published",
            "fallback_fields": [],
        },
        "coverage": first,
        "parse_failures": corpus["parse_failure_count"] + query["parse_failure_count"],
        "deterministic_replay": {
            "status": "PASS",
            "exact_aggregate_and_manifest_match": True,
            "replay_sha256": canonical_sha256(first),
        },
        "no_silent_fallback": {
            "status": "PASS",
            "tac_allowed": False,
            "title_or_abstract_allowed": False,
            "alternate_claim_field_allowed": False,
            "dependency_regex_used": False,
        },
        "preserved_lineage": {
            "v11_v12_r3_v13_unchanged": True,
            "original_p02_definition_unchanged": True,
            "rep_harness_split_unchanged": True,
            "measured_runs": 0,
            "provider_contacted": False,
        },
    }
    assert_aggregate_only(body)
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != text:
            raise P02FirstClaimError("existing immutable P02 receipt differs")
        return
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-p02-first-claim-v1")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--protected-membership", type=Path, required=True)
    parser.add_argument("--owner-receipt", type=Path, required=True)
    parser.add_argument("--safe-audit-output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(
        args.repository_root,
        cache_root=args.cache_root,
        protected_membership_path=args.protected_membership,
    )
    owner_receipt = args.owner_receipt.resolve(strict=False)
    repository_root = args.repository_root.resolve()
    if owner_receipt.is_relative_to(repository_root):
        raise P02FirstClaimError("Owner-local P02 receipt must remain outside the repository")
    _atomic_json(owner_receipt, result)
    safe_output = args.safe_audit_output.resolve(strict=False)
    if not safe_output.is_relative_to(repository_root):
        raise P02FirstClaimError("safe P02 audit must be written inside the repository")
    _atomic_json(safe_output, result)
    summary = {
        "status": result["status"],
        "parser_sha256": result["parser"]["source_sha256"],
        "query_coverage": result["coverage"]["rep_dev_queries"]["coverage_fraction"],
        "corpus_coverage": result["coverage"]["corpus"]["coverage_fraction"],
        "parse_failures": result["parse_failures"],
        "receipt_sha256": result["receipt_sha256"],
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
