from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16.ps1"
REPAIR = ROOT / "scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16R2.ps1"
CONTRACT = ROOT / "control/armindex/a1.2/engineering-execution-contract.v16.json"


def _watchdog_prerequisites(tmp_path: Path) -> tuple[str, Path, Path, Path, Path]:
    powershell = shutil.which("powershell.exe")
    ssh_keygen = Path(r"C:\Windows\System32\OpenSSH\ssh-keygen.exe")
    if powershell is None or not ssh_keygen.is_file():
        pytest.skip("Windows OpenSSH test prerequisites are unavailable")
    private_key = tmp_path / "test_ed25519"
    generated = subprocess.run(
        [str(ssh_keygen), "-q", "-t", "ed25519", "-N", "", "-f", str(private_key)],
        capture_output=True, text=True, check=False, timeout=15,
    )
    assert generated.returncode == 0, generated.stderr
    key_parts = private_key.with_suffix(".pub").read_text(encoding="utf-8").split()[:2]
    known_hosts_dir = Path(tempfile.mkdtemp(prefix="myis-watchdog-test-", dir=r"C:\Users\Public"))
    known_hosts = known_hosts_dir / "known_hosts"
    known_hosts.write_text(f"[127.0.0.1]:2222 {' '.join(key_parts)}\n", encoding="utf-8")
    fingerprint = subprocess.run(
        [str(ssh_keygen), "-lf", str(known_hosts), "-E", "sha256"],
        capture_output=True, text=True, check=False, timeout=15,
    )
    assert fingerprint.returncode == 0, fingerprint.stderr
    match = re.search(r"SHA256:[A-Za-z0-9+/=]+", fingerprint.stdout)
    assert match is not None
    owner_connection = tmp_path / "owner-connection.txt"
    owner_connection.write_text(f"SSH_HOST_FINGERPRINT: {match.group(0)}\n", encoding="utf-8")
    return powershell, private_key, known_hosts_dir, known_hosts, owner_connection


def _watchdog_command(
    powershell: str, private_key: Path, known_hosts: Path, owner_connection: Path,
    output: Path, fake_ssh: Path, *, timeout_seconds: int = 3,
) -> list[str]:
    return [
        powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(REPAIR),
        "-InstanceId", "47411176", "-SshHost", "127.0.0.1", "-SshPort", "2222",
        "-SshKeyPath", str(private_key), "-OwnerConnectionFile", str(owner_connection),
        "-OutputDirectory", str(output), "-KnownHostsPath", str(known_hosts),
        "-TtlDeadlineUtc", "2030-01-01T00:00:00Z", "-ExpectedHostname", "synthetic-host",
        "-ExpectedInstanceIdentitySha256", "a" * 64, "-ExpectedGpuUuidSetSha256", "b" * 64,
        "-MaximumTotalHourlyUsd", "1.0", "-ProviderObservationMode", "OwnerDashboardSsh",
        "-OwnerDashboardTotalHourlyUsd", "0.6", "-OwnerDashboardEvidenceSha256", "c" * 64,
        "-OwnerManualDestroyReady", "-RuntimeProbeTimeoutSeconds", str(timeout_seconds),
        "-SshExecutablePath", str(fake_ssh),
    ]


def test_watchdog_repair_preserves_frozen_original_and_filters_provider_banner() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == contract["support_sources"]["watchdog"]["sha256"]
    repair = REPAIR.read_text(encoding="utf-8")
    assert 'runtimeRaw -join "`n"' in repair
    assert '-split "`r?`n"' in repair
    assert "runtimeJson.Count -ne 1" in repair
    assert "runtime_probe_json_invalid" in repair
    assert "TrimStart().StartsWith('{')" in repair
    assert "[string]$KnownHostsPath = ''" in repair
    assert "KnownHostsPath must not contain whitespace" in repair
    assert "SSH_HOST_FINGERPRINT:" in repair
    assert "RuntimeProbeTimeoutSeconds" in repair
    assert "ssh_runtime_probe_timeout" in repair
    assert "Stop-ChildProcessTree" in repair
    assert "taskkill.exe" in repair


