from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_vast import (
    CONTROL_ROOT,
    DENSE_ARMS,
    GPU_SLOT_BY_ARM,
    V1_BINDINGS,
    A12VastError,
    build_v2_files,
    quote_admission,
    remote_worker,
    validate_complete_sha256s,
    validate_live_preflight,
    validate_safe_export,
    validate_v2,
)
from myis_research.kernel.canonical import file_sha256


ROOT = Path(__file__).resolve().parents[1]


def _live_metadata() -> dict[str, object]:
    return {
        "git_commit": "a" * 40,
        "git_tree": "b" * 40,
        "image_digest": "sha256:" + "c" * 64,
        "gpus": [
            {"uuid": f"GPU-12345678-0000-0000-0000-00000000000{slot}", "model": "NVIDIA GeForce RTX 3090"}
            for slot in range(4)
        ],
        "cuda_available": True,
        "pytorch_cuda_compatible": True,
        "cpu_count": 16,
        "ram_gib": 64,
        "free_disk_gib": 250,
        "model_manifests_complete": True,
        "model_manifests_sha256": "d" * 64,
        "snowflake_remote_code_hashes_match": True,
        "snowflake_remote_code_sha256": "e" * 64,
        "dense_adapter_parity": True,
        "dense_adapter_parity_sha256": "f" * 64,
        "qwen_max_length_frozen": True,
        "qwen_measured_max_length": 8192,
        "qwen_max_length_sha256": "1" * 64,
        "protected_root_read_only": True,
        "protected_root_remote": False,
        "protected_root_probe_sha256": "2" * 64,
        "remote_forbidden_surface_absent": True,
        "return_path_writable": True,
        "return_path_free_gib": 50,
        "return_path_probe_sha256": "3" * 64,
        "provider_instance_id": "12345678",
        "quote_live": True,
        "provider_quote_sha256": "4" * 64,
        "hourly_instance_usd": 0.6,
        "estimated_instance_hours": 4,
        "heartbeat_fresh": True,
        "checkpoint_resume_passed": True,
        "heartbeat_resume_sha256": "5" * 64,
        "provider_destroy_dry_run_passed": True,
        "ttl_dry_run_passed": True,
        "watchdog_provider_instance_id": "12345678",
        "watchdog_dry_run_sha256": "6" * 64,
    }


def test_v1_contract_bytes_are_preserved() -> None:
    for relative, expected in V1_BINDINGS.items():
        assert file_sha256(ROOT / relative) == expected


def test_v2_contract_builder_keeps_launch_and_adoption_false() -> None:
    files = build_v2_files(ROOT)
    contract = json.loads(files[CONTROL_ROOT / "execution-contract.v2.json"])
    budget = json.loads(files[Path("control/budgets/a1.2-common-screen-vast-4x3090-v2.json")])
    runtime = json.loads(files[CONTROL_ROOT / "runtime-lock.v2.json"])
    image_contract = json.loads(files[CONTROL_ROOT / "image-digest-contract.v2.json"])
    assert contract["launch_allowed"] is False
    assert contract["adopted_for_execution"] is False
    assert set(contract["real_counters"].values()) == {0}
    assert set(contract["resource_counters"].values()) == {0}
    assert budget["planning_quote"]["hourly_instance_usd"] == 0.6
    assert budget["hard_stops"] == {
        "common_screen_usd": 18,
        "a1_total_usd": 23,
        "campaign_usd": 100,
    }
    assert runtime["cuda"] == "11.8"
    assert runtime["pytorch"] == "2.6.0+cu118"
    assert image_contract["built_image"]["docker_image_id_required"] is True
    dockerfile = (ROOT / "containers/a1_2_vast_4x3090/Dockerfile").read_text(encoding="utf-8")
    assert "--no-index" in dockerfile
    assert "sha256sum --check SHA256SUMS" in dockerfile
    assert "COPY bundle" not in dockerfile


def test_quote_admission_passes_owner_rate_and_blocks_overrun() -> None:
    assert quote_admission(hourly_instance_usd=0.6, estimated_instance_hours=4)["status"] == "PASS"
    blocked = quote_admission(hourly_instance_usd=0.6, estimated_instance_hours=31)
    assert blocked["status"] == "BLOCKED_BUDGET"
    assert blocked["fits_all_ceilings"] is False


def test_live_preflight_never_authorizes_launch_and_has_budget_terminal_state() -> None:
    passed = validate_live_preflight(_live_metadata())
    assert passed["status"] == "PASSED_PENDING_OWNER_ADOPTION"
    assert passed["launch_allowed"] is False
    assert passed["adopted_for_execution"] is False

    overrun = _live_metadata()
    overrun["estimated_instance_hours"] = 31
    blocked = validate_live_preflight(overrun)
    assert blocked["status"] == "BLOCKED_BUDGET"
    assert "budget" in blocked["blockers"]


