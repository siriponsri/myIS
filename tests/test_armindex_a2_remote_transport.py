from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from myis_research.armindex.a2_remote_transport import (
    A2RemoteTransportError,
    RemoteExecutor,
    RemoteTransportConfig,
    build_remote_validation_command,
    build_transport_request,
    validate_remote_transport_result,
    validate_transport_adoption_binding,
    validate_transport_request,
)
from myis_research.kernel.canonical import canonical_sha256

ATTEMPT = "a2-remote-test01"


def _config(tmp_path: Path) -> RemoteTransportConfig:
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("private owner-local fixture\n", encoding="ascii")
    known.write_text("pinned host fixture\n", encoding="ascii")
    return RemoteTransportConfig(
        provider_instance_id="47700074",
        host="127.0.0.1",
        port=10355,
        user="root",
        key_path=key,
        known_hosts_path=known,
        remote_root="/opt/myis/a2-remote-test01",
        remote_repository_root="/opt/myis/a2-remote-test01/current",
        remote_owner_root="/opt/myis/a2-remote-test01/owner-input",
        remote_input_manifest="/opt/myis/a2-remote-test01/owner-input/input.json",
        remote_bundle_path="/opt/myis/a2-remote-test01/incoming/bundle.tar.gz",
        remote_bundle_receipt_path=(
            "/opt/myis/a2-remote-test01/incoming/bundle.receipt.json"
        ),
        remote_python_executable="/opt/myis/a2-remote-test01/venv/bin/python",
        bundle_sha256="1" * 64,
        bundle_receipt_sha256="2" * 64,
        bundle_receipt_file_sha256="8" * 64,
        git_commit="3" * 40,
        git_tree="4" * 40,
        measurement_authority_commitment_uri=(
            "control/armindex/a2/measurement-authority-commitment.v1.json"
        ),
        measurement_authority_commitment_file_sha256="5" * 64,
        owner_manifest_sha256="6" * 64,
        remote_input_manifest_sha256="7" * 64,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider_instance_id", "47700075"),
        ("remote_repository_root", "/opt/myis/other/current"),
        ("bundle_sha256", "invalid"),
    ],
)
def test_remote_transport_config_rejects_identity_drift(
    tmp_path: Path, field: str, value: object
) -> None:
    values = dict(_config(tmp_path).__dict__)
    values[field] = value
    with pytest.raises(A2RemoteTransportError):
        RemoteTransportConfig(**values)


def test_remote_transport_request_is_exactly_hash_bound(tmp_path: Path) -> None:
    config = _config(tmp_path)
    request = build_transport_request(config, attempt_id=ATTEMPT)
    assert validate_transport_request(request, config, attempt_id=ATTEMPT) == request
    drifted = copy.deepcopy(request)
    drifted["owner_manifest_sha256"] = "0" * 64
    with pytest.raises(A2RemoteTransportError, match="binding drift"):
        validate_transport_request(drifted, config, attempt_id=ATTEMPT)


def test_successor_transport_uses_new_commitment_and_allows_fresh_instance(
    tmp_path: Path,
) -> None:
    base = _config(tmp_path)
    config = RemoteTransportConfig(
        **{
            **base.__dict__,
            "provider_instance_id": "47700075",
            "measurement_authority_commitment_uri": (
                "control/armindex/a2/measurement-authority-commitment.v2.json"
            ),
        }
    )
    request = build_transport_request(config, attempt_id=ATTEMPT)
    assert request["schema_version"] == "myis.armindex-a2-remote-measured-transport.v3"
    assert request["request_id"].endswith("-v3")


def test_remote_transport_must_equal_execution_adoption(tmp_path: Path) -> None:
    config = _config(tmp_path)
    adoption = {
        "attempt_id": ATTEMPT,
        "bundle_sha256": config.bundle_sha256,
        "bundle_receipt_sha256": config.bundle_receipt_sha256,
        "git_commit": config.git_commit,
        "git_tree": config.git_tree,
        "remote_root": config.remote_root,
    }
    validate_transport_adoption_binding(
        config, attempt_id=ATTEMPT, adoption_receipt=adoption
    )
    adoption["bundle_sha256"] = "0" * 64
    with pytest.raises(A2RemoteTransportError, match="execution adoption"):
        validate_transport_adoption_binding(
            config, attempt_id=ATTEMPT, adoption_receipt=adoption
        )


