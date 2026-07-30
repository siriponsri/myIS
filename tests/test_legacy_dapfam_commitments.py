from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from myis_research.legacy_dapfam import (
    assert_legacy_p1_request_current,
    build_legacy_p1_request,
    build_request_scope,
    current_git_commit,
    discover_legacy,
)
from myis_research.legacy_dapfam_cli import main as console_main
from myis_research.kernel.canonical import file_sha256
from myis_research.owner_local import validate_request


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _certifier_main():
    spec = importlib.util.spec_from_file_location("legacy_dapfam_certify_test", REPOSITORY_ROOT / "scripts" / "legacy_dapfam_certify.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def _write_legacy_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root = tmp_path / "is1-projects"
    legacy_root = project_root / "shared" / "data"
    query_path = legacy_root / "processed" / "dapfam" / "queries.jsonl"
    query_path.parent.mkdir(parents=True)
    query_path.write_text(
        "\n".join(
            json.dumps({"query_id": value, "text": "synthetic fixture"})
            for value in ("fixture-query-a", "fixture-query-b", "fixture-query-c")
        ) + "\n",
        encoding="utf-8",
    )
    split_path = project_root / "paper-d" / "config" / "dev_test_split.json"
    split_path.parent.mkdir(parents=True)
    split_path.write_text(json.dumps({"test": ["paper-d-fixture-id"]}), encoding="utf-8")
    ids_path = legacy_root / "embeddings" / "dapfam" / "claim" / "ids_000000.jsonl"
    ids_path.parent.mkdir(parents=True)
    ids_path.write_text(json.dumps({"id": "protected-id-mapping"}) + "\n", encoding="utf-8")
    return legacy_root, query_path, split_path


def test_owner_local_split_commitments_are_hash_only_and_cover_paper_d(tmp_path: Path) -> None:
    legacy_root, query_path, split_path = _write_legacy_fixture(tmp_path)
    inventory = discover_legacy(legacy_root)
    scope = build_request_scope(legacy_root, inventory, REPOSITORY_ROOT)

    assert inventory["paper_d_copies"] == {
        "status": "present",
        "path": "paper-d",
        "file_count": 1,
        "bytes": split_path.stat().st_size,
        "protected_named_file_count": 1,
        "split_named_file_count": 1,
        "disposition": "historical-reference",
        "content_hashes": "owner_local_only",
    }
    assert inventory["root"] == "APP-DAPFAM-PROTECTED"
    assert str(legacy_root) not in json.dumps(inventory, sort_keys=True)
    assert all(asset["sha256"] is None for asset in inventory["assets"])
    assert "embeddings/dapfam/claim/ids_000000.jsonl" in inventory["protected_assets_owner_local_only"]
    assert set(scope) >= {
        "active_seed42_split_membership_sha256",
        "paper_d_split_membership_sha256",
        "legacy_adapter_code_sha256",
        "legacy_cli_code_sha256",
        "legacy_certifier_code_sha256",
        "owner_local_runner_code_sha256",
        "p1_evaluator_code_sha256",
        "campaign_sha256",
        "envelope_sha256",
        "request_schema_sha256",
        "receipt_schema_sha256",
    }
    assert all(len(value) == 64 for value in scope.values())
    assert scope["legacy_adapter_code_sha256"] == file_sha256(REPOSITORY_ROOT / "src" / "myis_research" / "legacy_dapfam.py")
    assert scope["legacy_cli_code_sha256"] == file_sha256(REPOSITORY_ROOT / "src" / "myis_research" / "legacy_dapfam_cli.py")
    assert scope["legacy_certifier_code_sha256"] == file_sha256(REPOSITORY_ROOT / "scripts" / "legacy_dapfam_certify.py")
    assert scope["campaign_sha256"] == file_sha256(REPOSITORY_ROOT / "control" / "campaigns" / "scope-autoindex-v1.yaml")
    assert scope["request_schema_sha256"] == file_sha256(REPOSITORY_ROOT / "control" / "owner-local" / "request.schema.json")
    rendered = json.dumps({"inventory": inventory, "scope": scope}, sort_keys=True)
    assert "fixture-query-a" not in rendered
    assert "paper-d-fixture-id" not in rendered

    query_path.write_text(json.dumps({"query_id": "different-fixture-query", "text": "synthetic fixture"}) + "\n", encoding="utf-8")
    changed_active = build_request_scope(legacy_root, discover_legacy(legacy_root), REPOSITORY_ROOT)
    assert changed_active["active_seed42_split_membership_sha256"] != scope["active_seed42_split_membership_sha256"]

    split_path.write_text(json.dumps({"test": ["different-paper-d-fixture-id"]}), encoding="utf-8")
    changed_historical = build_request_scope(legacy_root, discover_legacy(legacy_root), REPOSITORY_ROOT)
    assert changed_historical["paper_d_split_membership_sha256"] != changed_active["paper_d_split_membership_sha256"]


def test_certifier_binds_current_scope_and_never_writes_legacy_bytes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    legacy_root, query_path, split_path = _write_legacy_fixture(tmp_path)
    inventory_path = tmp_path / "inventory.json"
    request_path = tmp_path / "request.json"
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (query_path, split_path)}

    assert _certifier_main()([
        "--legacy-root", str(legacy_root),
        "--repository-root", str(REPOSITORY_ROOT),
        "--inventory-output", str(inventory_path),
        "--make-request", str(request_path),
    ]) == 0
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before} == before

    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["request_id"] == "legacy-dapfam-p1-cpu-s42-commitment-v2"
    assert request["git_commit"] == current_git_commit(REPOSITORY_ROOT)
    assert validate_request(request) == request
    assert_legacy_p1_request_current(request, legacy_root, REPOSITORY_ROOT)
    rendered = request_path.read_text(encoding="utf-8") + inventory_path.read_text(encoding="utf-8") + capsys.readouterr().out
    assert "fixture-query-a" not in rendered
    assert "paper-d-fixture-id" not in rendered

    request["scope"] = {"campaign_sha256": "0" * 64}
    with pytest.raises(ValueError, match="scope does not match current bindings"):
        assert_legacy_p1_request_current(request, legacy_root, REPOSITORY_ROOT)


