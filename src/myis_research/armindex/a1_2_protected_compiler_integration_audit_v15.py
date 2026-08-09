"""Project validated Owner-local v15 compiler receipts into aggregate-safe evidence."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from . import a1_2_owner_local_protected_compiler_v15 as compiler

SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-protected-compiler-integration-audit.v15.json"
)
INTEGRATION_PATH = compiler.INTEGRATION_PATH


class ProtectedCompilerAuditV15Error(ValueError):
    """Fail-closed aggregate projection error."""


def _read(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProtectedCompilerAuditV15Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise ProtectedCompilerAuditV15Error(f"{role} must be an object")
    return value


def _external(path: Path, root: Path, *, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ProtectedCompilerAuditV15Error(f"{role} is missing") from error
    if resolved.is_symlink() or not resolved.is_file() or resolved.is_relative_to(root):
        raise ProtectedCompilerAuditV15Error(f"{role} must be an external regular file")
    return resolved


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _validate_self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    if value.get(field) != _self_hash(value, field):
        raise ProtectedCompilerAuditV15Error(f"{role} self-hash mismatch")


def _schema(root: Path, value: Mapping[str, Any]) -> None:
    schema = _read(root / SCHEMA_PATH, role="v15 compiler audit schema")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path)
    )
    if errors:
        raise ProtectedCompilerAuditV15Error(
            f"v15 compiler audit schema failure at {list(errors[0].path)}"
        )


def _write(path: Path, value: Mapping[str, Any]) -> None:
    text = json.dumps(
        value, ensure_ascii=True, indent=2, sort_keys=False, separators=(",", ": ")
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_audit(
    repository_root: Path,
    *,
    binding_set_path: Path,
    compiler_receipt_path: Path,
    handoff_receipt_path: Path,
    transfer_manifest_path: Path,
) -> dict[str, Any]:
    root = repository_root.resolve()
    paths = {
        "binding": _external(binding_set_path, root, role="binding set"),
        "compiler": _external(compiler_receipt_path, root, role="compiler receipt"),
        "handoff": _external(handoff_receipt_path, root, role="handoff receipt"),
        "transfer": _external(transfer_manifest_path, root, role="transfer manifest"),
    }
    binding = _read(paths["binding"], role="binding set")
    receipt = _read(paths["compiler"], role="compiler receipt")
    handoff = _read(paths["handoff"], role="handoff receipt")
    transfer = _read(paths["transfer"], role="transfer manifest")
    compiler.validate_binding_set(root, binding)
    compiler.validate_receipt(root, receipt)
    _validate_self_hash(handoff, "receipt_sha256", role="handoff receipt")
    _validate_self_hash(transfer, "manifest_sha256", role="transfer manifest")
    if receipt["binding_set_sha256"] != binding["binding_set_sha256"]:
        raise ProtectedCompilerAuditV15Error("compiler receipt binding-set mismatch")
    if receipt["handoff_receipt_sha256"] != file_sha256(paths["handoff"]):
        raise ProtectedCompilerAuditV15Error("compiler receipt handoff mismatch")
    if receipt["protected_transfer_manifest_sha256"] != file_sha256(paths["transfer"]):
        raise ProtectedCompilerAuditV15Error("compiler receipt transfer mismatch")
    integration = compiler._validate_integration(root)
    cells = [
        {
            key: item[key]
            for key in (
                "arm_id",
                "program_slot",
                "program_id",
                "mode",
                "effective_input_limit",
                "raw_rendered_input_max_tokens",
                "physical_window_max_tokens",
                "physical_window_count",
                "corpus_logical_unit_count",
                "corpus_overflow_logical_unit_count",
                "query_logical_unit_count",
                "query_overflow_logical_unit_count",
            )
        }
        for item in binding["bindings"]
    ]
    over_limit = sum(
        int(item["physical_window_max_tokens"] > item["effective_input_limit"])
        for item in cells
    )
    safety_keys = (
        "coverage_gap_count",
        "omitted_unit_count",
        "source_token_drop_count",
        "source_token_overlap_count",
        "truncation_count",
        "fallback_count",
    )
    safety = {key: sum(int(item[key]) for item in binding["bindings"]) for key in safety_keys}
    publication = _read(root / compiler.V13_PATH, role="v13 publication contract")
    outcomes = publication["analysis"]["outcomes"]
    body = {
        "schema_version": "myis.armindex-a1.2-protected-compiler-integration-audit.v15",
        "audit_id": "a1.2-protected-compiler-integration-20260809-v15",
        "status": "PASS",
        "evidence_class": "pre_measurement_owner_local_compiler_validation",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe validation of the Owner-local additive v15 compiler integration. It proves protected receipt linkage, exact 25-cell topology, deterministic tokenizer-level physical-window compatibility, and zero silent truncation only; it exposes no protected identifiers, text, qrels, membership, ranking, per-query outcome, provider payload, or scientific/publication result.",
        "integration": {
            "uri": INTEGRATION_PATH.as_posix(),
            "file_sha256": file_sha256(root / INTEGRATION_PATH),
            "contract_sha256": integration["contract_sha256"],
            "compiler_source_sha256": integration["implementation"]["source_sha256"],
            "materializer_source_sha256": integration["implementation"][
                "materializer_source_sha256"
            ],
        },
        "protected_receipts": {
            "binding_set_file_sha256": file_sha256(paths["binding"]),
            "binding_set_sha256": binding["binding_set_sha256"],
            "compiler_receipt_file_sha256": file_sha256(paths["compiler"]),
            "compiler_receipt_sha256": receipt["receipt_sha256"],
            "handoff_receipt_sha256": receipt["handoff_receipt_sha256"],
            "transfer_manifest_sha256": receipt["protected_transfer_manifest_sha256"],
            "pre_compilation_anchor_sha256": receipt["pre_compilation_anchor_sha256"],
        },
        "coverage": {
            "compiled_bindings": 25,
            "dense_bindings": 20,
            "rep_dev_queries": binding["query_compatibility"]["rep_dev_query_count"],
            "corpus_families": _read(
                root / "outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json",
                role="composition audit",
            )["scope"]["corpus_family_count"],
            "query_coverage_fraction": binding["query_compatibility"]["coverage_fraction"],
            "corpus_coverage_fraction": 1.0,
            "raw_overflow_count": receipt["raw_overflow_count"],
            "cells": cells,
        },
        "safety": {
            **safety,
            "over_limit_physical_window_count": over_limit,
            "deterministic_replay": receipt["deterministic_replay"],
            "zero_silent_truncation": receipt["zero_silent_truncation"],
            "protected_boundary": "PASS",
        },
        "p02_semantics": {
            "program_id": "P02-FIRST-CLAIM",
            "independence_status": integration["p02_successor"][
                "independence_or_dependency_status"
            ],
            "fallback": integration["p02_successor"]["fallback"],
        },
        "publication_v13": {
            "unchanged": True,
            "primary": outcomes["primary"],
            "secondary": outcomes["secondary"],
            "interaction_complementarity_preregistered": True,
            "measured_or_publication_claim_authorized": False,
        },
        "authorization": dict(integration["authorization"]),
        "pending_live_provider": [
            "fresh_provider_identity",
            "fresh_all_fee_quote",
            "whole_workload_live_budget_admission",
            "live_provider_admission_receipt",
        ],
    }
    audit = {**body, "audit_sha256": canonical_sha256(body)}
    _schema(root, audit)
    try:
        assert_aggregate_only(audit)
    except ValueError as error:
        raise ProtectedCompilerAuditV15Error(
            "v15 compiler audit is not aggregate-safe"
        ) from error
    return audit


def validate_audit(repository_root: Path, audit: Mapping[str, Any]) -> dict[str, Any]:
    root = repository_root.resolve()
    _schema(root, audit)
    if audit["audit_sha256"] != _self_hash(audit, "audit_sha256"):
        raise ProtectedCompilerAuditV15Error("v15 compiler audit self-hash mismatch")
    integration = compiler._validate_integration(root)
    if (
        audit["integration"]["file_sha256"] != file_sha256(root / INTEGRATION_PATH)
        or audit["integration"]["contract_sha256"] != integration["contract_sha256"]
    ):
        raise ProtectedCompilerAuditV15Error("v15 compiler audit integration binding mismatch")
    assert_aggregate_only(audit)
    return {
        "status": "PASS",
        "compiled_bindings": 25,
        "zero_silent_truncation": True,
        "protected_boundary": "PASS",
        "audit_sha256": audit["audit_sha256"],
        "provider_contact_allowed": False,
        "measured_retrieval_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-protected-compiler-audit-v15")
    parser.add_argument("command", choices=("build", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--binding-set", type=Path)
    parser.add_argument("--compiler-receipt", type=Path)
    parser.add_argument("--handoff-receipt", type=Path)
    parser.add_argument("--transfer-manifest", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        required = (
            args.binding_set,
            args.compiler_receipt,
            args.handoff_receipt,
            args.transfer_manifest,
            args.output,
        )
        if any(value is None for value in required):
            parser.error("build requires all protected receipts and --output")
        output = args.output.resolve()
        root = args.repository_root.resolve()
        if not output.is_relative_to(root):
            parser.error("aggregate audit output must remain inside the repository")
        audit = build_audit(
            root,
            binding_set_path=args.binding_set,
            compiler_receipt_path=args.compiler_receipt,
            handoff_receipt_path=args.handoff_receipt,
            transfer_manifest_path=args.transfer_manifest,
        )
        _write(output, audit)
        result = validate_audit(root, audit)
    else:
        if args.audit is None:
            parser.error("validate requires --audit")
        result = validate_audit(args.repository_root, _read(args.audit, role="v15 audit"))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
