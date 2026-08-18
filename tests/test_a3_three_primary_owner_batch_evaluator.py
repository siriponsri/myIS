from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from myis_research.armindex.a3_three_primary_remote_retriever import (
    build_remote_cell_request,
    run_remote_retrieval_cell,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_a3_three_primary_owner_local.py"
SPEC = importlib.util.spec_from_file_location("a3_owner_batch_evaluator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


ARMS = ("ARM-03", "ARM-04", "ARM-05")


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="ascii")


def _self_hash(value: dict[str, object], field: str) -> dict[str, object]:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})
    return value


def _execution_contract() -> dict[str, object]:
    matrix = [
        {
            "source_arm_id": source,
            "target_arm_id": target,
            "post_admission_action": "reuse_self_winner" if source == target else "validate_cross_arm_transfer",
            "winner_program_sha256": "a" * 64,
            "target_adapter_sha256": "b" * 64,
            "result_scope": "aggregate_only",
        }
        for source in ARMS
        for target in ARMS
    ]
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-execution-contract.v1",
            "status": "READY_FOR_POST_ADMISSION_EXECUTION",
            "runtime_bindings_sha256": "c" * 64,
            "transfer_matrix": matrix,
            "fixed_union_sha256": "d" * 64,
            "harness_batch_sha256s": ["e" * 64],
            "execution_order": ["transfer_matrix", "fixed_union_controls", "complete_harnessopt_batches"],
            "selection_permitted": False,
            "final_permitted": False,
            "provider_contact_performed": False,
            "remote_execution_performed": False,
            "execution_contract_sha256": "",
        },
        "execution_contract_sha256",
    )


def _stage(runtime_sha: str, execution_sha: str, *, assets: dict[str, object]) -> dict[str, object]:
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-stage-receipt.v1",
            "status": "PASS_A3_ISOLATED_REMOTE_STAGE",
            "attempt_id": "a3-goal003-20260818-101",
            "remote_root": "/opt/myis/a3-goal003-20260818-101",
            "stage_manifest_sha256": "f" * 64,
            "code_bundle_sha256": "0" * 64,
            "runtime_assets_archive_sha256": "1" * 64,
            "runtime_assets_inventory_sha256": "2" * 64,
            "remote_asset_sha256s": assets,
            "staged_file_count": 3,
            "rankings_returned": False,
            "protected_payload_included": False,
            "receipt_sha256": "",
        },
        "receipt_sha256",
    )


def _runtime_bindings(*, qrels_sha: str, membership_sha: str, corpus_sha: str, queries_sha: str) -> dict[str, object]:
    package = {
        "corpus_sha256": corpus_sha,
        "query_bundle_sha256": queries_sha,
        "split_commitment_sha256": "3" * 64,
        "evaluator_sha256": "4" * 64,
        "qrels_commitment_sha256": qrels_sha,
        "membership_commitment_sha256": membership_sha,
        "runtime_lock_sha256": "5" * 64,
        "data_handoff_sha256": "6" * 64,
    }
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-runtime-bindings.v1",
            "primary_arm_scope": list(ARMS),
            "budget_extension_sha256": "7" * 64,
            "authority_sha256": "8" * 64,
            "manifest_sha256": "9" * 64,
            "admission_sha256": "a" * 64,
            "winner_bindings": {
                arm: {"winner_program_sha256": "b" * 64, "winner_selection_receipt_sha256": "c" * 64}
                for arm in ARMS
            },
            "target_adapter_sha256s": {arm: "d" * 64 for arm in ARMS},
            "package_bindings": package,
            "runtime_bindings_sha256": "",
        },
        "runtime_bindings_sha256",
    )


