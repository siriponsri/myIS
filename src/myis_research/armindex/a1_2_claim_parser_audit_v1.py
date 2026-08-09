"""Bounded aggregate-only audit of the App structured-claim parser candidate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

CLAIM_PARSER_RELATIVE = "00_App/shared/code/is1/thaiphalex_is1/parsing/claim_parser.py"
CLAIM_STRUCTURE_RELATIVE = "00_App/shared/code/is1/thaiphalex_is1/parsing/claim_structure.py"
PREP_RELATIVE = "00_App/shared/code/scripts/is1_dapfam_prepare.py"
AUDIT_SCHEMA_VERSION = "myis.armindex-a1.2-claim-parser-audit.v1"


class ClaimParserAuditError(ValueError):
    """Fail-closed parser audit error without protected payloads."""


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ClaimParserAuditError("candidate parser cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        raise ClaimParserAuditError("candidate parser import failed") from error
    return module


def _app_commit(app_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=app_root,
        capture_output=True,
        text=True,
        encoding="ascii",
        check=False,
    )
    if completed.returncode != 0:
        raise ClaimParserAuditError("App repository identity is unavailable")
    return completed.stdout.strip()


def _literal_constant(source: str, name: str) -> str | None:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == name and isinstance(node.value, ast.Constant):
            return str(node.value.value)
    return None


def _scan(
    paths: tuple[Path, ...],
    *,
    split_claims: Callable[[Any], list[str]],
    detect_dependency: Callable[..., Any],
    source_role: str,
) -> dict[str, Any]:
    rows = 0
    rows_with_text = 0
    rows_missing_text = 0
    claims = 0
    text_missing = 0
    parse_failures = 0
    inferred_independent = 0
    inferred_dependent = 0
    manifest = hashlib.sha256()
    for row_index, row in enumerate(iter_arrow_rows(paths, ("claims_text",))):
        rows += 1
        raw = row.get("claims_text")
        try:
            claim_values = split_claims(raw)
        except Exception:  # noqa: BLE001 - candidate parser failures are counted audit evidence.
            parse_failures += 1
            continue
        if claim_values:
            rows_with_text += 1
        else:
            rows_missing_text += 1
        for claim_ordinal, claim_text in enumerate(claim_values, start=1):
            claims += 1
            if not isinstance(claim_text, str) or not claim_text.strip():
                text_missing += 1
                continue
            try:
                dependency = detect_dependency(claim_text_th=None, claim_text_en=claim_text)
                is_independent = bool(dependency.is_independent)
            except Exception:  # noqa: BLE001 - candidate parser failures are counted audit evidence.
                parse_failures += 1
                continue
            if is_independent:
                inferred_independent += 1
            else:
                inferred_dependent += 1
            claim_digest = hashlib.sha256(claim_text.encode("utf-8")).hexdigest()
            manifest.update(
                f"{source_role}:{row_index}:{claim_ordinal}:{claim_digest}:{int(is_independent)}\n".encode("ascii")
            )
    return {
        "source_role": source_role,
        "row_count": rows,
        "rows_with_nonempty_claim_source": rows_with_text,
        "rows_with_missing_claim_source": rows_missing_text,
        "candidate_record_count": claims,
        "claim_ordinal_missing_count": 0,
        "text_missing_count": text_missing,
        "is_independent_missing_count": 0,
        "parse_failure_count": parse_failures,
        "inferred_independent_count": inferred_independent,
        "inferred_dependent_count": inferred_dependent,
        "independence_ground_truth_count": 0,
        "independence_validation_ambiguous_count": claims,
        "output_manifest_sha256": manifest.hexdigest(),
    }


def audit(
    repository_root: Path,
    *,
    app_root: Path,
    cache_root: Path,
    focused_unit_test_status: str = "NOT_RUN",
    focused_unit_test_count: int = 0,
    focused_unit_test_source_sha256: str | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    app = app_root.resolve(strict=True)
    parser_path = app / "shared/code/is1/thaiphalex_is1/parsing/claim_parser.py"
    structure_path = app / "shared/code/is1/thaiphalex_is1/parsing/claim_structure.py"
    prep_path = app / "shared/code/scripts/is1_dapfam_prepare.py"
    for path in (parser_path, structure_path, prep_path):
        if not path.is_file() or path.is_symlink():
            raise ClaimParserAuditError("candidate source is missing or unsafe")
    cache = resolve_cache(cache_root, root)
    parser = _load_module(parser_path, "myis_a12_claim_parser_candidate")
    prep = _load_module(prep_path, "myis_a12_dapfam_prepare_candidate")
    structure_source = structure_path.read_text(encoding="utf-8")
    corpus_paths = tuple(path for path in cache.files["corpus"] if path.suffix == ".arrow")
    query_paths = tuple(path for path in cache.files["queries"] if path.suffix == ".arrow")
    first = {
        "corpus": _scan(corpus_paths, split_claims=prep.split_claims, detect_dependency=parser.detect_dependency, source_role="corpus"),
        "queries": _scan(query_paths, split_claims=prep.split_claims, detect_dependency=parser.detect_dependency, source_role="queries"),
    }
    replay = {
        "corpus": _scan(corpus_paths, split_claims=prep.split_claims, detect_dependency=parser.detect_dependency, source_role="corpus"),
        "queries": _scan(query_paths, split_claims=prep.split_claims, detect_dependency=parser.detect_dependency, source_role="queries"),
    }
    if first != replay:
        raise ClaimParserAuditError("candidate parser replay was not deterministic")
    audit_value: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_id": "a1.2-structured-claim-parser-audit-20260808-v1",
        "status": "PASS_WITH_P02_BLOCKER",
        "evidence_class": "pre_measurement_parser_audit",
        "scientific_authority": False,
        "claim_boundary": "Engineering audit only. It supports no measured retrieval, legal, ranking, or publication claim.",
        "active_dapfam": {
            "dataset_id": cache.contract["dataset"]["dataset_id"],
            "revision": cache.contract["dataset"]["revision"],
            "source_contract_uri": "control/assets/dapfam-p1-source.v1.json",
            "source_contract_sha256": file_sha256(root / "control/assets/dapfam-p1-source.v1.json"),
            "corpus_arrow_sha256": [cache.input_hashes[key] for key in sorted(cache.input_hashes) if key.startswith("corpus_")],
            "queries_arrow_sha256": [cache.input_hashes[key] for key in sorted(cache.input_hashes) if key.startswith("queries_")],
        },
        "parser_candidate": {
            "source_uri": CLAIM_PARSER_RELATIVE,
            "source_sha256": file_sha256(parser_path),
            "source_version": "unversioned_claim_parser_module_at_app_commit",
            "app_git_commit": _app_commit(app),
            "dependency_semantics": "is_independent=true when no parent-claim reference regex matches; parent numbers are expanded from English/Thai regex captures.",
            "independence_source": "INFERRED_FROM_REGEX_ABSENCE",
            "regex_or_heuristics_involved": True,
            "pattern_families": {"english": 2, "thai": 2, "range_expansion": True},
            "deterministic_replay": True,
            "synthetic_unit_tests": {
                "status": focused_unit_test_status,
                "passed_count": focused_unit_test_count if focused_unit_test_status == "PASS" else 0,
                "ground_truth": False,
                "source_sha256": focused_unit_test_source_sha256,
            },
        },
        "structured_parser_candidate": {
            "source_uri": CLAIM_STRUCTURE_RELATIVE,
            "source_sha256": file_sha256(structure_path),
            "schema_version": _literal_constant(structure_source, "SCHEMA_VERSION"),
            "parser_version": _literal_constant(structure_source, "PARSER_VERSION"),
            "dependency_is_independent_source": "INFERRED_VIA_CLAIM_PARSER",
            "top_level_output_fields": ["claim_number", "raw_text", "dependency.is_independent"],
            "active_dapfam_alignment": "raw claims_text only; no canonical structured independent-claim source field",
        },
        "preprocessing_candidate": {
            "source_uri": PREP_RELATIVE,
            "source_sha256": file_sha256(prep_path),
            "claim_ordinal_semantics": "derived_by_sequential_enumeration_after_candidate_regex_split",
            "dependency_semantics": "_dependency_label regex heuristic; not source-derived",
        },
        "claim_coverage": first,
        "required_structured_semantics_coverage": {
            "claim_ordinal": {"exact_top_level_source_records": 0, "status": "ABSENT"},
            "is_independent": {"exact_source_derived_records": 0, "status": "ABSENT"},
            "text": {"exact_top_level_source_records": 0, "status": "ABSENT"},
            "candidate_records_with_inferred_dependency": sum(item["candidate_record_count"] for item in first.values()),
        },
        "validation_evidence": {
            "independent_ground_truth_available": False,
            "independent_validation_status": "ABSENT",
            "synthetic_parser_tests_are_ground_truth": False,
            "real_dapfam_independence_labels": False,
            "existing_chunks_claim_manifest_sha256": "d083eb62229aa31d993ae9eef5548980a89eca06419ba86e60db8db25b1f7493",
            "existing_chunks_claim_label_source": "is1_dapfam_prepare._dependency_label_regex",
        },
        "recommendation": "ADDITIVE_PRE_MEASUREMENT_P02_FIRST_CLAIM_REPAIR",
        "safety": {
            "retrieval_results_inspected": False,
            "measured_retrieval_started": False,
            "provider_contacted": False,
            "paid_api_used": False,
            "frozen_program_changed": False,
            "p02_changed": False,
        },
    }
    assert_aggregate_only(audit_value)
    audit_value["audit_sha256"] = canonical_sha256(audit_value)
    return audit_value


def build_composite_audit(
    repository_root: Path,
    *,
    claim_audit: Mapping[str, Any],
    split_receipt_path: Path,
    split_receipt_uri: str,
) -> dict[str, Any]:
    """Join safe split commitments and parser findings without opening membership."""

    root = repository_root.resolve()
    try:
        split_receipt = json.loads(split_receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ClaimParserAuditError("Owner-local split receipt is missing or invalid") from error
    if not isinstance(split_receipt, Mapping):
        raise ClaimParserAuditError("Owner-local split receipt must be an object")
    assert_aggregate_only(split_receipt)
    if split_receipt.get("receipt_sha256") != canonical_sha256(
        {key: value for key, value in split_receipt.items() if key != "receipt_sha256"}
    ):
        raise ClaimParserAuditError("Owner-local split receipt self-hash mismatch")
    composite: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-rep-harness-claim-audit.v1",
        "audit_id": "a1.2-rep-harness-and-claim-parser-audit-20260808-v1",
        "status": "SPLIT_PASS_P02_BLOCKED",
        "evidence_class": "pre_measurement_owner_local_input_audit",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe local preparation only; no retrieval outcome, scientific result, publication claim, provider identity, or execution authorization.",
        "split": {
            "status": split_receipt["status"],
            "decision_id": split_receipt["decision_id"],
            "decision_sha256": split_receipt["decision_sha256"],
            "algorithm_id": split_receipt["algorithm_id"],
            "algorithm_source_sha256": split_receipt["algorithm_source_sha256"],
            "seed": split_receipt["seed"],
            "parent_split_sha256": split_receipt["parent_split_sha256"],
            "parent_split_file_sha256": split_receipt["parent_split_file_sha256"],
            "counts": split_receipt["counts"],
            "strata": split_receipt["strata"],
            "parent_train_membership_sha256": split_receipt["parent_train_membership_sha256"],
            "rep_dev_membership_sha256": split_receipt["rep_dev_membership_sha256"],
            "harness_dev_membership_sha256": split_receipt["harness_dev_membership_sha256"],
            "grouping_policy": split_receipt["grouping_policy"],
            "deterministic_replay": split_receipt["deterministic_replay"],
            "owner_local_receipt_uri": split_receipt_uri,
            "owner_local_receipt_file_sha256": file_sha256(split_receipt_path),
            "owner_local_receipt_sha256": split_receipt["receipt_sha256"],
        },
        "claim_parser_audit": {
            "audit_uri": "outputs/audits/rigor/a1.2-claim-parser-audit-20260808.json",
            "audit_sha256": claim_audit["audit_sha256"],
            "status": claim_audit["status"],
            "recommendation": claim_audit["recommendation"],
            "parser_source_sha256": claim_audit["parser_candidate"]["source_sha256"],
            "independence_source": claim_audit["parser_candidate"]["independence_source"],
            "ground_truth_available": claim_audit["validation_evidence"]["independent_ground_truth_available"],
            "required_structured_semantics_coverage": claim_audit["required_structured_semantics_coverage"],
        },
        "publication_v13": {
            "contract_uri": "control/armindex/a1.2/publication-impact-contract.v13.json",
            "contract_sha256": file_sha256(root / "control/armindex/a1.2/publication-impact-contract.v13.json"),
            "disposition_uri": "control/armindex/a1.2/instance-disposition-policy.v13.json",
            "disposition_sha256": file_sha256(root / "control/armindex/a1.2/instance-disposition-policy.v13.json"),
            "unchanged_in_this_change": True,
        },
        "blockers": [
            "P02 structured independent-claim source is absent from active DAPFAM input",
            "candidate parser independence is regex-inferred and lacks independent ground truth",
            "protected compiler preflight must remain blocked until additive P02-FIRST-CLAIM repair is Owner-approved",
        ],
        "safety": {
            "retrieval_results_inspected": False,
            "measured_retrieval_started": False,
            "provider_contacted": False,
            "paid_api_used": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_runs": 0,
        },
    }
    assert_aggregate_only(composite)
    composite["audit_sha256"] = canonical_sha256(composite)
    return composite


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-claim-parser-audit-v1")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--focused-unit-test-status", default="NOT_RUN")
    parser.add_argument("--focused-unit-test-count", type=int, default=0)
    parser.add_argument("--focused-unit-test-source-sha256")
    parser.add_argument("--split-receipt")
    parser.add_argument("--split-receipt-uri", default="owner-local/a1.2-v12-r3/protected/splits/A1_2_REP_HARNESS_SPLIT_RECEIPT_V1.json")
    parser.add_argument("--composite-output")
    args = parser.parse_args()
    result = audit(
        args.repository_root,
        app_root=args.app_root,
        cache_root=args.cache_root,
        focused_unit_test_status=args.focused_unit_test_status,
        focused_unit_test_count=args.focused_unit_test_count,
        focused_unit_test_source_sha256=args.focused_unit_test_source_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
    if args.split_receipt and args.composite_output:
        composite = build_composite_audit(
            args.repository_root,
            claim_audit=result,
            split_receipt_path=Path(args.split_receipt),
            split_receipt_uri=args.split_receipt_uri,
        )
        Path(args.composite_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.composite_output).write_text(json.dumps(composite, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
    elif args.split_receipt or args.composite_output:
        parser.error("--split-receipt and --composite-output must be provided together")
    print(json.dumps({"status": result["status"], "audit_sha256": result["audit_sha256"], "recommendation": result["recommendation"]}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
