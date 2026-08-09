from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import myis_research.armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 as r3
from myis_research.armindex.a1_2_compiled_bindings_v12 import pending_template
from myis_research.armindex.a1_2_watchdog_provider_destroy_dry_run_v12 import (
    evaluate_payload,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64


def _git(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_git(_root: Path, *args: str) -> str:
        values = {
            ("status", "--porcelain=v1", "--untracked-files=all"): "",
            ("rev-parse", "HEAD^{commit}"): "b" * 40,
            ("rev-parse", "HEAD^{tree}"): "c" * 40,
            ("rev-parse", "origin/main"): "b" * 40,
            ("ls-files",): "\n".join(r3._BUNDLE_PATHS),
        }
        return values[args]

    monkeypatch.setattr(r3, "_git", fake_git)


def _binding_and_owner(
    shared: dict[str, str],
    *,
    anchor_file_sha256: str,
) -> tuple[dict[str, object], dict[str, object]]:
    binding = pending_template(ROOT)
    binding["binding_set_id"] = "a1.2-v12-r3-test-bindings"
    binding["status"] = "validated_owner_local_protected_compilation"
    binding["owner_local_receipts"] = shared
    expected = binding["expected_bindings"]
    locks = json.loads((ROOT / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json").read_text())["model_locks"]
    by_arm = {item["arm_id"]: item for item in locks}
    bindings = []
    for row in expected:
        lock = by_arm[row["arm_id"]]
        bindings.append({
            **row,
            "compiler_source_manifest_sha256": binding["frozen_bindings"]["compiler_source_manifest_sha256"],
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
        })
    binding["bindings"] = bindings
    binding["binding_set_sha256"] = canonical_sha256({key: value for key, value in binding.items() if key != "binding_set_sha256"})
    owner_body = {
        "schema_version": "myis.armindex-a1.2-owner-local-protected-compiler-receipt.v12-r3",
        "status": "PASS",
        "claim_boundary": "Aggregate-safe protected compiler test receipt only. It contains hashes and zero execution authority, preserves every protected payload outside the repository, and cannot contact a provider, adopt execution, launch a workload, retrieve, evaluate, or make a scientific claim.",
        **shared,
        "pre_adoption_anchor_sha256": anchor_file_sha256,
        "binding_set_sha256": binding["binding_set_sha256"],
        "binding_count": 25,
        "coverage_gap_count": 0,
        "omitted_unit_count": 0,
        "truncation_count": 0,
        "overlength_count": 0,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }
    owner = {**owner_body, "receipt_sha256": canonical_sha256(owner_body)}
    return binding, owner


def _transfer(
    tmp_path: Path,
    *,
    anchor: dict[str, object],
) -> tuple[Path, dict[str, str]]:
    handoff = json.loads((ROOT / r3.HANDOFF_REQUEST_PATH).read_text())
    workload_set = json.loads((ROOT / r3.WORKLOAD_SET_PATH).read_text())
    transfer_contract = json.loads((ROOT / r3.TRANSFER_CONTRACT_PATH).read_text())
    shared = {
        "handoff_receipt_sha256": "1" * 64,
        "protected_transfer_manifest_sha256": "0" * 64,
        "corpus_bundle_sha256": "2" * 64,
        "query_bundle_sha256": "3" * 64,
        "split_commitment_sha256": "4" * 64,
        "evaluator_sha256": "5" * 64,
        "ephemeral_token_map_sha256": "6" * 64,
    }
    body = {
        "transfer_id": "synthetic-r3-transfer",
        "request_sha256": r3.validate_contract(ROOT)["preserved_bindings"]["v11_request"]["self_sha256"],
        "adoption_receipt_sha256": anchor["anchor_sha256"],
        "dataset_revision": handoff["source_contract"]["dataset_revision"],
        "split_commitment_sha256": shared["split_commitment_sha256"],
        "evaluator_sha256": shared["evaluator_sha256"],
        "corpus_bundle_sha256": shared["corpus_bundle_sha256"],
        "corpus_bundle_bytes": 123,
        "corpus_family_count": 2,
        "query_bundle_sha256": shared["query_bundle_sha256"],
        "query_bundle_bytes": 456,
        "rep_dev_query_count": 150,
        "harness_dev_reserved_count": 100,
        "opaque_token_scheme_sha256": canonical_sha256(transfer_contract["opaque_token_contract"]),
        "ephemeral_token_map_sha256": shared["ephemeral_token_map_sha256"],
        "workload_manifest_set_sha256": workload_set["manifest_set_sha256"],
        "expected_result_rows_per_program": 150,
    }
    value = {**body, "manifest_sha256": canonical_sha256(body)}
    path = _write(tmp_path / "transfer.json", value)
    shared["protected_transfer_manifest_sha256"] = file_sha256(path)
    return path, shared


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def test_r3_contract_binds_v11_v12_and_v13_without_authorization() -> None:
    value = r3.validate_contract(ROOT)
    assert value["revision_id"] == r3.REVISION_ID
    assert value["authorization"]["launch_allowed"] is False
    assert value["counters"]["measured_runs"] == 0


def test_r3_bundle_is_deterministic_and_archive_tampering_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(monkeypatch)
    first = r3.build_bundle(ROOT, tmp_path / "first.tar.gz", receipt_output=tmp_path / "first.json")
    second = r3.build_bundle(ROOT, tmp_path / "second.tar.gz", receipt_output=tmp_path / "second.json")
    assert (tmp_path / "first.tar.gz").read_bytes() == (tmp_path / "second.tar.gz").read_bytes()
    assert first["bundle_sha256"] == second["bundle_sha256"]
    altered = tmp_path / "altered.tar.gz"
    altered.write_bytes((tmp_path / "first.tar.gz").read_bytes() + b"x")
    with pytest.raises(r3.AdoptionInputsV12R3Error):
        r3._bundle_receipt(ROOT, altered, tmp_path / "first.json", r3.validate_contract(ROOT))


def test_r3_finalizer_links_all_owner_hashes_and_writes_immutable_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(monkeypatch)
    bundle = tmp_path / "bundle.tar.gz"
    bundle_receipt = tmp_path / "bundle.json"
    r3.build_bundle(ROOT, bundle, receipt_output=bundle_receipt)
    anchor_path = tmp_path / "anchor.json"
    r3.build_anchor(ROOT, bundle_path=bundle, bundle_receipt_path=bundle_receipt, output=anchor_path)
    anchor = json.loads(anchor_path.read_text())
    transfer_path, shared = _transfer(tmp_path, anchor=anchor)
    binding, owner = _binding_and_owner(shared, anchor_file_sha256=file_sha256(anchor_path))
    binding_path = _write(tmp_path / "bindings.json", binding)
    owner_path = _write(tmp_path / "owner.json", owner)
    watchdog = evaluate_payload(ROOT, {
        "target_instance_identity_sha256": HASH,
        "ttl_seconds": 21600,
        "heartbeat_stale_seconds": 300,
        "simulated_elapsed_seconds": 21600,
        "simulated_heartbeat_age_seconds": 0,
        "expected_trigger": "ttl_expired",
        "command_template_tokens": ["<provider_cli>", "destroy", "instance", "<provider_instance_identity_sha256>"],
    }, receipt_id="a1.2-watchdog-provider-destroy-dry-run-r3-test-v12")
    watchdog_path = _write(tmp_path / "watchdog.json", watchdog)
    monkeypatch.setattr(r3, "RECEIPT_PATH", Path(".pytest-v12-r3/receipt.json"))
    try:
        receipt = r3.finalize(ROOT, bundle_path=bundle, bundle_receipt_path=bundle_receipt, pre_adoption_anchor_path=anchor_path, owner_receipt_path=owner_path, binding_set_path=binding_path, transfer_manifest_path=transfer_path, watchdog_receipt_path=watchdog_path)
        assert receipt["compiled_bindings"]["binding_count"] == 25
        assert receipt["owner_local_receipt"]["query_bundle_sha256"] == binding["owner_local_receipts"]["query_bundle_sha256"]
        assert (ROOT / r3.RECEIPT_PATH).is_file()
        assert r3.finalize(ROOT, bundle_path=bundle, bundle_receipt_path=bundle_receipt, pre_adoption_anchor_path=anchor_path, owner_receipt_path=owner_path, binding_set_path=binding_path, transfer_manifest_path=transfer_path, watchdog_receipt_path=watchdog_path) == receipt
    finally:
        target = ROOT / r3.RECEIPT_PATH
        target.unlink(missing_ok=True)
        target.parent.rmdir()


def test_r3_finalizer_rejects_one_mismatched_owner_commitment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(monkeypatch)
    bundle = tmp_path / "bundle.tar.gz"
    bundle_receipt = tmp_path / "bundle.json"
    r3.build_bundle(ROOT, bundle, receipt_output=bundle_receipt)
    anchor_path = tmp_path / "anchor.json"
    r3.build_anchor(ROOT, bundle_path=bundle, bundle_receipt_path=bundle_receipt, output=anchor_path)
    anchor = json.loads(anchor_path.read_text())
    _transfer_path, shared = _transfer(tmp_path, anchor=anchor)
    binding, owner = _binding_and_owner(shared, anchor_file_sha256=file_sha256(anchor_path))
    owner = copy.deepcopy(owner)
    owner["query_bundle_sha256"] = "f" * 64
    body = {key: value for key, value in owner.items() if key != "receipt_sha256"}
    owner["receipt_sha256"] = canonical_sha256(body)
    with pytest.raises(r3.AdoptionInputsV12R3Error, match="commitments differ"):
        r3._compiled_bindings(ROOT, _write(tmp_path / "binding.json", binding), r3._owner_receipt(ROOT, _write(tmp_path / "owner.json", owner)))
