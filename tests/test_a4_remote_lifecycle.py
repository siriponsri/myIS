from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a4_remote_launcher import (
    A4RemoteLauncherError,
    _connection,
    build_a4_checkpoint,
    build_a4_heartbeat,
    build_a4_launch_integrity_receipt,
    build_a4_stage_manifest,
    launch_a4_remote_operation,
    safe_return_a4_result,
    stage_a4_remote_runtime,
    stage_a4_remote_runtime_from_verified_seed,
    validate_a4_stage_manifest,
)
from myis_research.armindex.a4_remote_worker import (
    A4RemoteWorkerError,
    execute_a4_remote_worker,
    validate_a4_completion_receipt,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256


HASH = "a" * 64


def test_connection_quotes_windows_known_hosts_path(tmp_path: Path) -> None:
    known_hosts = tmp_path / "owner path" / "known_hosts"
    ssh, scp, _target = _connection("example.test", 22, tmp_path / "key", known_hosts)
    expected = f'UserKnownHostsFile="{known_hosts.resolve()}"'
    assert expected in ssh
    assert expected in scp
    assert "ServerAliveInterval=30" in ssh
    assert "ServerAliveCountMax=6" in scp


def _request(attempt: str) -> dict:
    body = {
        "schema_version": "myis.armindex-a4-remote-profile-request.v1",
        "attempt_id": attempt,
        "request_id": "a4-goal001-20260819T010203Z-abcd--fast",
        "profile_id": "FAST",
        "system_sha256": HASH,
        "profile_registry_sha256": HASH,
        "runtime_bindings_sha256": HASH,
        "hdev_scope_sha256": HASH,
        "arm_ids": ["ARM-01"],
        "candidate_depth": 100,
        "mode": "synchronous",
        "license_scope": "commercial_capable",
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def _write_json(path: Path, value: dict) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def test_worker_returns_aggregate_safe_completion(tmp_path: Path) -> None:
    attempt = "a4-goal001-20260819T010203Z-abcd"
    assets = tmp_path / "assets"
    assets.mkdir()
    marker = assets / "marker.txt"
    marker.write_text("opaque", encoding="ascii")
    inventory_body = {
        "schema_version": "myis.armindex-a4-runtime-assets-inventory.v1",
        "attempt_id": attempt,
        "asset_sha256s": {"marker.txt": file_sha256(marker)},
        "profile_registry_sha256": HASH,
        "protected_payload_included": False,
    }
    _write_json(assets / "A4_RUNTIME_ASSETS.json", {**inventory_body, "inventory_sha256": canonical_sha256(inventory_body)})
    request_path = tmp_path / "request.json"
    _write_json(request_path, _request(attempt))
    raw = {
        "rankings": {f"opaque-{i}": [{"family_token": f"fam-{j}", "rank": j + 1, "score": 1.0} for j in range(100)] for i in range(100)},
        "coverage": {"expected_units": 100, "completed_units": 100},
        "latency": {"wall_seconds": 1.0, "search_p50_seconds": 0.01, "search_p95_seconds": 0.02, "search_p99_seconds": 0.03},
        "resource": {"gpu_ids": [0], "mode": "synchronous"},
    }

    def fake_runner(arguments: list[str]) -> None:
        _write_json(Path(arguments[arguments.index("--result") + 1]), raw)

    completion = execute_a4_remote_worker(request_path, assets_root=assets, output_root=tmp_path / "out", ranker_runner=fake_runner)
    assert validate_a4_completion_receipt(completion)["status"] == "PASS_A4_REMOTE_RETRIEVAL_READY_FOR_OWNER_EVALUATION"
    assert (tmp_path / "out" / "ranking-package.json").is_file()
    assert not (tmp_path / "out" / ".ranker-result.json").exists()


def test_worker_rejects_protected_output(tmp_path: Path) -> None:
    attempt = "a4-goal001-20260819T010203Z-abcd"
    assets = tmp_path / "assets"
    assets.mkdir()
    marker = assets / "marker.txt"
    marker.write_text("opaque", encoding="ascii")
    body = {"schema_version": "myis.armindex-a4-runtime-assets-inventory.v1", "attempt_id": attempt, "asset_sha256s": {"marker.txt": file_sha256(marker)}, "profile_registry_sha256": HASH, "protected_payload_included": False}
    _write_json(assets / "A4_RUNTIME_ASSETS.json", {**body, "inventory_sha256": canonical_sha256(body)})
    request_path = tmp_path / "request.json"
    _write_json(request_path, _request(attempt))

    def fake_runner(arguments: list[str]) -> None:
        _write_json(Path(arguments[arguments.index("--result") + 1]), {"rankings": {}, "coverage": {"expected_units": 100, "completed_units": 100}, "latency": {}, "resource": {"qrels": "leak"}})

    with pytest.raises(A4RemoteWorkerError):
        execute_a4_remote_worker(request_path, assets_root=assets, output_root=tmp_path / "out", ranker_runner=fake_runner)


def test_launcher_contracts_and_safe_return(tmp_path: Path) -> None:
    attempt = "a4-goal001-20260819T010203Z-abcd"
    root = f"/opt/myis/{attempt}"
    manifest = build_a4_stage_manifest(attempt_id=attempt, remote_root=root, runtime_bindings_sha256=HASH, profile_registry_sha256=HASH, code_bundle_sha256=HASH, runtime_assets_archive_sha256=HASH, runtime_assets_inventory_sha256=HASH, remote_asset_sha256s={"corpus": HASH})
    assert validate_a4_stage_manifest(manifest)["status"] == "READY_A4_ISOLATED_REMOTE_STAGE"
    request_path = tmp_path / "request.json"
    _write_json(request_path, _request(attempt))
    stage_body = {"schema_version": "myis.armindex-a4-remote-stage-receipt.v1", "status": "PASS_A4_REMOTE_RUNTIME_STAGED", "attempt_id": attempt, "remote_root": root, "stage_manifest_sha256": manifest["stage_manifest_sha256"], "code_bundle_sha256": HASH, "runtime_assets_archive_sha256": HASH, "runtime_assets_inventory_sha256": HASH, "protected_payload_included": False, "selection_accesses": 0, "final_accesses": 0}
    stage = {**stage_body, "receipt_sha256": canonical_sha256(stage_body)}
    integrity = build_a4_launch_integrity_receipt(attempt_id=attempt, stage_receipt_sha256=stage["receipt_sha256"], request_sha256=json.loads(request_path.read_text())["request_sha256"], code_bundle_sha256=HASH, runtime_bindings_sha256=HASH)
    calls: list[list[str]] = []

    def fake_run(arguments: list[str]) -> str:
        calls.append(arguments)
        return "54321\n"

    launch = launch_a4_remote_operation(stage, integrity, request_path=request_path, ssh_host="example.test", ssh_port=22, ssh_key_path=tmp_path / "key", known_hosts_path=tmp_path / "known", run=fake_run)
    assert launch["remote_root"] == root
    completion_body = {"schema_version": "myis.armindex-a4-remote-completion-receipt.v1", "status": "PASS_A4_REMOTE_RETRIEVAL_READY_FOR_OWNER_EVALUATION", "attempt_id": attempt, "request_sha256": json.loads(request_path.read_text())["request_sha256"], "ranking_sha256": HASH, "coverage": {"expected_units": 100, "completed_units": 100}, "latency": {}, "qrels_opened": False, "membership_opened": False, "protected_payload_included": False, "ranking_embedded": False}
    completion = {**completion_body, "receipt_sha256": canonical_sha256(completion_body)}
    completion_path = tmp_path / "completion.json"
    _write_json(completion_path, completion)
    returned = safe_return_a4_result(launch_receipt=launch, completion_path=completion_path, owner_output_path=tmp_path / "owner" / "completion.json")
    assert returned["owner_local_only"] is True
    assert len(calls) == 3
    assert "test ! -e" in " ".join(calls[0])
    assert build_a4_heartbeat(attempt_id=attempt, operation_id=launch["operation_id"], remote_pid="54321", completed_units=10)["completed_units"] == 10
    assert build_a4_checkpoint(attempt_id=attempt, operation_id=launch["operation_id"], completed_units=100, request_sha256=HASH)["expected_units"] == 100


def test_stage_rejects_attempt_root_reuse() -> None:
    with pytest.raises(A4RemoteLauncherError):
        build_a4_stage_manifest(attempt_id="a4-goal001-20260819T010203Z-abcd", remote_root="/opt/myis/a3-goal003-20260819T010203Z-abcd", runtime_bindings_sha256=HASH, profile_registry_sha256=HASH, code_bundle_sha256=HASH, runtime_assets_archive_sha256=HASH, runtime_assets_inventory_sha256=HASH, remote_asset_sha256s={"corpus": HASH})


def test_fresh_stage_copies_bound_runtime_metadata(tmp_path: Path) -> None:
    attempt = "a4-goal001-20260819T010203Z-abcd"
    root = f"/opt/myis/{attempt}"
    code = tmp_path / "code.tar.gz"
    archive = tmp_path / "assets.tar.gz"
    inventory = tmp_path / "A4_RUNTIME_ASSETS.json"
    code.write_bytes(b"code")
    archive.write_bytes(b"assets")
    inventory.write_text("{}", encoding="ascii")
    runtime_body = {"schema_version": "myis.armindex-a4-runtime-bindings.v1", "attempt_id": attempt}
    runtime = {**runtime_body, "runtime_bindings_sha256": canonical_sha256(runtime_body)}
    registry_body = {"schema_version": "myis.armindex-a4-profile-registry.v1", "attempt_id": attempt}
    registry = {**registry_body, "registry_sha256": canonical_sha256(registry_body)}
    runtime_path = tmp_path / "A4_RUNTIME_BINDINGS.json"
    registry_path = tmp_path / "profile-registry.json"
    _write_json(runtime_path, runtime)
    _write_json(registry_path, registry)
    manifest = build_a4_stage_manifest(
        attempt_id=attempt,
        remote_root=root,
        runtime_bindings_sha256=runtime["runtime_bindings_sha256"],
        profile_registry_sha256=registry["registry_sha256"],
        code_bundle_sha256=file_sha256(code),
        runtime_assets_archive_sha256=file_sha256(archive),
        runtime_assets_inventory_sha256=file_sha256(inventory),
        remote_asset_sha256s={"assets": HASH},
    )
    calls: list[list[str]] = []

    def fake_run(arguments: list[str]) -> str:
        calls.append(arguments)
        return ""

    staged = stage_a4_remote_runtime(
        manifest,
        code_bundle=code,
        runtime_assets_archive=archive,
        runtime_assets_inventory=inventory,
        runtime_bindings=runtime_path,
        profile_registry=registry_path,
        ssh_host="example.test",
        ssh_port=22,
        ssh_key_path=tmp_path / "key",
        known_hosts_path=tmp_path / "known",
        run=fake_run,
    )
    assert staged["status"] == "PASS_A4_REMOTE_RUNTIME_STAGED"
    copied = "\n".join(" ".join(command) for command in calls)
    assert "A4_RUNTIME_BINDINGS.json" in copied
    assert "profile-registry.json" in copied


def test_verified_a4_seed_stage_never_reuses_worker_or_output(tmp_path: Path) -> None:
    attempt = "a4-goal001-20260819T010203Z-abcd"
    root = f"/opt/myis/{attempt}"
    code = tmp_path / "code.tar.gz"
    code.write_bytes(b"code")
    scope_body = {
        "schema_version": "myis.armindex-a4-harness-dev-scope.v1",
        "scope": "HARNESS-DEV",
        "query_count": 100,
    }
    scope = {**scope_body, "scope_sha256": canonical_sha256(scope_body)}
    inventory_body = {
        "schema_version": "myis.armindex-a4-runtime-assets-inventory.v1",
        "attempt_id": attempt,
        "asset_sha256s": {"opaque.txt": HASH},
        "hdev_scope_sha256": scope["scope_sha256"],
        "profile_registry_sha256": HASH,
        "protected_payload_included": False,
    }
    inventory = {**inventory_body, "inventory_sha256": canonical_sha256(inventory_body)}
    registry_body = {"schema_version": "myis.armindex-a4-profile-registry.v1", "attempt_id": attempt}
    registry = {**registry_body, "registry_sha256": canonical_sha256(registry_body)}
    inventory["profile_registry_sha256"] = registry["registry_sha256"]
    inventory_body["profile_registry_sha256"] = registry["registry_sha256"]
    inventory["inventory_sha256"] = canonical_sha256(inventory_body)
    runtime_body = {
        "schema_version": "myis.armindex-a4-runtime-bindings.v1",
        "attempt_id": attempt,
        "asset_inventory_sha256": inventory["inventory_sha256"],
        "hdev_scope_sha256": scope["scope_sha256"],
    }
    runtime = {**runtime_body, "runtime_bindings_sha256": canonical_sha256(runtime_body)}
    paths = {
        "runtime": tmp_path / "runtime.json",
        "registry": tmp_path / "registry.json",
        "scope": tmp_path / "scope.json",
        "inventory": tmp_path / "inventory.json",
    }
    _write_json(paths["runtime"], runtime)
    _write_json(paths["registry"], registry)
    _write_json(paths["scope"], scope)
    _write_json(paths["inventory"], inventory)
    manifest = build_a4_stage_manifest(
        attempt_id=attempt,
        remote_root=root,
        runtime_bindings_sha256=runtime["runtime_bindings_sha256"],
        profile_registry_sha256=registry["registry_sha256"],
        code_bundle_sha256=file_sha256(code),
        runtime_assets_archive_sha256=HASH,
        runtime_assets_inventory_sha256=inventory["inventory_sha256"],
        remote_asset_sha256s={"asset_inventory": inventory["inventory_sha256"]},
    )
    calls: list[list[str]] = []

    def fake_run(arguments: list[str]) -> str:
        calls.append(arguments)
        return ""

    staged = stage_a4_remote_runtime_from_verified_seed(
        manifest,
        code_bundle=code,
        runtime_bindings=paths["runtime"],
        profile_registry=paths["registry"],
        hdev_scope=paths["scope"],
        runtime_assets_inventory=paths["inventory"],
        seed_root="/opt/myis/a4-goal001-20260818T235614Z-a4x1",
        ssh_host="example.test",
        ssh_port=22,
        ssh_key_path=tmp_path / "key",
        known_hosts_path=tmp_path / "known",
        run=fake_run,
    )
    assert staged["stage_receipt"]["status"] == "PASS_A4_REMOTE_RUNTIME_STAGED"
    assert staged["seed_receipt"]["reused_output"] is False
    assert staged["seed_receipt"]["reused_worker"] is False
    assert any("cp -a --reflink=auto" in " ".join(command) for command in calls)