def test_sha256sums_requires_complete_directory_coverage(tmp_path: Path) -> None:
    (tmp_path / "weights.bin").write_bytes(b"weights")
    (tmp_path / "tokenizer.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "SHA256SUMS").write_text(
        f"{file_sha256(tmp_path / 'weights.bin')}  weights.bin\n",
        encoding="utf-8",
    )
    with pytest.raises(A12VastError, match="coverage mismatch"):
        validate_complete_sha256s(tmp_path)
    (tmp_path / "SHA256SUMS").write_text(
        f"{file_sha256(tmp_path / 'tokenizer.json')}  tokenizer.json\n"
        f"{file_sha256(tmp_path / 'weights.bin')}  weights.bin\n",
        encoding="utf-8",
    )
    assert validate_complete_sha256s(tmp_path)["file_count"] == 2


def test_worker_writes_failure_then_resumes_from_checkpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    files = build_v2_files(ROOT)
    job_path = tmp_path / "ARM-02.json"
    job_path.write_text(files[CONTROL_ROOT / "jobs/v2/ARM-02.json"], encoding="utf-8")
    output = tmp_path / "output"
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    with pytest.raises(RuntimeError, match="injected"):
        remote_worker(job_path, output, fail_after_step=1)
    receipt = remote_worker(job_path, output)
    assert receipt["status"] == "synthetic_preflight_passed"
    assert receipt["resumed_from_checkpoint"] is True
    assert receipt["measured_execution"] is False
    assert (output / "failure-receipts/ARM-02.json").is_file()


def test_safe_export_rejects_unlisted_and_sensitive_names(tmp_path: Path) -> None:
    files = build_v2_files(ROOT)
    allowlist = tmp_path / "allowlist.json"
    allowlist.write_text(files[CONTROL_ROOT / "safe-export-allowlist.v2.json"], encoding="utf-8")
    output = tmp_path / "output"
    (output / "heartbeats").mkdir(parents=True)
    (output / "heartbeats/ARM-02.json").write_text("{}\n", encoding="utf-8")
    assert validate_safe_export(output, allowlist)["file_count"] == 1
    (output / "unexpected.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(A12VastError, match="outside the safe-export allowlist"):
        validate_safe_export(output, allowlist)


def test_fixed_four_arm_device_mapping_is_total_and_unique() -> None:
    assert tuple(GPU_SLOT_BY_ARM) == DENSE_ARMS
    assert set(GPU_SLOT_BY_ARM.values()) == {0, 1, 2, 3}


def test_materialized_v2_contracts_validate() -> None:
    validation = validate_v2(ROOT)
    assert validation.status == "prepared_launch_locked"
    assert validation.job_count == 4
    assert validation.launch_allowed is False


@pytest.mark.skipif(os.name != "nt", reason="PowerShell 5.1 coordinator test is Windows-specific")
def test_local_powershell_coordinator_and_watchdog_dry_runs(tmp_path: Path) -> None:
    key = tmp_path / "synthetic-key"
    key.write_text("synthetic-placeholder\n", encoding="utf-8")
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"synthetic-bundle")
    image_archive = tmp_path / "image.tar"
    image_archive.write_bytes(b"synthetic-image")
    collect = tmp_path / "collect"
    collect.mkdir()
    coordinator = ROOT / "scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1"
    common = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(coordinator),
            "-Action",
            "verify",
            "-HostName",
            "example.invalid",
            "-Port",
            "22",
            "-UserName",
            "root",
            "-KeyPath",
            str(key),
        ]
    by_action = {
        "upload": ["-BundlePath", str(bundle), "-ImageArchivePath", str(image_archive), "-ImageReference", "myis-a1.2-vast-runtime:v2"],
        "verify": ["-ExpectedGitCommit", "a" * 40, "-ExpectedGitTree", "b" * 40, "-ExpectedImageDigest", "sha256:" + "c" * 64, "-ImageReference", "myis-a1.2-vast-runtime:v2"],
        "start": ["-ExpectedImageDigest", "sha256:" + "c" * 64, "-ImageReference", "myis-a1.2-vast-runtime:v2"],
        "status": [],
        "collect": ["-CollectPath", str(collect)],
        "teardown": [],
    }
    for action, extra in by_action.items():
        args = list(common)
        args[args.index("verify")] = action
        completed = subprocess.run(
            args + extra + ["-DryRun"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, f"{action}: {completed.stderr}"
        assert json.loads(completed.stdout)["status"] == "dry_run_validated"
        assert str(key) not in completed.stdout

    fake_cli = tmp_path / "fake-vast.cmd"
    fake_cli.write_text("@exit /b 0\n", encoding="ascii")
    watchdog = ROOT / "scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1"
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(watchdog),
            "-Mode",
            "DryRun",
            "-ProviderInstanceId",
            "123456",
            "-HeartbeatPath",
            str(tmp_path / "heartbeat.json"),
            "-VastCliPath",
            str(fake_cli),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "dry_run_validated"
    assert payload["destroy_command_validated"] is True
    assert payload["provider_destroy_invoked"] is False
