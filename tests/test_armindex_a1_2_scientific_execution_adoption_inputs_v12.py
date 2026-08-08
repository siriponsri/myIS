from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_scientific_execution_adoption_inputs_v12 import (
    CONTRACT_PATH,
    V11_RECEIPT_FILE_SHA256,
    V11_REQUEST_FILE_SHA256,
    _validate_final_inputs,
    _validate_ledger_entries,
    finalize,
    materialize,
    validate,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.armindex.a1_2_watchdog_provider_destroy_dry_run_v12 import (
    evaluate_payload,
)


ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64


def _read(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _inputs() -> dict[str, object]:
    programs = _read("control/armindex/a1.2/common-program-set.v11.json")["programs"]
    program_hashes = {
        item["program_key"]: item["program_spec_sha256"] for item in programs
    }
    contract = _read(
        "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json"
    )
    expected: list[dict[str, object]] = []
    bindings: list[dict[str, object]] = []
    for arm in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        lock = next(item for item in contract["model_locks"] if item["arm_id"] == arm)
        for program_id, logical_hash in sorted(program_hashes.items()):
            binding_id = f"{arm}--{program_id}"
            expected.append(
                {
                    "binding_id": binding_id,
                    "arm_id": arm,
                    "program_id": program_id,
                    "logical_program_sha256": logical_hash,
                }
            )
            bindings.append(
                {
                    "binding_id": binding_id,
                    "arm_id": arm,
                    "program_id": program_id,
                    "logical_program_sha256": logical_hash,
                    "compiler_source_manifest_sha256": contract["program_set"][
                        "compiler_source_manifest_sha256"
                    ],
                    "model_lock_file_sha256": lock["file_sha256"],
                    "adapter_contract_sha256": lock["adapter_contract_sha256"],
                    "tokenizer_sha256": lock["tokenizer_sha256"],
                    "effective_input_limit": lock["effective_input_limit"] or 32,
                    "rendered_input_max_tokens": 32,
                    "compiled_representation_sha256": HASH,
                    "unit_count": 1,
                    "coverage_gap_count": 0,
                    "omitted_unit_count": 0,
                    "truncation_count": 0,
                    "overlength_count": 0,
                    "index_manifest_sha256": HASH,
                }
            )
    binding_set = {
        "schema_version": "myis.armindex-a1.2-compiled-program-binding-set.v12",
        "binding_set_id": "a1.2-v12-test-bindings",
        "status": "validated_owner_local_protected_compilation",
        "claim_boundary": "Aggregate-safe synthetic test evidence only; it does not represent a protected compilation or measured execution.",
        "contract_file_sha256": file_sha256(
            ROOT
            / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json"
        ),
        "frozen_bindings": {
            "v11_request_file_sha256": V11_REQUEST_FILE_SHA256,
            "v11_request_sha256": "2e95bf70d4843dadac03b442cb231573f73ec05a65884a70ac42d9713f52b7db",
            "program_set_file_sha256": file_sha256(
                ROOT / "control/armindex/a1.2/common-program-set.v11.json"
            ),
            "program_set_sha256": _read(
                "control/armindex/a1.2/common-program-set.v11.json"
            )["program_set_sha256"],
            "compiler_source_manifest_sha256": contract["program_set"][
                "compiler_source_manifest_sha256"
            ],
        },
        "owner_local_receipts": {
            key: HASH for key in contract["required_owner_local_receipt_hashes"]
        },
        "expected_bindings": expected,
        "bindings": bindings,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }
    binding_set["binding_set_sha256"] = canonical_sha256(binding_set)
    return {
        "execution_bundle": {
            "clean_worktree": True,
            "pushed_to_origin_main": True,
            "git_commit": "b" * 40,
            "git_tree": "c" * 40,
            "frozen_bundle_sha256": HASH,
            "receipt_sha256": HASH,
        },
        "owner_local_receipt": {
            "status": "PASS",
            "handoff_receipt_sha256": HASH,
            "protected_transfer_manifest_sha256": HASH,
            "receipt_sha256": HASH,
        },
        "compiled_bindings": binding_set,
        "watchdog_destroy_dry_run": evaluate_payload(
            ROOT,
            {
                "target_instance_identity_sha256": HASH,
                "ttl_seconds": 21600,
                "heartbeat_stale_seconds": 300,
                "simulated_elapsed_seconds": 21600,
                "simulated_heartbeat_age_seconds": 0,
                "expected_trigger": "ttl_expired",
                "command_template_tokens": [
                    "<provider_cli>",
                    "destroy",
                    "instance",
                    "<provider_instance_identity_sha256>",
                ],
            },
            receipt_id="a1.2-watchdog-provider-destroy-dry-run-adoption-inputs-v12",
        ),
    }


def test_v12_materializes_deterministically_and_keeps_execution_locked() -> None:
    before = file_sha256(ROOT / CONTRACT_PATH)
    result = materialize(ROOT)
    contract = _read(CONTRACT_PATH.as_posix())

    assert result["status"] == "PASS"
    assert file_sha256(ROOT / CONTRACT_PATH) == before
    assert (
        contract["preserved_v11"]["request"]["file_sha256"] == V11_REQUEST_FILE_SHA256
    )
    assert (
        contract["preserved_v11"]["receipt"]["file_sha256"] == V11_RECEIPT_FILE_SHA256
    )
    assert set(contract["authorization"].values()) == {False}
    assert set(contract["counters"].values()) == {0}
    assert contract["ready_for_live_adoption_goal"] is False


def test_v12_finalization_requires_exactly_25_zero_truncation_bindings() -> None:
    result = finalize(ROOT, _inputs())

    assert result["status"] == "LOCAL_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER"
    assert result["compiled_bindings"] == {
        "binding_set_sha256": _inputs()["compiled_bindings"]["binding_set_sha256"],
        "binding_count": 25,
        "truncation_count": 0,
        "overlength_count": 0,
    }
    assert result["ready_for_live_adoption_goal"] is True
    assert result["authorization"] == {
        "provider_contact_allowed": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval_allowed": False,
    }


@pytest.mark.parametrize("mutation", ("missing", "truncation", "unsafe", "watchdog"))
def test_v12_finalization_fails_closed_on_invalid_owner_inputs(mutation: str) -> None:
    inputs = copy.deepcopy(_inputs())
    if mutation == "missing":
        inputs["compiled_bindings"]["bindings"].pop()
        inputs["compiled_bindings"]["binding_set_sha256"] = canonical_sha256(
            {
                key: value
                for key, value in inputs["compiled_bindings"].items()
                if key != "binding_set_sha256"
            }
        )
    elif mutation == "truncation":
        inputs["compiled_bindings"]["bindings"][0]["truncation_count"] = 1
        inputs["compiled_bindings"]["binding_set_sha256"] = canonical_sha256(
            {
                key: value
                for key, value in inputs["compiled_bindings"].items()
                if key != "binding_set_sha256"
            }
        )
    else:
        if mutation == "unsafe":
            inputs["owner_local_receipt"]["query_ids"] = "forbidden"
        else:
            inputs["watchdog_destroy_dry_run"].pop("actual_destroy_receipt_required")

    with pytest.raises(ValueError):
        _validate_final_inputs(ROOT, inputs)


def test_v12_validate_does_not_require_protected_or_provider_values() -> None:
    result = validate(ROOT)
    assert result["provider_status"] == "PENDING_LIVE_PROVIDER"
    assert result["ready_for_live_adoption_goal"] is False
    assert result["compiled_bindings_required"] == 25


def test_v12_finalization_rejects_sha256_shaped_git_identity_fields() -> None:
    inputs = _inputs()
    inputs["execution_bundle"]["git_commit"] = HASH

    with pytest.raises(ValueError, match="40-hex git_commit"):
        _validate_final_inputs(ROOT, inputs)


def test_v12_ledger_validator_rejects_chain_or_hash_drift() -> None:
    lines = (
        (
            ROOT
            / "control/armindex/a1.2/scientific-execution-adoption-inputs-ledger.v12.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
    )
    entries = [json.loads(line) for line in lines]

    result = _validate_ledger_entries(entries)
    assert result["entry_count"] == 3

    drifted = copy.deepcopy(entries)
    drifted[-1]["previous_entry_sha256"] = HASH
    with pytest.raises(ValueError, match="chain mismatch"):
        _validate_ledger_entries(drifted)
