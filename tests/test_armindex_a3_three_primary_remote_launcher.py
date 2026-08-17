from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a3_three_primary_remote_launcher import (
    A3ThreePrimaryRemoteLauncherError,
    build_a3_remote_stage_manifest,
    collect_a3_remote_ranking_package,
    launch_a3_remote_operation,
    stage_a3_remote_runtime,
    validate_a3_remote_launch_receipt,
    validate_a3_remote_stage_manifest,
    validate_a3_remote_stage_receipt,
    validate_a3_transient_ranking_return_receipt,
)
from myis_research.armindex.a3_three_primary_remote_retriever import (
    build_remote_cell_request,
    run_remote_retrieval_cell,
)
from myis_research.armindex.a3_three_primary_remote_worker import (
    execute_a3_remote_worker,
    validate_a3_remote_completion_receipt,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256


PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")


def _self_hash(value: dict[str, object], field: str) -> dict[str, object]:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})
    return value


def _contract(*, batches: int = 1) -> dict[str, object]:
    matrix = [
        {
            "source_arm_id": source,
            "target_arm_id": target,
            "post_admission_action": "reuse_self_winner" if source == target else "validate_cross_arm_transfer",
            "winner_program_sha256": "1" * 64,
            "target_adapter_sha256": "2" * 64,
            "result_scope": "aggregate_only",
        }
        for source in PRIMARY_ARMS
        for target in PRIMARY_ARMS
    ]
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-execution-contract.v1",
            "status": "READY_FOR_POST_ADMISSION_EXECUTION",
            "runtime_bindings_sha256": "3" * 64,
            "transfer_matrix": matrix,
            "fixed_union_sha256": "4" * 64,
            "harness_batch_sha256s": [str(index + 5) * 64 for index in range(batches)],
            "execution_order": ["transfer_matrix", "fixed_union_controls", "complete_harnessopt_batches"],
            "selection_permitted": False,
            "final_permitted": False,
            "provider_contact_performed": False,
            "remote_execution_performed": False,
            "execution_contract_sha256": "",
        },
        "execution_contract_sha256",
    )


def _assets() -> dict[str, object]:
    return {
        "corpus_sha256": "8" * 64,
        "queries_sha256": "9" * 64,
        "model_sha256s": {arm_id: str(index + 1) * 64 for index, arm_id in enumerate(PRIMARY_ARMS)},
    }


def _stage_manifest(tmp_path: Path) -> tuple[dict[str, object], dict[str, Path]]:
    code = tmp_path / "code.tar.gz"
    archive = tmp_path / "assets.tar.gz"
    inventory = tmp_path / "A3_RUNTIME_ASSETS.json"
    code.write_bytes(b"safe code bundle")
    archive.write_bytes(b"opaque owner-local assets")
    inventory.write_text(canonical_json(_assets()), encoding="utf-8")
    manifest = build_a3_remote_stage_manifest(
        _contract(),
        attempt_id="a3-goal003-20260817-001",
        remote_root="/opt/myis/a3-goal003-20260817-001",
        code_bundle_sha256=file_sha256(code),
        runtime_assets_archive_sha256=file_sha256(archive),
        runtime_assets_inventory_sha256=file_sha256(inventory),
        remote_asset_sha256s=_assets(),
    )
    return manifest, {"code": code, "archive": archive, "inventory": inventory}


def _ssh_material(tmp_path: Path) -> tuple[Path, Path]:
    key, known = tmp_path / "id_ed25519", tmp_path / "known_hosts"
    key.write_text("fixture key path only", encoding="utf-8")
    known.write_text("fixture known host", encoding="utf-8")
    return key, known


def test_stage_manifest_requires_new_a3_root_and_complete_extended_batches(tmp_path: Path) -> None:
    manifest, _files = _stage_manifest(tmp_path)
    assert validate_a3_remote_stage_manifest(manifest) == manifest

    with pytest.raises(A3ThreePrimaryRemoteLauncherError, match="one to three"):
        build_a3_remote_stage_manifest(
            _contract(batches=0),
            attempt_id="a3-goal003-20260817-001",
            remote_root="/opt/myis/a3-goal003-20260817-001",
            code_bundle_sha256="a" * 64,
            runtime_assets_archive_sha256="b" * 64,
            runtime_assets_inventory_sha256="c" * 64,
            remote_asset_sha256s=_assets(),
        )
    with pytest.raises(A3ThreePrimaryRemoteLauncherError, match="new isolated A3 root"):
        build_a3_remote_stage_manifest(
            _contract(),
            attempt_id="a3-goal003-20260817-001",
            remote_root="/opt/myis/a2-goal004-20260816-005",
            code_bundle_sha256="a" * 64,
            runtime_assets_archive_sha256="b" * 64,
            runtime_assets_inventory_sha256="c" * 64,
            remote_asset_sha256s=_assets(),
        )