def _fixture_batch(tmp_path: Path) -> dict[str, Path]:
    owner = tmp_path / "owner-store"
    package = owner / "train-package"
    qrels_rows = [{"work_token": f"Q-{index:03d}", "relevance": {"F-001": 1}} for index in range(250)]
    membership_rows = [{"work_token": f"Q-{index:03d}", "eligible_out": True} for index in range(250)]
    _write_text(package / "inputs" / "qrels.jsonl", "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in qrels_rows) + "\n")
    _write_text(package / "inputs" / "membership.jsonl", "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in membership_rows) + "\n")
    qrels_path = package / "inputs" / "qrels.jsonl"
    membership_path = package / "inputs" / "membership.jsonl"
    qrels_sha, membership_sha = file_sha256(qrels_path), file_sha256(membership_path)
    corpus_sha, queries_sha = "e" * 64, "f" * 64
    bindings = _runtime_bindings(qrels_sha=qrels_sha, membership_sha=membership_sha, corpus_sha=corpus_sha, queries_sha=queries_sha)
    _write(owner / "runtime-bindings.json", bindings)
    _write(package / "train-scope.json", {
        "schema_version": "myis.armindex-a3-train-scope.v1", "scope": "Train-250", "split_id": "Train-250",
        "query_count": 250, "queries_sha256": queries_sha, "split_commitment_sha256": "3" * 64,
    })
    package_bindings = {
        "input_hashes": {"corpus_sha256": corpus_sha, "queries_sha256": queries_sha, "qrels_sha256": qrels_sha, "membership_sha256": membership_sha},
        "package_bindings_sha256": "",
    }
    _write(package / "package-bindings.json", _self_hash(package_bindings, "package_bindings_sha256"))
    receipt = {
        "schema_version": "myis.armindex-a3-train250-owner-package-receipt.v1", "status": "PASS_A3_TRAIN250_OWNER_PACKAGE",
        "query_count": 250, "corpus_sha256": corpus_sha, "queries_sha256": queries_sha,
        "qrels_sha256": qrels_sha, "membership_sha256": membership_sha, "receipt_sha256": "",
    }
    _write(package / "A3_TRAIN250_OWNER_PACKAGE_RECEIPT.json", _self_hash(receipt, "receipt_sha256"))
    assets = {"corpus_sha256": corpus_sha, "queries_sha256": queries_sha, "model_sha256s": {arm: str(index + 1) * 64 for index, arm in enumerate(ARMS)}}
    contract = _execution_contract()
    contract["runtime_bindings_sha256"] = bindings["runtime_bindings_sha256"]
    contract["execution_contract_sha256"] = canonical_sha256({key: item for key, item in contract.items() if key != "execution_contract_sha256"})
    stage = _stage(bindings["runtime_bindings_sha256"], contract["execution_contract_sha256"], assets=assets)
    stage_manifest = {
        "schema_version": "myis.armindex-a3-three-primary-remote-stage-manifest.v1",
        "status": "READY_A3_ISOLATED_REMOTE_STAGE", "attempt_id": stage["attempt_id"], "remote_root": stage["remote_root"],
        "runtime_bindings_sha256": bindings["runtime_bindings_sha256"], "execution_contract_sha256": contract["execution_contract_sha256"],
        "harness_batch_sha256s": ["e" * 64], "code_bundle_sha256": "0" * 64, "runtime_assets_archive_sha256": "1" * 64,
        "runtime_assets_inventory_sha256": "2" * 64, "remote_asset_sha256s": assets,
        "selection_permitted": False, "final_permitted": False, "stage_manifest_sha256": "",
    }
    _write(owner / "stage-manifest.json", _self_hash(stage_manifest, "stage_manifest_sha256"))
    stage["stage_manifest_sha256"] = stage_manifest["stage_manifest_sha256"]
    stage = _self_hash(stage, "receipt_sha256")
    _write(owner / "stage-receipt.json", stage)
    requests, rankings, returns = owner / "requests", owner / "rankings", owner / "returns"
    operations: list[tuple[str, str, str | None, str | None, str | None, list[str]]] = []
    for source in ARMS:
        for target in ARMS:
            operations.append((f"transfer-arm-{source[-2:]}-to-arm-{target[-2:]}", "transfer_cell", source, target, None, [target]))
    operations.extend([
        ("fixed-best-single", "fixed_union", None, None, "best_single", ["ARM-03"]),
        ("fixed-all-primary-rrf60", "fixed_union", None, None, "all_primary_rrf60", list(ARMS)),
        ("fixed-top-two-rrf60", "fixed_union", None, None, "top_two_rrf60", ["ARM-03", "ARM-04"]),
        ("fixed-top-three-rrf60", "fixed_union", None, None, "top_three_rrf60", list(ARMS)),
        ("fixed-commercial-only-fixed-union", "fixed_union", None, None, "commercial_only_fixed_union", ["ARM-04", "ARM-05"]),
    ])
    ranks = {
        f"Q-{index:03d}": [{"family_token": f"F-{rank:03d}", "rank": rank, "score": 1.0 / rank} for rank in range(1, 101)]
        for index in range(250)
    }
    for operation_id, kind, source, target, control, arm_ids in operations:
        request = build_remote_cell_request(
            contract, operation_id=operation_id, operation_kind=kind, source_arm_id=source, target_arm_id=target,
            fixed_union_control_id=control, retrieval_arm_ids=arm_ids, output_depth_by_arm={arm: 100 for arm in arm_ids}, remote_asset_sha256s=assets,
        )
        _write(requests / f"{operation_id}.json", request)
        ranking = run_remote_retrieval_cell(request, ranker=lambda _request: {"rankings": ranks, "coverage": {"expected_units": 250, "completed_units": 250}, "latency": {"wall_seconds": 1.0, "search_p95_seconds": 0.01}})
        ranking_path = rankings / f"{operation_id}.json"
        _write(ranking_path, ranking)
        returned = {
            "schema_version": "myis.armindex-a3-three-primary-transient-ranking-return-receipt.v1",
            "status": "PASS_A3_TRANSIENT_OWNER_LOCAL_RANKING_RETURN", "attempt_id": stage["attempt_id"],
            "operation_id": operation_id, "request_sha256": request["request_sha256"], "stage_receipt_sha256": stage["receipt_sha256"],
            "launch_receipt_sha256": "0" * 64, "ranking_sha256": ranking["ranking_sha256"],
            "ranking_package_receipt_sha256": ranking["receipt_sha256"], "ranking_package_file_sha256": file_sha256(ranking_path),
            "owner_local_only": True, "evaluation_pending": True, "rankings_embedded": False,
            "protected_payload_included": False, "receipt_sha256": "",
        }
        _write(returns / f"{operation_id}.json", _self_hash(returned, "receipt_sha256"))
    return {"owner": owner, "package": package, "requests": requests, "rankings": rankings, "returns": returns}


def test_owner_batch_evaluator_emits_only_aggregate_safe_artifacts(tmp_path: Path) -> None:
    paths = _fixture_batch(tmp_path)
    result = MODULE.evaluate_a3_owner_batch(
        owner_store_root=paths["owner"], stage_receipt_path=paths["owner"] / "stage-receipt.json", stage_manifest_path=paths["owner"] / "stage-manifest.json",
        runtime_bindings_path=paths["owner"] / "runtime-bindings.json", train_package_root=paths["package"],
        requests_dir=paths["requests"], rankings_dir=paths["rankings"], return_receipts_dir=paths["returns"],
        aggregate_output_dir=paths["owner"] / "aggregate", safe_return_receipt_path=paths["owner"] / "safe-return.json",
    )
    assert result["operation_count"] == 14
    assert result["protected_payload_included"] is False
    assert len(list((paths["owner"] / "aggregate").glob("*.aggregate-result.json"))) == 14
    safe_return = json.loads((paths["owner"] / "safe-return.json").read_text(encoding="ascii"))
    assert safe_return["rankings_returned"] is False
    assert safe_return["aggregate_result_count"] == 14


def test_owner_batch_evaluator_rejects_a_repository_destination_before_evaluation(tmp_path: Path) -> None:
    paths = _fixture_batch(tmp_path)
    with pytest.raises(MODULE.A3OwnerBatchEvaluatorError, match="must remain inside the Owner Store"):
        MODULE.evaluate_a3_owner_batch(
            owner_store_root=paths["owner"], stage_receipt_path=paths["owner"] / "stage-receipt.json", stage_manifest_path=paths["owner"] / "stage-manifest.json",
            runtime_bindings_path=paths["owner"] / "runtime-bindings.json", train_package_root=paths["package"],
            requests_dir=paths["requests"], rankings_dir=paths["rankings"], return_receipts_dir=paths["returns"],
            aggregate_output_dir=tmp_path / "repository-visible-output", safe_return_receipt_path=paths["owner"] / "safe-return.json",
        )


def test_owner_batch_cli_maps_stage_receipt_to_path_parameter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_evaluate(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"status": "PASS"}

    monkeypatch.setattr(MODULE, "evaluate_a3_owner_batch", fake_evaluate)
    values = {
        "owner-store-root": tmp_path / "owner",
        "stage-receipt": tmp_path / "stage-receipt.json",
        "stage-manifest": tmp_path / "stage-manifest.json",
        "runtime-bindings": tmp_path / "runtime.json",
        "train-package-root": tmp_path / "train",
        "requests-dir": tmp_path / "requests",
        "rankings-dir": tmp_path / "rankings",
        "return-receipts-dir": tmp_path / "returns",
        "aggregate-output-dir": tmp_path / "aggregate",
        "safe-return-receipt": tmp_path / "safe-return.json",
    }
    argv = [item for flag, value in values.items() for item in (f"--{flag}", str(value))]

    assert MODULE.main(argv) == 0
    assert captured["stage_receipt_path"] == values["stage-receipt"]
    assert captured["stage_manifest_path"] == values["stage-manifest"]
    assert captured["runtime_bindings_path"] == values["runtime-bindings"]
    assert captured["safe_return_receipt_path"] == values["safe-return-receipt"]