def test_console_and_script_share_the_same_current_request_contract(tmp_path: Path) -> None:
    legacy_root, _, _ = _write_legacy_fixture(tmp_path)
    script_inventory = tmp_path / "script-inventory.json"
    script_request = tmp_path / "script-request.json"
    console_inventory = tmp_path / "console-inventory.json"
    console_request = tmp_path / "console-request.json"
    args = ["--legacy-root", str(legacy_root), "--repository-root", str(REPOSITORY_ROOT)]

    assert _certifier_main()([*args, "--inventory-output", str(script_inventory), "--make-request", str(script_request)]) == 0
    assert console_main([*args, "--inventory-output", str(console_inventory), "--make-request", str(console_request)]) == 0
    assert json.loads(script_inventory.read_text(encoding="utf-8")) == json.loads(console_inventory.read_text(encoding="utf-8"))
    assert json.loads(script_request.read_text(encoding="utf-8")) == json.loads(console_request.read_text(encoding="utf-8"))


def test_certifier_rejects_outputs_inside_the_repository_or_legacy_project(tmp_path: Path) -> None:
    legacy_root, _, _ = _write_legacy_fixture(tmp_path)
    with pytest.raises(ValueError, match="read-only legacy tree"):
        _certifier_main()([
            "--legacy-root", str(legacy_root),
            "--repository-root", str(REPOSITORY_ROOT),
            "--inventory-output", str(legacy_root / "forbidden-inventory.json"),
        ])
    with pytest.raises(ValueError, match="repository"):
        console_main([
            "--legacy-root", str(legacy_root),
            "--repository-root", str(REPOSITORY_ROOT),
            "--inventory-output", str(REPOSITORY_ROOT / "evidence" / "forbidden-inventory.json"),
        ])


def test_builder_returns_current_inventory_and_request(tmp_path: Path) -> None:
    legacy_root, _, _ = _write_legacy_fixture(tmp_path)
    inventory, request = build_legacy_p1_request(legacy_root, REPOSITORY_ROOT)
    assert inventory["root"] == "APP-DAPFAM-PROTECTED"
    assert_legacy_p1_request_current(request, legacy_root, REPOSITORY_ROOT)
