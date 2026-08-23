from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_a7_contract_is_locked_to_a6_and_has_seven_layers() -> None:
    contract = _load("control/armindex/a7/a7-seven-layer-diagnosis-contract.v1.json")
    assert contract["status"] == "ACTIVE_OWNER_APPROVED_A6_HASH_BOUND"
    assert contract["execution_permitted"] is True
    assert contract["activation_receipt"] == "control/armindex/a7/a7-owner-approval-admission-20260823.json"
    assert contract["frozen_bindings"]["winner_binding_sha256"] == "551dd85b4df94eefe0a8dfc1e5cfbcdfb46b240b6144df192ae16cb4f025e7f2"
    assert contract["required_predecessor"]["required_pool_depth"] == 200
    assert len(contract["layers"]) == 8  # seven layers plus optional L3R reference
    assert contract["frozen_bindings"]["selection_accesses"] == 0
    assert contract["frozen_bindings"]["final_accesses"] == 0


def test_a7_readiness_is_hash_bound_and_owner_authorized() -> None:
    readiness = _load("control/armindex/a7/a7-seven-layer-readiness.v1.json")
    assert readiness["launch_allowed"] is True
    assert readiness["activation_receipt"] == "control/armindex/a7/a7-owner-approval-admission-20260823.json"
    assert readiness["predecessor"]["a6_authority_status"] == "PASS_A6_FROZEN_POOL_AUTHORITY"
    assert readiness["predecessor"]["a6_pool_sha256"] == "9ede1cee084db346743eb7e3dcbf300ac013c60055403f58449169dd71041879"
    assert readiness["predecessor"]["a6_evaluation_receipt_sha256"] == "5e8950b801dae04c408234336d8fbdc868a9c07c015b8519fdc7469d21fa1d3a"
    assert readiness["predecessor"]["a6_evaluation_sha256"] == "6766b09a5272384caec18d3514f46de9a6643e72ca179c86bdfa21527e4d2381"