@pytest.mark.skipif(os.name != "nt", reason="Windows-only watchdog process test")
def test_hung_ssh_runtime_probe_hard_stops_and_reaps_child(tmp_path: Path) -> None:
    powershell, private_key, known_hosts_dir, known_hosts, owner_connection = _watchdog_prerequisites(tmp_path)

    started = tmp_path / "started.txt"
    survived = tmp_path / "survived.txt"
    fake_ssh = tmp_path / "hang-ssh.cmd"
    fake_ssh.write_text(
        "@echo off\r\n"
        f"powershell.exe -NoProfile -Command \"Set-Content -LiteralPath '{started}' -Value started; Start-Sleep -Seconds 8; Set-Content -LiteralPath '{survived}' -Value survived\"\r\n",
        encoding="ascii",
    )
    output = tmp_path / "watchdog-output"
    command = _watchdog_command(powershell, private_key, known_hosts, owner_connection, output, fake_ssh, timeout_seconds=1)
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=20, check=False
        )
        assert completed.returncode == 0, completed.stderr
        heartbeat = json.loads((output / "heartbeat.json").read_text(encoding="utf-8"))
        assert heartbeat["status"] == "HARD_STOP"
        assert heartbeat["hard_stop_reason"] == "ssh_runtime_probe_timeout"
        assert heartbeat["provider_destroy_invoked"] is False
        time.sleep(2)
        assert started.exists()
        assert not survived.exists()
        with (output / "watchdog.lock").open("a+b"):
            pass
    finally:
        shutil.rmtree(known_hosts_dir, ignore_errors=True)


@pytest.mark.skipif(os.name != "nt", reason="Windows-only watchdog process test")
def test_zero_exit_runtime_probe_reaches_pass_before_controlled_stop(tmp_path: Path) -> None:
    powershell, private_key, known_hosts_dir, known_hosts, owner_connection = _watchdog_prerequisites(tmp_path)
    fake_ssh = tmp_path / "success-ssh.cmd"
    fake_ssh.write_text(
        "@echo off\r\n"
        "echo {\"hostname\":\"synthetic-host\",\"python\":\"3.11.11\",\"torch\":\"2.6.0+cu118\",\"cuda\":\"11.8\",\"gpu_count\":4,\"gpu_names_match\":true,\"gpu_memory_min_mib\":24576,\"gpu_uuid_set_sha256\":\"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\"}\r\n"
        "exit /b 0\r\n",
        encoding="ascii",
    )
    output = tmp_path / "watchdog-output"
    process = subprocess.Popen(
        _watchdog_command(powershell, private_key, known_hosts, owner_connection, output, fake_ssh),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            heartbeat_path = output / "heartbeat.json"
            if heartbeat_path.is_file():
                heartbeat = json.loads(heartbeat_path.read_text(encoding="utf-8"))
                if heartbeat["status"] == "PASS":
                    break
            time.sleep(0.1)
        else:
            pytest.fail("zero-exit SSH probe did not reach the PASS/provider path")
        assert heartbeat["provider_status_match"] is True
        assert heartbeat["runtime_identity_match"] is True
        assert heartbeat["gpu_identity_4_of_4"] is True
        process.terminate()
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        shutil.rmtree(known_hosts_dir, ignore_errors=True)


@pytest.mark.skipif(os.name != "nt", reason="Windows-only watchdog process test")
def test_nonzero_ssh_exit_is_classified_as_runtime_probe_failure(tmp_path: Path) -> None:
    powershell, private_key, known_hosts_dir, known_hosts, owner_connection = _watchdog_prerequisites(tmp_path)
    fake_ssh = tmp_path / "failed-ssh.cmd"
    fake_ssh.write_text("@echo off\r\nexit /b 7\r\n", encoding="ascii")
    output = tmp_path / "watchdog-output"
    try:
        completed = subprocess.run(
            _watchdog_command(powershell, private_key, known_hosts, owner_connection, output, fake_ssh),
            capture_output=True, text=True, timeout=15, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        heartbeat = json.loads((output / "heartbeat.json").read_text(encoding="utf-8"))
        assert heartbeat["status"] == "HARD_STOP"
        assert heartbeat["hard_stop_reason"] == "ssh_runtime_probe_failed"
    finally:
        shutil.rmtree(known_hosts_dir, ignore_errors=True)
