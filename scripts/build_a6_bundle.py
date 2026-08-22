"""Build or validate the fail-closed A6 preparation bundle.

The bundle is a transport/readiness manifest only.  It cannot admit A6
execution before a valid A5 closeout supplies the frozen winner and corpus
commitments.  No corpus, model payload, query data, or provider payload is
read by this utility.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a6_materialization import (
    A6MaterializationError,
    validate_pending_a6_materialization_template,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.protection import assert_aggregate_only


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path("control/armindex/a6/a6-full-dapfam-execution-contract.v1.json")
TEMPLATE = Path("control/armindex/a6/a6-pending-a5-closeout-template.v1.json")
GOAL = Path("docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md")
SOURCE_CONTRACT = Path("control/assets/dapfam-p1-source.v1.json")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise A6MaterializationError(f"expected JSON object: {path}")
    return value


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _source_hashes() -> dict[str, str]:
    paths = (CONTRACT, TEMPLATE, GOAL, SOURCE_CONTRACT)
    missing = [str(path) for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise A6MaterializationError(f"missing A6 source file(s): {', '.join(missing)}")
    return {_relative(path): file_sha256(ROOT / path) for path in paths}


def build_bundle() -> dict[str, Any]:
    contract = _load_json(ROOT / CONTRACT)
    template = _load_json(ROOT / TEMPLATE)
    validated = validate_pending_a6_materialization_template(template, contract)
    sources = _source_hashes()
    source_contract = _load_json(ROOT / SOURCE_CONTRACT)
    corpus = source_contract.get("configs", {}).get("corpus", {})
    if source_contract.get("dataset", {}).get("revision") != "a59a74ce31384165065af1823a83c6f94ccafd48" or corpus.get("rows") != 45336:
        raise A6MaterializationError("canonical DAPFAM full-corpus inventory drifted")
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a6-preparation-bundle.v1",
        "bundle_id": "A6_PREPARATION_PENDING_A5_CLOSEOUT",
        "status": "PENDING_A5_CLOSEOUT",
        "phase_id": "A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY",
        "task_id": "A6.1",
        "execution_permitted": False,
        "launch_allowed": False,
        "scientific_authority": False,
        "authorized_instance_id": validated["authorized_instance_id"],
        "a6_contract_sha256": validated["a6_contract_sha256"],
        "pending_template_sha256": validated["template_sha256"],
        "source_file_sha256": sources,
        "full_corpus_source_manifest_sha256": sources[_relative(SOURCE_CONTRACT)],
        "full_corpus_row_count": corpus["rows"],
        "full_corpus_inventory": {
            "dataset_revision": source_contract["dataset"]["revision"],
            "rows": corpus["rows"],
            "files": corpus.get("files", []),
        },
        "required_a5_terminal_state": "PASS_A5_FINAL_CONFIRMATION",
        "required_a5_bindings": [
            "a5_closeout_receipt_sha256",
            "a5_result_integrity_audit_sha256",
            "a5_safe_return_receipt_sha256",
            "a5_finalist_registry_sha256",
            "a5_frozen_winner_configuration_sha256",
            "full_corpus_source_sha256",
        ],
        "fresh_a6_attempt_required": True,
        "stale_runtime_reuse_forbidden": True,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "required_aggregate_metrics": validated["required_aggregate_metrics"],
        "safe_return_allowlist": validated["safe_return_allowlist"],
        "claim_boundary": validated["claim_boundary"],
        "validation": {
            "contract_validated": True,
            "pending_template_validated": True,
            "source_hashes_recorded": True,
            "dry_run_only": True,
        },
    }
    assert_aggregate_only(body)
    return {**body, "bundle_sha256": canonical_sha256(body)}


def validate_bundle(path: Path) -> dict[str, Any]:
    bundle = _load_json(path)
    expected_fields = {
        "schema_version", "bundle_id", "status", "phase_id", "task_id",
        "execution_permitted", "launch_allowed", "scientific_authority",
        "authorized_instance_id", "a6_contract_sha256", "pending_template_sha256",
        "source_file_sha256", "full_corpus_source_manifest_sha256", "full_corpus_row_count",
        "full_corpus_inventory", "required_a5_terminal_state", "required_a5_bindings",
        "fresh_a6_attempt_required", "stale_runtime_reuse_forbidden",
        "selection_accesses", "final_accesses", "protected_payload_included",
        "required_aggregate_metrics", "safe_return_allowlist", "claim_boundary",
        "validation", "bundle_sha256",
    }
    if set(bundle) != expected_fields:
        raise A6MaterializationError("A6 bundle fields are invalid")
    if bundle["schema_version"] != "myis.armindex-a6-preparation-bundle.v1":
        raise A6MaterializationError("A6 bundle schema is invalid")
    contract = _load_json(ROOT / CONTRACT)
    template = _load_json(ROOT / TEMPLATE)
    validated = validate_pending_a6_materialization_template(template, contract)
    for field, expected in (("status", "PENDING_A5_CLOSEOUT"), ("execution_permitted", False), ("launch_allowed", False), ("scientific_authority", False), ("selection_accesses", 0), ("final_accesses", 0), ("protected_payload_included", False), ("authorized_instance_id", validated["authorized_instance_id"]), ("fresh_a6_attempt_required", True), ("stale_runtime_reuse_forbidden", True)):
        if bundle[field] != expected:
            raise A6MaterializationError(f"A6 bundle guard failed: {field}")
    if bundle["required_a5_terminal_state"] != "PASS_A5_FINAL_CONFIRMATION":
        raise A6MaterializationError("A6 bundle predecessor gate drifted")
    assert_aggregate_only(bundle)
    digest = bundle.get("bundle_sha256")
    if not isinstance(digest, str) or digest != canonical_sha256({k: v for k, v in bundle.items() if k != "bundle_sha256"}):
        raise A6MaterializationError("A6 bundle self-hash mismatch")
    if bundle["a6_contract_sha256"] != validated["a6_contract_sha256"] or bundle["pending_template_sha256"] != validated["template_sha256"]:
        raise A6MaterializationError("A6 contract/template commitment drifted")
    current = _source_hashes()
    if bundle["source_file_sha256"] != current:
        raise A6MaterializationError("A6 source file hash drifted")
    source_contract = _load_json(ROOT / SOURCE_CONTRACT)
    if bundle["full_corpus_source_manifest_sha256"] != current[_relative(SOURCE_CONTRACT)] or bundle["full_corpus_row_count"] != 45336:
        raise A6MaterializationError("A6 full-corpus source binding drifted")
    if bundle["full_corpus_inventory"] != {"dataset_revision": source_contract["dataset"]["revision"], "rows": source_contract["configs"]["corpus"]["rows"], "files": source_contract["configs"]["corpus"].get("files", [])}:
        raise A6MaterializationError("A6 full-corpus inventory drifted")
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate")
    check.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build_bundle()
        output = (ROOT / args.output).resolve() if not args.output.is_absolute() else args.output
        if output.exists() or output.is_symlink():
            raise SystemExit(f"refusing to overwrite existing file: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    else:
        result = validate_bundle(args.bundle if args.bundle.is_absolute() else ROOT / args.bundle)
    print(json.dumps({"status": "PASS_A6_PREPARATION_BUNDLE_VALIDATED", "bundle_sha256": result["bundle_sha256"], "execution_permitted": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
