from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_runtime_minimal as runtime
from myis_research.kernel.canonical import file_sha256


ROOT = Path(__file__).resolve().parents[1]


def _fake_policy(directory: Path, *, arm_id: str = "ARM-02") -> dict[str, object]:
    lock_path = ROOT / "control/armindex/a1.2/model-locks" / f"{arm_id}.v1.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    paths = ["config.json", "pytorch_model.bin", "tokenizer.json"]
    critical = [
        {"path": path, "sha256": file_sha256(directory / path)}
        for path in ("pytorch_model.bin", "tokenizer.json")
    ]
    return {
        "schema_version": "myis.armindex-a1.2-runtime-minimal-policy.v4",
        "revision_id": runtime.REVISION_ID,
        "allowlist_version": "test.v1",
        "exclusion_policy": {"policy_id": "test"},
        "arms": [
            {
                "arm_id": arm_id,
                "model_id": lock["model_id"],
                "resolved_revision": lock["resolved_revision"],
                "source_lock_file_sha256": file_sha256(lock_path),
                "upstream_full_snapshot_bytes": 100,
                "runtime_minimal_expected_bytes": sum((directory / path).stat().st_size for path in paths),
                "allow_patterns": paths,
                "critical_artifacts": critical,
                "required_custom_code": [],
                "excluded_files": [{"path": "onnx/model.onnx", "reason": "alternate"}],
            }
        ],
    }


def _seed_runtime_files(directory: Path) -> None:
    (directory / "config.json").write_text("{}\n", encoding="utf-8")
    (directory / "pytorch_model.bin").write_bytes(b"frozen-test-weights")
    (directory / "tokenizer.json").write_text('{"test": true}\n', encoding="utf-8")


def test_policy_is_complete_for_the_exact_locks_and_excludes_alternates() -> None:
    policy = runtime.load_runtime_policy(ROOT)
    assert tuple(arm["arm_id"] for arm in policy["arms"]) == runtime.DENSE_ARMS
    assert sum(arm["upstream_full_snapshot_bytes"] for arm in policy["arms"]) == 13317159049
    assert sum(arm["runtime_minimal_expected_bytes"] for arm in policy["arms"]) == 6119853855
    for arm in policy["arms"]:
        allowed = arm["allow_patterns"]
        assert allowed == sorted(set(allowed))
        assert all("onnx" not in path.lower() for path in allowed)
        assert {item["path"] for item in arm["critical_artifacts"]}.issubset(allowed)
    arm02 = next(item for item in policy["arms"] if item["arm_id"] == "ARM-02")
    arm04 = next(item for item in policy["arms"] if item["arm_id"] == "ARM-04")
    assert len(arm02["excluded_files"]) == 18
    assert len(arm04["excluded_files"]) == 8


def test_snowflake_custom_code_is_required_and_bound_to_the_locked_git_oids() -> None:
    policy = runtime.load_runtime_policy(ROOT)
    arm04 = next(item for item in policy["arms"] if item["arm_id"] == "ARM-04")
    assert arm04["required_custom_code"] == [
        {"path": "configuration_hf_alibaba_nlp_gte.py", "git_oid": "d816ed663a58404f966fe322cd113ac39a957686"},
        {"path": "modeling_hf_alibaba_nlp_gte.py", "git_oid": "63c0975e09b5631b564170d2ecb7985c5d8dd189"},
    ]
    assert set(item["path"] for item in arm04["required_custom_code"]).issubset(arm04["allow_patterns"])


def test_runtime_manifest_is_deterministic_streamed_and_ignores_only_preserved_excluded_parts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_runtime_files(tmp_path)
    (tmp_path / "onnx").mkdir()
    (tmp_path / "onnx/model.onnx.part").write_bytes(b"unfinished-alternate")
    policy = _fake_policy(tmp_path)
    monkeypatch.setattr(runtime, "load_runtime_policy", lambda _root: policy)

    first = runtime.write_runtime_manifest(ROOT, "ARM-02", tmp_path)
    first_bytes = (tmp_path / "runtime-file-manifest.v4.json").read_bytes()
    second = runtime.write_runtime_manifest(ROOT, "ARM-02", tmp_path)
    assert first == second
    assert (tmp_path / "runtime-file-manifest.v4.json").read_bytes() == first_bytes
    result = runtime.validate_runtime_manifest(ROOT, "ARM-02", tmp_path)
    assert result["status"] == "PASS"
    assert result["file_count"] == 3
    assert result["dense_model_loaded"] is False


def test_runtime_manifest_fails_closed_on_a_critical_artifact_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_runtime_files(tmp_path)
    policy = _fake_policy(tmp_path)
    policy["arms"][0]["critical_artifacts"][0]["sha256"] = "0" * 64
    monkeypatch.setattr(runtime, "load_runtime_policy", lambda _root: policy)
    with pytest.raises(runtime.RuntimeMinimalError, match="critical artifact"):
        runtime.write_runtime_manifest(ROOT, "ARM-02", tmp_path)


def test_runtime_settings_have_no_network_fallback() -> None:
    assert runtime.validate_offline_runtime_settings(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "local_files_only": True,
            "network_model_download_allowed": False,
        }
    )["network_fallback"] is False
    with pytest.raises(runtime.RuntimeMinimalError, match="network fallback"):
        runtime.validate_offline_runtime_settings(
            {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "local_files_only": False,
                "network_model_download_allowed": False,
            }
        )


def test_v4_policy_contains_no_protected_or_credential_like_path() -> None:
    text = (ROOT / runtime.POLICY_PATH).read_text(encoding="utf-8").lower()
    for forbidden in ("qrels", "membership", "query_ids", "id_rsa", "id_ed25519", "openai_api_key"):
        assert forbidden not in text
