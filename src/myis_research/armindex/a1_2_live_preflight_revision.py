"""Materialize the additive A1.2 live-container correction revision v6."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_runtime_minimal_direct_base import (
    RECEIPT_PATH as V5_RECEIPT_PATH,
    validate_direct_base_revision,
)


REVISION_ID = "a1.2-live-preflight-correction-v6"
CONTRACT_PATH = Path("control/armindex/a1.2/execution-contract.live-preflight.v6.json")
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-correction.receipt.v6.json"
)
SCHEMA_PATH = Path("schemas/armindex/a1.2-live-preflight-correction.v6.json")
BINDING_PATHS = (
    V5_RECEIPT_PATH,
    Path("control/armindex/a1.2/runtime-lock.direct-base.v5.json"),
    Path("control/armindex/a1.2/image-digest-contract.direct-base.v5.json"),
    Path("control/armindex/a1.2/topology-contract.direct-base.v5.json"),
    Path("control/armindex/a1.2/safe-export-allowlist.v6.json"),
    Path("scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV6.ps1"),
    Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v6.sh"),
    Path("scripts/a1_2_vast/remote-live-preflight-v6.sh"),
    Path("src/myis_research/armindex/a1_2_live_preflight.py"),
    Path("src/myis_research/armindex/a1_2_live_preflight_revision.py"),
    Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V6.md"),
    SCHEMA_PATH,
)


class LiveRevisionError(ValueError):
    """Raised when v6 lineage or a bound implementation byte drifts."""


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LiveRevisionError(f"JSON object required: {path.as_posix()}")
    return value


def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    body = dict(value)
    body[field] = canonical_sha256(body)
    return body


def _bindings(root: Path) -> list[dict[str, str]]:
    return [{"uri": path.as_posix(), "sha256": file_sha256(root / path)} for path in BINDING_PATHS]


def materialize_live_revision(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_direct_base_revision(root)
    v5 = _load(root, V5_RECEIPT_PATH)
    bindings = _bindings(root)
    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.live-preflight.v6",
            "contract_id": REVISION_ID,
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "live_correction_prepared_preflight_pending",
            "evidence_class": "live_engineering_preflight_correction",
            "scientific_authority": False,
            "migration_from": {
                "uri": V5_RECEIPT_PATH.as_posix(),
                "receipt_sha256": v5["receipt_sha256"],
                "disposition": "preserved_immutable_additive_live_correction",
            },
            "observed_live_defects": [
                "direct_vast_container_has_no_docker_cli_or_socket",
                "ssh_login_shell_does_not_inherit_offline_environment",
            ],
            "corrections": {
                "offline_environment_injected_per_remote_command": True,
                "bundle_archive_commit_tree_and_all_file_hashes_verified": True,
                "image_identity_when_container_api_absent": "registry_manifest_binding_plus_exact_runtime_anchors_with_observability_limit_reported",
                "runtime_minimal_model_validation": True,
                "synthetic_gpu_adapter_checks": True,
                "checkpoint_resume_injected_failure": True,
                "safe_export_v6": True,
            },
            "disk_interpretation": {
                "provider_volume_capacity_gib_min": 249,
                "post_stage_free_gib_min": 230,
                "reason": "250-GiB allocation includes filesystem metadata and staged 6.12-GB models",
            },
            "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
            "resolved_manifest_digest": "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20",
            "platform": "linux/amd64",
            "live_quote_usd_per_hour": 0.656,
            "estimated_preflight_usd": {"two_hours": 1.312, "four_hours": 2.624, "six_hour_ttl": 3.936},
            "budget_hard_stops_usd": {"common_screen": 18, "a1": 23, "campaign": 100},
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
            "synthetic_preflight_only": True,
            "bindings": bindings,
            "next_authorized_action": "Run v6 upload, structural verification, synthetic GPU adapter and checkpoint-resume preflight, collect safe artifacts, then require Owner provider destruction.",
        },
        "contract_sha256",
    )
    (root / CONTRACT_PATH).write_text(_json_text(contract), encoding="utf-8", newline="")
    receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-live-preflight-correction.v6",
            "receipt_id": REVISION_ID,
            "revision_id": REVISION_ID,
            "status": "live_correction_prepared_preflight_pending",
            "evidence_class": "live_engineering_preflight_correction",
            "scientific_authority": False,
            "claim_boundary": "live container compatibility correction only; no measured retrieval or scientific result",
            "v5_receipt_sha256": v5["receipt_sha256"],
            "contract_sha256": file_sha256(root / CONTRACT_PATH),
            "observed_live_defects": contract["observed_live_defects"],
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


def validate_live_revision(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_direct_base_revision(root)
    contract = _load(root, CONTRACT_PATH)
    receipt = _load(root, RECEIPT_PATH)
    schema = _load(root, SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise LiveRevisionError(f"v6 receipt schema failure: {errors[0].message}")
    for payload, field in ((contract, "contract_sha256"), (receipt, "receipt_sha256")):
        body = dict(payload)
        recorded = body.pop(field, None)
        if recorded != canonical_sha256(body):
            raise LiveRevisionError(f"v6 {field} mismatch")
    for binding in contract["bindings"]:
        if file_sha256(root / binding["uri"]) != binding["sha256"]:
            raise LiveRevisionError(f"v6 binding mismatch: {binding['uri']}")
    if receipt["contract_sha256"] != file_sha256(root / CONTRACT_PATH):
        raise LiveRevisionError("v6 receipt contract binding mismatch")
    if contract["migration_from"]["receipt_sha256"] != receipt["v5_receipt_sha256"]:
        raise LiveRevisionError("v6/v5 lineage mismatch")
    if contract["launch_allowed"] is not False or contract["adopted_for_execution"] is not False:
        raise LiveRevisionError("v6 cannot authorize scientific execution")
    return {
        "status": receipt["status"],
        "revision_id": REVISION_ID,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight-revision")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = (
        materialize_live_revision(args.repository_root)
        if args.command == "materialize"
        else validate_live_revision(args.repository_root)
    )
    print(_json_text(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