def test_remote_validation_binds_attempt_owner_manifest_and_retriever(
    tmp_path: Path,
) -> None:
    command = build_remote_validation_command(_config(tmp_path), attempt_id=ATTEMPT)

    assert "remote_input.get('attempt_id')==request['attempt_id']" in command
    assert (
        "remote_input.get('owner_manifest_sha256')==request['owner_manifest_sha256']"
        in command
    )
    assert "a2_remote_retriever.py" in command
    assert "pathlib.Path('/proc').glob('[0-9]*/cmdline')" in command
    assert "module.startswith('myis_research.armindex.a2_')" in command


def test_remote_executor_maps_paths_and_binds_candidate_environment(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config = RemoteTransportConfig(
        **{
            **config.__dict__,
            "local_repository_root": "C:\\research",
            "local_owner_root": "C:\\owner",
            "local_python_executable": "C:\\python.exe",
        }
    )
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, json.dumps({"status": "PASS"}), "")

    executor = RemoteExecutor(config=config, attempt_id=ATTEMPT, runner=runner)
    result = executor(
        ["C:\\python.exe", "C:\\research\\program.json", "C:\\owner\\input.json"],
        environment={
            "PATH": "local-only",
            "MYIS_A2_CANDIDATE_ID": "a2-arm-03-matched-b1-exploit",
            "MYIS_A2_ARM_ID": "ARM-03",
            "MYIS_A2_PROGRAM_SHA256": "a" * 64,
            "HF_HUB_OFFLINE": "1",
        },
        heartbeat_path=tmp_path / "heartbeat",
        process_path=tmp_path / "process",
        timeout_seconds=60,
    )
    assert result == {"status": "PASS"}
    remote_command = calls[0][-1]
    assert f"PYTHONPATH={config.remote_repository_root}/src" in remote_command
    assert "MYIS_A2_CANDIDATE_ID=a2-arm-03-matched-b1-exploit" in remote_command
    assert "local-only" not in remote_command
    assert config.remote_python_executable in remote_command
    assert config.remote_repository_root in remote_command
    assert config.remote_input_manifest in remote_command
    assert "myis_research.armindex.a2_remote_candidate" in remote_command
    assert config.remote_bundle_receipt_path in remote_command
    assert config.bundle_receipt_file_sha256 in remote_command
    assert config.remote_input_manifest_sha256 in remote_command
    assert config.owner_manifest_sha256 in remote_command
    assert (tmp_path / "heartbeat").is_file()
    assert (tmp_path / "process").is_file()
    process = json.loads((tmp_path / "process").read_text(encoding="ascii"))
    assert process["status"] == "REMOTE_REAPED_WITH_DURABLE_RESULT"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate_evaluation_started", True),
        ("rep_dev_measurement_started", True),
        ("protected_payload_returned", True),
        ("gpu_compute_process_count", 1),
        ("a2_process_count", 1),
    ],
)
def test_remote_transport_result_rejects_measured_boundary_or_live_worker(
    tmp_path: Path, field: str, value: object
) -> None:
    config = _config(tmp_path)
    body = {
        "schema_version": "myis.armindex-a2-remote-transport-check.v1",
        "status": "PASS_A2_REMOTE_TRANSPORT_CHECK",
        "attempt_id": ATTEMPT,
        "provider_instance_id": config.provider_instance_id,
        "bundle_sha256": config.bundle_sha256,
        "git_commit": config.git_commit,
        "git_tree": config.git_tree,
        "gpu_compute_process_count": 0,
        "a2_process_count": 0,
        "candidate_evaluation_started": False,
        "rep_dev_measurement_started": False,
        "protected_payload_returned": False,
    }
    body[field] = value
    result = {**body, "receipt_sha256": canonical_sha256(body)}
    with pytest.raises(A2RemoteTransportError):
        validate_remote_transport_result(result, config, attempt_id=ATTEMPT)