def test_stage_and_launch_emit_only_aggregate_safe_receipts(tmp_path: Path) -> None:
    manifest, files = _stage_manifest(tmp_path)
    key, known = _ssh_material(tmp_path)
    calls: list[list[str]] = []

    def run(arguments: list[str]) -> str:
        calls.append(arguments)
        return "4242\n" if "nohup" in arguments[-1] else ""

    stage = stage_a3_remote_runtime(
        manifest,
        code_bundle=files["code"],
        runtime_assets_archive=files["archive"],
        runtime_assets_inventory=files["inventory"],
        ssh_host="host.example",
        ssh_port=51007,
        ssh_key_path=key,
        known_hosts_path=known,
        run=run,
    )
    assert validate_a3_remote_stage_receipt(stage) == stage
    assert stage["rankings_returned"] is False
    assert stage["protected_payload_included"] is False

    request = build_remote_cell_request(
        _contract(),
        operation_id="a3-self-03",
        operation_kind="transfer_cell",
        source_arm_id="ARM-03",
        target_arm_id="ARM-03",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-03"],
        output_depth_by_arm={"ARM-03": 100},
        remote_asset_sha256s=_assets(),
    )
    request_path = tmp_path / "request.json"
    request_path.write_text(canonical_json(request), encoding="utf-8")
    launch = launch_a3_remote_operation(
        stage,
        request,
        request_manifest=request_path,
        ssh_host="host.example",
        ssh_port=51007,
        ssh_key_path=key,
        known_hosts_path=known,
        remote_python="/opt/myis/a3-runtime/venv/bin/python",
        run=run,
    )
    assert validate_a3_remote_launch_receipt(launch) == launch
    assert launch["remote_pid"] == "4242"
    assert all("qrels" not in " ".join(call) for call in calls)
    launch_command = next(call[-1] for call in calls if "nohup" in call[-1])
    assert f"mkdir -p {manifest['remote_root']}/output;" in launch_command
    assert f"mkdir -p {manifest['remote_root']}/output/a3-self-03;" not in launch_command


def test_stage_rejects_unbound_a2_asset_reuse_root(tmp_path: Path) -> None:
    manifest, files = _stage_manifest(tmp_path)
    key, known = _ssh_material(tmp_path)
    with pytest.raises(A3ThreePrimaryRemoteLauncherError, match="asset reuse source"):
        stage_a3_remote_runtime(
            manifest,
            code_bundle=files["code"],
            runtime_assets_archive=files["archive"],
            runtime_assets_inventory=files["inventory"],
            ssh_host="host.example",
            ssh_port=51007,
            ssh_key_path=key,
            known_hosts_path=known,
            remote_reuse_assets_root="/opt/myis/a2-other/assets",
            run=lambda _arguments: "",
        )


def test_stage_rejects_a_local_asset_hash_mismatch(tmp_path: Path) -> None:
    manifest, files = _stage_manifest(tmp_path)
    files["code"].write_bytes(b"changed")
    key, known = _ssh_material(tmp_path)
    with pytest.raises(A3ThreePrimaryRemoteLauncherError, match="does not match"):
        stage_a3_remote_runtime(
            manifest,
            code_bundle=files["code"],
            runtime_assets_archive=files["archive"],
            runtime_assets_inventory=files["inventory"],
            ssh_host="host.example",
            ssh_port=51007,
            ssh_key_path=key,
            known_hosts_path=known,
            run=lambda _arguments: "",
        )


def test_launch_rejects_a_request_file_that_does_not_match_its_request_hash(tmp_path: Path) -> None:
    manifest, _files = _stage_manifest(tmp_path)
    stage = {
        "schema_version": "myis.armindex-a3-three-primary-stage-receipt.v1",
        "status": "PASS_A3_ISOLATED_REMOTE_STAGE",
        "attempt_id": manifest["attempt_id"],
        "remote_root": manifest["remote_root"],
        "stage_manifest_sha256": manifest["stage_manifest_sha256"],
        "code_bundle_sha256": manifest["code_bundle_sha256"],
        "runtime_assets_archive_sha256": manifest["runtime_assets_archive_sha256"],
        "runtime_assets_inventory_sha256": manifest["runtime_assets_inventory_sha256"],
        "remote_asset_sha256s": manifest["remote_asset_sha256s"],
        "staged_file_count": 3,
        "rankings_returned": False,
        "protected_payload_included": False,
        "receipt_sha256": "",
    }
    _self_hash(stage, "receipt_sha256")
    request = build_remote_cell_request(
        _contract(),
        operation_id="a3-self-04",
        operation_kind="transfer_cell",
        source_arm_id="ARM-04",
        target_arm_id="ARM-04",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-04"],
        output_depth_by_arm={"ARM-04": 100},
        remote_asset_sha256s=_assets(),
    )
    request_path = tmp_path / "wrong-request.json"
    request_path.write_text(json.dumps({"wrong": True}), encoding="utf-8")
    key, known = _ssh_material(tmp_path)
    with pytest.raises(A3ThreePrimaryRemoteLauncherError, match="request manifest does not match"):
        launch_a3_remote_operation(
            stage,
            request,
            request_manifest=request_path,
            ssh_host="host.example",
            ssh_port=51007,
            ssh_key_path=key,
            known_hosts_path=known,
            remote_python="/opt/myis/a3-runtime/venv/bin/python",
            run=lambda _arguments: "",
        )


