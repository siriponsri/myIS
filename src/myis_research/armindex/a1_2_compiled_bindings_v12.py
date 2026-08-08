"""Validate Owner-local A1.2 v12 compiled program-arm binding receipts.

This module never reads corpus text, qrels, membership, model bytes, or provider
configuration. It accepts only aggregate-safe hashes and counts produced inside
the Owner-local protected root.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


CONTRACT_PATH = Path("control/owner-local/a1.2-compiled-program-bindings-contract.v12.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-compiled-program-binding-set.v12.json")
REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
PROGRAM_SET_PATH = Path("control/armindex/a1.2/common-program-set.v11.json")
MODEL_LOCK_ROOT = Path("control/armindex/a1.2/model-locks")
ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
_SECRET_OR_PATH = re.compile(
    r"(?:bearer\s+|api[_-]?key|private[_-]?key|password|token\s*=|[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _self_hash(value: Mapping[str, Any]) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != "binding_set_sha256"})


def _safe(value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if _SECRET_OR_PATH.search(text):
        raise ValueError("protected, credential-like, or absolute-path material is forbidden")


def _validate_schema(root: Path, value: Mapping[str, Any]) -> None:
    schema = _read_json(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        raise ValueError(f"schema failure at {list(error.path)}: {error.message}")


def _contract(root: Path) -> dict[str, Any]:
    contract = _read_json(root / CONTRACT_PATH)
    required = {
        "schema_version",
        "contract_id",
        "status",
        "claim_boundary",
        "v11_request",
        "program_set",
        "model_locks",
        "required_binding_fields",
        "required_owner_local_receipt_hashes",
        "forbidden_payload_classes",
        "zero_required",
        "launch_allowed",
        "adopted_for_execution",
        "measured_runs",
        "charged_usd",
    }
    if set(contract) != required:
        raise ValueError("v12 contract fields differ from the frozen contract")
    if contract["status"] != "template_only_owner_local_protected_compilation_required":
        raise ValueError("v12 contract must remain template-only")
    if any(contract[key] is not False for key in ("launch_allowed", "adopted_for_execution")):
        raise ValueError("v12 contract cannot authorize launch or adoption")
    if any(contract[key] != 0 for key in ("measured_runs", "charged_usd")):
        raise ValueError("v12 contract counters must remain zero")
    request = _read_json(root / REQUEST_PATH)
    program_set = _read_json(root / PROGRAM_SET_PATH)
    if file_sha256(root / REQUEST_PATH) != contract["v11_request"]["file_sha256"]:
        raise ValueError("v11 request file hash mismatch")
    if request.get("request_sha256") != contract["v11_request"]["request_sha256"]:
        raise ValueError("v11 request self-hash mismatch")
    if file_sha256(root / PROGRAM_SET_PATH) != contract["program_set"]["file_sha256"]:
        raise ValueError("v11 program-set file hash mismatch")
    if program_set.get("program_set_sha256") != contract["program_set"]["program_set_sha256"]:
        raise ValueError("v11 program-set self-hash mismatch")
    if program_set["compiler_contract"]["source_manifest_sha256"] != contract["program_set"]["compiler_source_manifest_sha256"]:
        raise ValueError("v11 compiler source-manifest hash mismatch")
    if [item["arm_id"] for item in contract["model_locks"]] != list(ARM_IDS):
        raise ValueError("v12 model-lock order differs from the frozen arm order")
    for item in contract["model_locks"]:
        path = root / item["uri"]
        if file_sha256(path) != item["file_sha256"]:
            raise ValueError(f"{item['arm_id']} model-lock file hash mismatch")
        lock = _read_json(path)
        if item["arm_id"] == "ARM-01":
            adapter = lock["adapter"]
            tokenizer_sha256 = canonical_sha256(adapter["tokenizer"])
            expected_limit = None
        else:
            adapter = {
                key: lock[key]
                for key in (
                    "query_format",
                    "document_format",
                    "pooling",
                    "normalization",
                    "dimension",
                )
                if key in lock
            }
            tokenizer_sha256 = item["tokenizer_sha256"]
            expected_limit = lock.get(
                "declared_max_input_tokens", lock.get("max_input_tokens")
            )
        if canonical_sha256(adapter) != item["adapter_contract_sha256"]:
            raise ValueError(f"{item['arm_id']} adapter-contract hash mismatch")
        if tokenizer_sha256 != item["tokenizer_sha256"]:
            raise ValueError(f"{item['arm_id']} tokenizer hash mismatch")
        if item["effective_input_limit"] != expected_limit:
            raise ValueError(f"{item['arm_id']} effective-input limit mismatch")
    return contract


def _expected_bindings(program_set: Mapping[str, Any]) -> list[dict[str, str]]:
    hashes = {item["program_key"]: item["program_spec_sha256"] for item in program_set["programs"]}
    return [
        {
            "binding_id": f"{arm_id}--{program_id}",
            "arm_id": arm_id,
            "program_id": program_id,
            "logical_program_sha256": hashes[program_id],
        }
        for arm_id in ARM_IDS
        for program_id in PROGRAM_IDS
    ]


def pending_template(root: Path) -> dict[str, Any]:
    """Return a deterministic, non-evidentiary template with no protected data."""

    contract = _contract(root)
    program_set = _read_json(root / PROGRAM_SET_PATH)
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-compiled-program-binding-set.v12",
        "binding_set_id": "a1.2-v12-pending-owner-local-compiled-bindings",
        "status": "pending_owner_local_protected_compilation",
        "claim_boundary": "Deterministic Owner-local template only. It contains no corpus, query, qrels, membership, model bytes, compiled representation, index, measured retrieval result, provider identity, or execution authorization.",
        "contract_file_sha256": file_sha256(root / CONTRACT_PATH),
        "frozen_bindings": {
            "v11_request_file_sha256": contract["v11_request"]["file_sha256"],
            "v11_request_sha256": contract["v11_request"]["request_sha256"],
            "program_set_file_sha256": contract["program_set"]["file_sha256"],
            "program_set_sha256": contract["program_set"]["program_set_sha256"],
            "compiler_source_manifest_sha256": contract["program_set"]["compiler_source_manifest_sha256"],
        },
        "owner_local_receipts": {key: None for key in contract["required_owner_local_receipt_hashes"]},
        "expected_bindings": _expected_bindings(program_set),
        "bindings": [],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }
    body["binding_set_sha256"] = _self_hash(body)
    return body


def _validate_frozen_bindings(value: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    expected = {
        "v11_request_file_sha256": contract["v11_request"]["file_sha256"],
        "v11_request_sha256": contract["v11_request"]["request_sha256"],
        "program_set_file_sha256": contract["program_set"]["file_sha256"],
        "program_set_sha256": contract["program_set"]["program_set_sha256"],
        "compiler_source_manifest_sha256": contract["program_set"]["compiler_source_manifest_sha256"],
    }
    if value["frozen_bindings"] != expected:
        raise ValueError("binding set does not bind the frozen v11 request/program/compiler identity")


def _validate_expected_matrix(value: Mapping[str, Any], program_set: Mapping[str, Any]) -> set[str]:
    expected = _expected_bindings(program_set)
    if value["expected_bindings"] != expected:
        raise ValueError("expected binding matrix is not the exact ordered 25 program-arm set")
    return {item["binding_id"] for item in expected}


def _validate_actual_bindings(
    value: Mapping[str, Any],
    contract: Mapping[str, Any],
    expected_ids: set[str],
) -> None:
    bindings = value["bindings"]
    if len(bindings) != 25:
        raise ValueError("validated binding set requires exactly 25 program-arm bindings")
    by_id = {item["binding_id"]: item for item in bindings}
    if len(by_id) != 25 or set(by_id) != expected_ids:
        raise ValueError("bindings must be unique and cover the exact 25 program-arm matrix")
    lock_by_arm = {item["arm_id"]: item for item in contract["model_locks"]}
    expected_by_id = {item["binding_id"]: item for item in value["expected_bindings"]}
    for binding_id, binding in by_id.items():
        expected = expected_by_id[binding_id]
        if any(binding[key] != expected[key] for key in ("arm_id", "program_id", "logical_program_sha256")):
            raise ValueError(f"binding identity mismatch: {binding_id}")
        lock = lock_by_arm[binding["arm_id"]]
        if binding["model_lock_file_sha256"] != lock["file_sha256"]:
            raise ValueError(f"model-lock hash mismatch: {binding_id}")
        if binding["tokenizer_sha256"] != lock["tokenizer_sha256"]:
            raise ValueError(f"tokenizer hash mismatch: {binding_id}")
        if binding["adapter_contract_sha256"] != lock["adapter_contract_sha256"]:
            raise ValueError(f"adapter-contract hash mismatch: {binding_id}")
        if binding["compiler_source_manifest_sha256"] != contract["program_set"]["compiler_source_manifest_sha256"]:
            raise ValueError(f"compiler hash mismatch: {binding_id}")
        expected_limit = lock["effective_input_limit"]
        if expected_limit is None:
            if binding["effective_input_limit"] != binding["rendered_input_max_tokens"]:
                raise ValueError(
                    f"unbounded lexical input limit must equal observed maximum: {binding_id}"
                )
        elif binding["effective_input_limit"] != expected_limit:
            raise ValueError(f"effective-input limit mismatch: {binding_id}")
        if binding["rendered_input_max_tokens"] > binding["effective_input_limit"]:
            raise ValueError(f"overlength rendered input: {binding_id}")
        if any(binding[field] != 0 for field in contract["zero_required"]):
            raise ValueError(f"gap, omission, truncation, or overlength count is nonzero: {binding_id}")


def validate_binding_set(root: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a sanitized Owner-local template or completed binding receipt."""

    root = root.resolve()
    contract = _contract(root)
    _validate_schema(root, value)
    _safe(value)
    if value["binding_set_sha256"] != _self_hash(value):
        raise ValueError("binding-set self-hash mismatch")
    if value["contract_file_sha256"] != file_sha256(root / CONTRACT_PATH):
        raise ValueError("binding set contract file hash mismatch")
    _validate_frozen_bindings(value, contract)
    program_set = _read_json(root / PROGRAM_SET_PATH)
    expected_ids = _validate_expected_matrix(value, program_set)
    status = value["status"]
    receipts = value["owner_local_receipts"]
    if status == "pending_owner_local_protected_compilation":
        if value["bindings"] or any(item is not None for item in receipts.values()):
            raise ValueError("pending template must not claim receipts or actual bindings")
    elif status == "validated_owner_local_protected_compilation":
        if any(item is None for item in receipts.values()):
            raise ValueError("completed binding set requires all Owner-local receipt hashes")
        _validate_actual_bindings(value, contract, expected_ids)
    else:  # The schema rejects this; retain a fail-closed branch for direct callers.
        raise ValueError("unsupported binding-set status")
    return {
        "status": status,
        "binding_set_sha256": value["binding_set_sha256"],
        "expected_bindings": len(expected_ids),
        "actual_bindings": len(value["bindings"]),
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def write_pending_template(root: Path, output: Path) -> dict[str, Any]:
    """Write the deterministic template only outside the repository tree."""

    resolved_root = root.resolve()
    resolved_output = output.resolve()
    if resolved_output.is_relative_to(resolved_root):
        raise ValueError("Owner-local binding template must be outside the repository")
    template = pending_template(resolved_root)
    _validate_schema(resolved_root, template)
    _safe(template)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(_json_text(template), encoding="utf-8", newline="")
    return validate_binding_set(resolved_root, template)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-compiled-bindings-v12")
    parser.add_argument("command", choices=("template", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--binding-set", type=Path)
    args = parser.parse_args()
    if args.command == "template":
        if args.output is None:
            parser.error("template requires --output OUTSIDE_REPOSITORY")
        result = write_pending_template(args.repository_root, args.output)
    else:
        if args.binding_set is None:
            parser.error("validate requires --binding-set OWNER_LOCAL_RECEIPT.json")
        result = validate_binding_set(args.repository_root, _read_json(args.binding_set))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
