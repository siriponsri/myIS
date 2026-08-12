from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.armindex import official_codex_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "control/armindex/a2/official-codex-bridge.v1.json"
SCHEMA_ROOT = ROOT / "schemas/armindex/official-codex"


def _load_config(tmp_path: Path) -> bridge.BridgeConfig:
    return bridge.load_bridge_config(
        ROOT,
        config_path=CONFIG,
        event_root=tmp_path / "owner-events",
    )


def _engineering_request(request_id: str = "a2-smoke-0001") -> dict[str, object]:
    return {
        "schema_version": "myis.armindex-engineering-refactor-review-request.v1",
        "request_id": request_id,
        "failure_summary": "A synthetic schema fixture rejects one valid field order.",
        "allowed_files": [
            "src/myis_research/armindex/official_codex_bridge.py",
            "tests/test_armindex_official_codex_bridge.py",
        ],
        "frozen_scientific_semantics": [
            "candidate universe remains 40 matched plus 12 dormant reserve",
            "ARM-01 and ARM-02 remain diagnostic non-advancing",
        ],
        "contains_metrics": False,
        "contains_outcomes": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _engineering_response(request_id: str = "a2-smoke-0001") -> dict[str, object]:
    return {
        "schema_version": "myis.armindex-engineering-refactor-review-response.v1",
        "request_id": request_id,
        "verdict": "accept",
        "diagnosis": "The fixture should validate the field order before hashing.",
        "required_engineering_changes": [
            "Move the deterministic field-order validation before hash comparison."
        ],
        "forbidden_scientific_changes": [
            "Do not change candidate payloads, evaluator bindings, or advancement semantics."
        ],
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _mock_worker_response(request_id: str = "a2-smoke-0001") -> dict[str, object]:
    return {
        "schema_version": "myis.armindex-official-codex-worker-response.v1",
        "request_id": request_id,
        "operation": "engineering_refactor_review",
        "result": _engineering_response(request_id),
        "identity": {
            "sdk_version": bridge.SDK_VERSION,
            "runtime_user_agent": "codex_cli_rs/0.144.4",
            "cli_version": "0.144.4",
            "model": bridge.MODEL,
            "model_provider": "openai",
            "reasoning_effort": bridge.REASONING_EFFORT,
        },
        "usage": None,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _assert_openai_schema_shape(schema: dict[str, object]) -> None:
    definitions = schema.get("$defs", {})

    def walk(node: object, path: str, *, root: bool = False) -> None:
        assert isinstance(node, dict), path
        assert any(key in node for key in ("type", "$ref", "anyOf")), path
        if root:
            assert node.get("type") == "object"
            assert "anyOf" not in node
        if "$ref" in node:
            ref = node["$ref"]
            assert isinstance(ref, str) and ref.startswith("#/$defs/")
            assert ref.removeprefix("#/$defs/") in definitions
        if "anyOf" in node:
            for index, branch in enumerate(node["anyOf"]):
                walk(branch, f"{path}.anyOf[{index}]")
        declared = node.get("type")
        declared_types = {declared} if isinstance(declared, str) else set(declared or [])
        properties = node.get("properties")
        if "object" in declared_types:
            assert isinstance(properties, dict), path
            assert node.get("additionalProperties") is False, path
            assert set(node.get("required", [])) == set(properties), path
        if isinstance(properties, dict):
            for name, child in properties.items():
                walk(child, f"{path}.properties.{name}")
        if "array" in declared_types:
            walk(node["items"], f"{path}.items")
        nested = node.get("$defs")
        if isinstance(nested, dict):
            for name, child in nested.items():
                walk(child, f"{path}.$defs.{name}")

    walk(schema, "$", root=True)


def test_bridge_config_is_hash_bound_loopback_and_exact_allowlist(tmp_path: Path) -> None:
    config = _load_config(tmp_path)
    preflight = bridge.validate_bridge_preflight(config)

    assert preflight["host"] == "127.0.0.1"
    assert preflight["sdk_version"] == "0.144.4"
    assert preflight["model"] == "gpt-5.6-sol"
    assert preflight["reasoning_effort"] == "high"
    assert tuple(config.operations) == bridge.OPERATION_NAMES
    assert config.official_home != config.maxplus_home
    assert config.event_root.is_relative_to(tmp_path)


def test_operation_schemas_are_strict_and_structured_output_compatible() -> None:
    paths = sorted(SCHEMA_ROOT.glob("*.json"))
    assert len(paths) == 6
    for path in paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _assert_openai_schema_shape(schema)
        assert schema["additionalProperties"] is False
        if ".response." in path.name:
            assert "uniqueItems" not in path.read_text(encoding="utf-8")


def test_child_environment_is_explicit_and_does_not_mutate_parent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("BRIDGE_TEST_SECRET", "must-not-pass")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-pass")
    before = dict(os.environ)

    child = bridge.build_child_environment(tmp_path / ".codex-official")

    assert dict(os.environ) == before
    assert child["CODEX_HOME"].endswith(".codex-official")
    assert "BRIDGE_TEST_SECRET" not in child
    assert "OPENAI_API_KEY" not in child
    assert "MYIS_STORE" not in child
    assert set(child) <= set(bridge._SAFE_ENVIRONMENT_KEYS) | {
        "CODEX_HOME",
        "HOME",
        "NO_COLOR",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
    }


def test_mocked_operation_validates_both_sides_and_appends_safe_event(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _load_config(tmp_path)

    def fake_worker(
        _config: bridge.BridgeConfig, worker_input: dict[str, object]
    ) -> tuple[dict[str, object], bytes, bytes, int]:
        assert worker_input["model"] == bridge.MODEL
        assert worker_input["reasoning_effort"] == bridge.REASONING_EFFORT
        raw = _mock_worker_response(str(worker_input["request_id"]))
        encoded = (json.dumps(raw) + "\n").encode("utf-8")
        return raw, encoded, b"", 0

    monkeypatch.setattr(bridge, "_run_worker", fake_worker)
    parent_home = os.environ.get("CODEX_HOME")
    result = bridge.invoke_operation(
        config, "engineering_refactor_review", _engineering_request()
    )

    assert os.environ.get("CODEX_HOME") == parent_home
    assert result["status"] == "accepted"
    assert result["identity"]["model_provider"] == "openai"
    event_lines = (config.event_root / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(event_lines) == 1
    event = json.loads(event_lines[0])
    assert event["protected_data_accessed"] is False
    assert event["measured_execution_performed"] is False
    assert "failure_summary" not in event
    assert "required_engineering_changes" not in event


def test_operation_retries_worker_failure_without_scientific_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = replace(_load_config(tmp_path), max_retries=1)
    calls = 0

    def flaky_worker(
        _config: bridge.BridgeConfig, worker_input: dict[str, object]
    ) -> tuple[dict[str, object], bytes, bytes, int]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise bridge.OfficialCodexBridgeError("synthetic worker failure")
        raw = _mock_worker_response(str(worker_input["request_id"]))
        return raw, (json.dumps(raw) + "\n").encode(), b"", 0

    monkeypatch.setattr(bridge, "_run_worker", flaky_worker)
    result = bridge.invoke_operation(
        config, "engineering_refactor_review", _engineering_request("a2-retry-0001")
    )

    assert calls == 2
    assert result["retry_count"] == 1
    events = [
        json.loads(line)
        for line in (config.event_root / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["verdict"] for event in events] == ["retry", "accepted"]


def test_worker_failure_exposes_only_sanitized_error_type(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _load_config(tmp_path)

    def failed_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["worker"],
            returncode=70,
            stdout="",
            stderr="CodexAppServerError\n",
        )

    monkeypatch.setattr(bridge.subprocess, "run", failed_run)

    with pytest.raises(
        bridge.OfficialCodexBridgeError,
        match=r"exit 70: CodexAppServerError$",
    ):
        bridge._run_worker(
            config,
            {
                "request_id": "a2-worker-error-0001",
                "operation": "engineering_refactor_review",
            },
        )


def test_credit_snapshot_is_model_bound_sanitized_and_write_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _load_config(tmp_path)
    worker_snapshot = {
        "schema_version": bridge.CREDIT_SNAPSHOT_SCHEMA_VERSION,
        "checkpoint_id": "a2-credit-check-0001",
        "observed_at_utc": "2026-08-12T00:00:00Z",
        "model_name": "gpt-5.6-sol",
        "sdk_version": "0.144.4",
        "plan_type": "plus",
        "primary": {
            "used_percent": 10,
            "remaining_percent": 90,
            "window_duration_mins": 10080,
            "resets_at": 1787013939,
            "resets_at_utc": "2026-08-18T00:45:39Z",
        },
        "rate_limit_reached_type": None,
        "credits": {"has_credits": False, "unlimited": False},
        "reset_credit_available_count": 1,
        "limit_reached": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }

    def successful_run(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["credit-worker"],
            returncode=0,
            stdout=json.dumps(worker_snapshot),
            stderr="",
        )

    monkeypatch.setattr(bridge.subprocess, "run", successful_run)
    result = bridge.capture_official_credit_snapshot(
        config, "a2-credit-check-0001"
    )

    assert result["model_name"] == "gpt-5.6-sol"
    assert result["plan_type"] == "plus"
    assert result["primary"]["remaining_percent"] == 90
    assert result["primary"]["resets_at_utc"] == "2026-08-18T00:45:39Z"
    stored = json.loads(
        (
            config.event_root
            / "credit-snapshots"
            / "a2-credit-check-0001.json"
        ).read_text(encoding="ascii")
    )
    assert "balance" not in json.dumps(stored)
    assert "account" not in json.dumps(stored)
    assert "email" not in json.dumps(stored)
    with pytest.raises(bridge.OfficialCodexBridgeError, match="already exists"):
        bridge.capture_official_credit_snapshot(config, "a2-credit-check-0001")


def test_credit_snapshot_fails_closed_at_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _load_config(tmp_path)
    exhausted = {
        "schema_version": bridge.CREDIT_SNAPSHOT_SCHEMA_VERSION,
        "checkpoint_id": "a2-credit-limited-0001",
        "observed_at_utc": "2026-08-12T00:00:00Z",
        "model_name": "gpt-5.6-sol",
        "sdk_version": "0.144.4",
        "plan_type": "plus",
        "primary": {
            "used_percent": 100,
            "remaining_percent": 0,
            "window_duration_mins": 10080,
            "resets_at": 1787013939,
            "resets_at_utc": "2026-08-18T00:45:39Z",
        },
        "rate_limit_reached_type": "rate_limit_reached",
        "credits": {"has_credits": False, "unlimited": False},
        "reset_credit_available_count": 1,
        "limit_reached": True,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }
    monkeypatch.setattr(
        bridge.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=["credit-worker"],
            returncode=0,
            stdout=json.dumps(exhausted),
            stderr="",
        ),
    )

    with pytest.raises(bridge.OfficialCodexBridgeError, match="exhausted"):
        bridge.capture_official_credit_snapshot(config, "a2-credit-limited-0001")


def test_freeze_lock_rejects_scientific_operations(tmp_path: Path) -> None:
    lock = tmp_path / "candidate-freeze.lock.v1.json"
    lock.write_text("{}\n", encoding="utf-8")
    config = replace(_load_config(tmp_path), freeze_lock=lock)

    with pytest.raises(bridge.OfficialCodexBridgeError, match="locked after candidate freeze"):
        bridge.invoke_operation(
            config,
            "representation_propose",
            {"request_id": "a2-locked-0001"},
        )


def test_server_rejects_non_loopback_bind(tmp_path: Path) -> None:
    config = _load_config(tmp_path)
    with pytest.raises(bridge.OfficialCodexBridgeError, match="must be loopback"):
        bridge.OfficialCodexHTTPServer(("0.0.0.0", 0), config)


def test_what_if_uses_installed_sdk_without_official_call(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "myis_research.armindex.official_codex_bridge",
            "what-if",
            "--repository-root",
            str(ROOT),
            "--event-root",
            str(tmp_path / "events"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "PASS_OFFICIAL_CODEX_BRIDGE_PREFLIGHT"
    assert payload["protected_data_accessed"] is False
    assert payload["measured_execution_performed"] is False
    assert payload["parent_environment_mutated"] is False