def test_remote_worker_uses_bound_asset_ranker_and_emits_no_ranking_in_completion(
    tmp_path: Path,
) -> None:
    request = build_remote_cell_request(
        _contract(),
        operation_id="a3-cross-03-05",
        operation_kind="transfer_cell",
        source_arm_id="ARM-03",
        target_arm_id="ARM-05",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-05"],
        output_depth_by_arm={"ARM-05": 3},
        remote_asset_sha256s=_assets(),
    )
    request_path = tmp_path / "request.json"
    request_path.write_text(canonical_json(request), encoding="utf-8")
    assets = tmp_path / "assets"
    (assets / "bin").mkdir(parents=True)
    (assets / "bin" / "ranker").write_text("opaque executable", encoding="ascii")
    inventory = {
        "schema_version": "myis.armindex-a3-runtime-assets-inventory.v1",
        "remote_asset_sha256s": _assets(),
        "ranker_command": ["bin/ranker"],
        "inventory_sha256": "",
    }
    _self_hash(inventory, "inventory_sha256")
    (assets / "A3_RUNTIME_ASSETS.json").write_text(canonical_json(inventory), encoding="utf-8")

    def ranker(arguments: list[str]) -> None:
        result = Path(arguments[arguments.index("--result") + 1])
        result.write_text(
            canonical_json(
                {
                    "rankings": {
                        "Q-001": [
                            {"family_token": f"F-{rank}", "rank": rank, "score": 1.0 / rank}
                            for rank in range(1, 4)
                        ]
                    },
                    "coverage": {"expected_units": 1, "completed_units": 1},
                    "latency": {"wall_seconds": 1.0, "search_p95_seconds": 1.0},
                }
            ),
            encoding="utf-8",
        )

    completion = execute_a3_remote_worker(
        request_path, assets_root=assets, output_root=tmp_path / "operation", ranker_runner=ranker
    )
    assert validate_a3_remote_completion_receipt(completion) == completion
    assert completion["rankings_embedded"] is False
    assert completion["qrels_opened"] is False
    assert (tmp_path / "operation" / "ranking-package.json").is_file()


def test_transient_ranking_return_is_bound_and_aggregate_safe(tmp_path: Path) -> None:
    manifest, files = _stage_manifest(tmp_path)
    key, known = _ssh_material(tmp_path)
    stage = stage_a3_remote_runtime(
        manifest,
        code_bundle=files["code"],
        runtime_assets_archive=files["archive"],
        runtime_assets_inventory=files["inventory"],
        ssh_host="host.example",
        ssh_port=51007,
        ssh_key_path=key,
        known_hosts_path=known,
        run=lambda _arguments: "",
    )
    request = build_remote_cell_request(
        _contract(),
        operation_id="a3-self-05",
        operation_kind="transfer_cell",
        source_arm_id="ARM-05",
        target_arm_id="ARM-05",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-05"],
        output_depth_by_arm={"ARM-05": 3},
        remote_asset_sha256s=_assets(),
    )
    request_path = tmp_path / "request.json"
    request_path.write_text(canonical_json(request), encoding="utf-8")
    launch = launch_a3_remote_operation(
        stage,
        request,
        request_manifest=request_path,
        ssh_host="host.example",
        ssh_port=51007,
        ssh_key_path=key,
        known_hosts_path=known,
        remote_python="/opt/myis/a3-runtime/venv/bin/python",
        run=lambda _arguments: "99\n" if "nohup" in _arguments[-1] else "",
    )
    package = run_remote_retrieval_cell(
        request,
        ranker=lambda _request: {
            "rankings": {
                "Q-001": [
                    {"family_token": f"F-{rank}", "rank": rank, "score": 1.0 / rank}
                    for rank in range(1, 4)
                ]
            },
            "coverage": {"expected_units": 1, "completed_units": 1},
            "latency": {"wall_seconds": 1.0, "search_p95_seconds": 1.0},
        },
    )
    destination = tmp_path / "owner-store" / "a3-self-05.ranking-package.json"

    def return_runner(arguments: list[str]) -> str:
        if arguments[0] == "scp":
            Path(arguments[-1]).write_text(canonical_json(package), encoding="utf-8")
        return ""

    returned = collect_a3_remote_ranking_package(
        stage,
        launch,
        request,
        owner_local_output=destination,
        ssh_host="host.example",
        ssh_port=51007,
        ssh_key_path=key,
        known_hosts_path=known,
        run=return_runner,
    )
    assert validate_a3_transient_ranking_return_receipt(returned) == returned
    assert returned["rankings_embedded"] is False
    assert returned["owner_local_only"] is True
