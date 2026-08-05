"""Validation for non-authorizing ArmIndex resource proposals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


PROPOSAL_PATH = Path(
    "campaigns/armindex-multiretriever-v2/proposals/a1.2-gpu-execution-plan.v1.json"
)


def load_and_validate_gpu_proposal(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    payload = json.loads((root / PROPOSAL_PATH).read_text(encoding="utf-8"))
    validate_gpu_proposal(root, payload)
    return payload


def validate_gpu_proposal(repository_root: Path, payload: Mapping[str, Any]) -> None:
    root = repository_root.resolve()
    if payload.get("schema_version") != "myis.armindex-a1.2-gpu-proposal.v1":
        raise ValueError("unsupported A1.2 GPU proposal")
    if payload.get("status") != "proposal_not_adopted_execution_locked":
        raise ValueError("A1.2 proposal cannot authorize execution")
    if payload.get("scientific_authority") is not False:
        raise ValueError("A1.2 planning proposal cannot claim scientific authority")
    if payload.get("protected_data_accessed") is not False:
        raise ValueError("A1.2 planning proposal cannot access protected data")
    unsigned = {key: value for key, value in payload.items() if key != "proposal_sha256"}
    if payload.get("proposal_sha256") != canonical_sha256(unsigned):
        raise ValueError("A1.2 proposal self-hash is invalid")
    for binding in payload.get("source_bindings", []):
        path = root / str(binding.get("uri", ""))
        if not path.is_file():
            raise ValueError("A1.2 proposal source binding is missing")
        if hashlib.sha256(path.read_bytes()).hexdigest() != binding.get("sha256"):
            raise ValueError("A1.2 proposal source binding hash mismatch")
    spec = payload.get("proposed_gpu_spec", {})
    if spec.get("gpu_count") != 1 or spec.get("minimum_vram_gib") != 24:
        raise ValueError("A1.2 proposal must remain a bounded single-GPU plan")
    if spec.get("a100_or_h100_required") is not False:
        raise ValueError("A1.2 proposal cannot require an unsubstantiated premium GPU")
    if spec.get("measured_runtime_network_enabled") is not False:
        raise ValueError("A1.2 measured runtime must remain offline")
    estimate = payload.get("time_estimate", {})
    if estimate.get("gpu_reservation_hours_min", 0) > estimate.get("gpu_reservation_hours_max", 0):
        raise ValueError("A1.2 GPU time estimate is invalid")
    budget = payload.get("budget_estimate", {})
    if budget.get("common_screen_hard_stop") != 18:
        raise ValueError("A1.2 screening budget drifted from the scientific plan")
    if budget.get("a1_total_hard_stop") != 23 or budget.get("campaign_hard_stop") != 100:
        raise ValueError("A1.2 cumulative budget ceilings are invalid")
    if budget.get("automatic_shutdown_required") is not True:
        raise ValueError("A1.2 proposal requires automatic shutdown")
    assert_aggregate_only(payload)
