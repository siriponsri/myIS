"""Materialize and validate the additive A1.2 same-instance repair v7."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_live_preflight_revision import (
    RECEIPT_PATH as V6_RECEIPT_PATH,
    validate_live_revision,
)


REVISION_ID = "a1.2-live-preflight-same-instance-repair-v7"
CONTRACT_PATH = Path("control/armindex/a1.2/execution-contract.live-preflight-repair.v7.json")
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-live-preflight-repair.receipt.v7.json"
)
SCHEMA_PATH = Path("schemas/armindex/a1.2-live-preflight-repair.v7.json")
CONTINUATION_POLICY_PATH = Path("control/armindex/a1.2/owner-instance-continuation-policy.v1.json")
V7_COORDINATOR_PATH = Path("scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1")
V7_BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh")
V6_LAUNCHER_PATH = Path("scripts/a1_2_vast/remote-live-preflight-v6.sh")
SAFE_EXPORT_PATH = Path("control/armindex/a1.2/safe-export-allowlist.v6.json")
RUNTIME_LOCK_PATH = Path("control/armindex/a1.2/runtime-lock.direct-base.v5.json")
IMAGE_LOCK_PATH = Path("control/armindex/a1.2/image-digest-contract.direct-base.v5.json")
SUPPLEMENT_REQUIREMENTS_PATH = Path(
    "containers/a1_2_vast_4x3090/runtime/requirements.preflight-supplement.v7.txt"
)
SUPPLEMENT_WORKFLOW_PATH = Path(".github/workflows/a1-2-preflight-supplement-wheelhouse-v7.yml")
OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V7.md")

BINDING_PATHS = (
    V6_RECEIPT_PATH,
    CONTINUATION_POLICY_PATH,
    V7_COORDINATOR_PATH,
    V7_BOOTSTRAP_PATH,
    Path("scripts/a1_2_vast/validate_preflight_supplement_v7.py"),
    V6_LAUNCHER_PATH,
    SAFE_EXPORT_PATH,
    RUNTIME_LOCK_PATH,
    IMAGE_LOCK_PATH,
    SUPPLEMENT_REQUIREMENTS_PATH,
    SUPPLEMENT_WORKFLOW_PATH,
    Path("src/myis_research/armindex/a1_2_live_preflight.py"),
    Path("src/myis_research/armindex/a1_2_live_preflight_revision.py"),
    Path("src/myis_research/armindex/a1_2_live_preflight_repair_v7.py"),
    OWNER_RUNBOOK_PATH,
    SCHEMA_PATH,
)


class LiveRepairV7Error(ValueError):
    """Raised when v7 repair lineage or frozen bindings drift."""


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LiveRepairV7Error(f"JSON object required: {path.as_posix()}")
    return value


def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    body = dict(value)
    body[field] = canonical_sha256(body)
    return body


def _bindings(root: Path) -> list[dict[str, str]]:
    return [{"uri": path.as_posix(), "sha256": file_sha256(root / path)} for path in BINDING_PATHS]


def _validate_policy(policy: Mapping[str, Any]) -> None:
    if policy.get("schema_version") != "myis.armindex-a1.2-owner-instance-continuation-policy.v1":
        raise LiveRepairV7Error("v7 continuation policy schema mismatch")
    if policy.get("launch_allowed") is not False:
        raise LiveRepairV7Error("continuation policy cannot permit launch")
    counters = policy.get("measured_counters", {})
    if any(value != 0 for value in counters.values()):
        raise LiveRepairV7Error("continuation policy counters must remain zero")


def materialize_live_repair_v7(repository_root: Path) -> dict[str, Any]:
    """Create only the new v7 repair contract and aggregate-safe receipt."""

    root = repository_root.resolve()
    validate_live_revision(root)
    v6 = _load(root, V6_RECEIPT_PATH)
    policy = _load(root, CONTINUATION_POLICY_PATH)
    _validate_policy(policy)
    bindings = _bindings(root)
    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.live-preflight-repair.v7",
            "contract_id": REVISION_ID,
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "same_instance_repair_prepared_preflight_pending",
            "evidence_class": "live_engineering_preflight_repair",
            "scientific_authority": False,
            "claim_boundary": "same-instance synthetic preflight repair only; no measured retrieval or scientific result",
            "migration_from": {
                "uri": V6_RECEIPT_PATH.as_posix(),
                "receipt_sha256": v6["receipt_sha256"],
                "disposition": "preserved_immutable_additive_same_instance_repair",
            },
            "continuation_policy": {
                "uri": CONTINUATION_POLICY_PATH.as_posix(),
                "sha256": file_sha256(root / CONTINUATION_POLICY_PATH),
                "default_post_preflight_instruction": policy["default_post_preflight_instruction"],
            },
            "preserved_live_failures": [
                {
                    "failure_id": "v6-initial-wheelhouse-missing-pydantic",
                    "description": "initial staged wheelhouse lacked pydantic required by the repository runtime",
                    "disposition": "preserved_live_failure_repaired_by_hash_validated_supplement",
                },
                {
                    "failure_id": "v6-supplement-repair-mutated-pycache-tree",
                    "description": "supplement repair wrote __pycache__ into the frozen code tree",
                    "disposition": "preserved_live_failure_repaired_by_new_root_and_bytecode_suppression",
                },
            ],
            "active_correction": {
                "new_remote_root": "/opt/myis/a1.2-v7",
                "source_remote_root": "/opt/myis/a1.2-v6",
                "same_instance_reuse": True,
                "required_environment": {"PYTHONDONTWRITEBYTECODE": "1"},
                "reuse_only_after_sha256_validation": ["models", "wheelhouse", "jobs", "supplement_wheelhouse_v7"],
                "upload_only": ["new_frozen_code_bundle"],
                "fresh_root_required": True,
            },
            "image_runtime_lock": {
                "image_lock_uri": IMAGE_LOCK_PATH.as_posix(),
                "image_lock_sha256": file_sha256(root / IMAGE_LOCK_PATH),
                "runtime_lock_uri": RUNTIME_LOCK_PATH.as_posix(),
                "runtime_lock_sha256": file_sha256(root / RUNTIME_LOCK_PATH),
                "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
                "resolved_manifest_digest": "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20",
                "platform": "linux/amd64",
            },
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
            "synthetic_preflight_only": True,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
            },
            "bindings": bindings,
            "next_authorized_action": "Owner runs only the v7 same-instance repair preflight from the v7 runbook; validation, launch adoption, and measured retrieval remain closed.",
        },
        "contract_sha256",
    )
    (root / CONTRACT_PATH).write_text(_json_text(contract), encoding="utf-8", newline="")
    receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-live-preflight-repair.v7",
            "receipt_id": REVISION_ID,
            "revision_id": REVISION_ID,
            "status": "same_instance_repair_prepared_preflight_pending",
            "evidence_class": "live_engineering_preflight_repair",
            "scientific_authority": False,
            "claim_boundary": "same-instance synthetic preflight repair only; no measured retrieval or scientific result",
            "v6_receipt_sha256": v6["receipt_sha256"],
            "continuation_policy_sha256": file_sha256(root / CONTINUATION_POLICY_PATH),
            "contract_sha256": file_sha256(root / CONTRACT_PATH),
            "preserved_live_failure_ids": [item["failure_id"] for item in contract["preserved_live_failures"]],
            "new_remote_root": contract["active_correction"]["new_remote_root"],
            "pythondontwritebytecode": True,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_runs": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "bindings": bindings,
        },
        "receipt_sha256",
    )
    (root / RECEIPT_PATH).write_text(_json_text(receipt), encoding="utf-8", newline="")
    return {
        "status": receipt["status"],
        "revision_id": REVISION_ID,
        "contract_sha256": contract["contract_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
    }


def validate_live_repair_v7(repository_root: Path) -> dict[str, Any]:
    """Validate v7 lineage, frozen bindings, and launch-locked safety fields."""

    root = repository_root.resolve()
    validate_live_revision(root)
    contract = _load(root, CONTRACT_PATH)
    receipt = _load(root, RECEIPT_PATH)
    schema = _load(root, SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise LiveRepairV7Error(f"v7 receipt schema failure: {errors[0].message}")
    for payload, field in ((contract, "contract_sha256"), (receipt, "receipt_sha256")):
        body = dict(payload)
        recorded = body.pop(field, None)
        if recorded != canonical_sha256(body):
            raise LiveRepairV7Error(f"v7 {field} mismatch")
    for binding in contract["bindings"]:
        if file_sha256(root / binding["uri"]) != binding["sha256"]:
            raise LiveRepairV7Error(f"v7 binding mismatch: {binding['uri']}")
    if receipt["contract_sha256"] != file_sha256(root / CONTRACT_PATH):
        raise LiveRepairV7Error("v7 receipt contract binding mismatch")
    v6 = _load(root, V6_RECEIPT_PATH)
    if contract["migration_from"]["receipt_sha256"] != v6["receipt_sha256"]:
        raise LiveRepairV7Error("v7/v6 lineage mismatch")
    policy = _load(root, CONTINUATION_POLICY_PATH)
    _validate_policy(policy)
    if receipt["continuation_policy_sha256"] != file_sha256(root / CONTINUATION_POLICY_PATH):
        raise LiveRepairV7Error("v7 continuation policy binding mismatch")
    active = contract["active_correction"]
    if active["new_remote_root"] != "/opt/myis/a1.2-v7" or active["source_remote_root"] != "/opt/myis/a1.2-v6":
        raise LiveRepairV7Error("v7 remote-root correction mismatch")
    if active["required_environment"] != {"PYTHONDONTWRITEBYTECODE": "1"}:
        raise LiveRepairV7Error("v7 bytecode suppression is not exact")
    if contract["launch_allowed"] is not False or contract["adopted_for_execution"] is not False:
        raise LiveRepairV7Error("v7 cannot authorize scientific execution")
    if any(value != 0 for value in contract["real_counters"].values()) or any(
        value != 0 for value in contract["resource_counters"].values()
    ):
        raise LiveRepairV7Error("v7 counters must remain zero")
    return {
        "status": receipt["status"],
        "revision_id": REVISION_ID,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight-repair-v7")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = (
        materialize_live_repair_v7(args.repository_root)
        if args.command == "materialize"
        else validate_live_repair_v7(args.repository_root)
    )
    print(_json_text(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
