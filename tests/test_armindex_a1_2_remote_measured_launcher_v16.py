from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_remote_measured_launcher_v16 as launcher


def _manifest(root: Path, attempt_id: str) -> Path:
    (root / "cell.jsonl").write_text("{}\n", encoding="ascii")
    (root / "work.jsonl").write_text("{}\n", encoding="ascii")
    cells = []
    for arm in ("ARM-01", *launcher.REMOTE_ARM_SLOTS):
        for program in ("P00", "P01", "P02", "P03", "P04"):
            cells.append({"binding_path": "cell.jsonl", "corpus_path": "cell.jsonl", "query_path": "cell.jsonl"})
    value = {
        "attempt_id": attempt_id,
        "cells": cells,
        "work_tokens": {"path": "work.jsonl"},
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(value), encoding="ascii")
    return path


def test_remote_launcher_uses_v16_worker_and_pinned_ssh(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setenv("PIP_NO_INDEX", "1")
    manifest = _manifest(tmp_path, "attempt-v16")
    adoption = tmp_path / "adoption.json"
    adoption.write_text(json.dumps({"status": "PASS", "measured_retrieval_allowed": True}), encoding="ascii")
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("key", encoding="ascii")
    known.write_text("host", encoding="ascii")
    calls: list[tuple[str, list[str]]] = []

    def fake_native(executable: str, arguments: list[str], *, role: str) -> str:
        calls.append((executable, arguments))
        return "1234" if "remote launch" in role else ""

    monkeypatch.setattr(launcher, "_native", fake_native)
    result = launcher.stage_and_launch_remote_arms(
        bundle_path=bundle,
        manifest_path=manifest,
        adoption_receipt_path=adoption,
        remote_root="/opt/myis/a1.2-test",
        remote_model_root="/opt/myis/a1.2-v16-stage-20260809/models",
        attempt_id="attempt-v16",
        ssh_host="151.237.25.234",
        ssh_port=27068,
        ssh_key_path=key,
        known_hosts_path=known,
    )
    assert result["status"] == "PASS"
    assert set(result["remote_pids"]) == set(launcher.REMOTE_ARM_SLOTS)
    joined = "\n".join(" ".join(args) for _, args in calls)
    assert "a1_2_remote_arm_worker_v16" in joined
    assert "a1_2_vast remote-worker" not in joined
    assert "sha256sum -c SHA256SUMS" in joined
    assert "-P 27068" in joined
    assert "PYTHONPATH=/opt/myis/a1.2-test/current/src" in joined
    assert "StrictHostKeyChecking=yes" in " ".join(calls[0][1])
    assert "UserKnownHostsFile=" in " ".join(calls[0][1])


def test_wait_remote_arms_retries_until_all_screens_exist(monkeypatch, tmp_path: Path) -> None:
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("key", encoding="ascii")
    known.write_text("host", encoding="ascii")
    attempts = iter((False, True))

    def fake_native(executable: str, arguments: list[str], *, role: str) -> str:
        if next(attempts):
            return "PASS"
        raise launcher.RemoteMeasuredLauncherV16Error("not ready")

    monkeypatch.setattr(launcher, "_native", fake_native)
    result = launcher.wait_remote_arms(
        remote_root="/opt/myis/a1.2-test",
        attempt_id="attempt-v16",
        ssh_host="151.237.25.234",
        ssh_port=27068,
        ssh_key_path=key,
        known_hosts_path=known,
        timeout_seconds=3,
        poll_seconds=1,
    )
    assert result["status"] == "PASS"


def test_wait_remote_arms_fails_fast_on_worker_failure(monkeypatch, tmp_path: Path) -> None:
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("key", encoding="ascii")
    known.write_text("host", encoding="ascii")

    def fake_native(executable: str, arguments: list[str], *, role: str) -> str:
        return "FAIL:/opt/myis/a1.2-test/output/ARM-03/worker.failure"

    monkeypatch.setattr(launcher, "_native", fake_native)
    with pytest.raises(launcher.RemoteMeasuredLauncherV16Error, match="worker failed"):
        launcher.wait_remote_arms(
            remote_root="/opt/myis/a1.2-test",
            attempt_id="attempt-v16",
            ssh_host="151.237.25.234",
            ssh_port=27068,
            ssh_key_path=key,
            known_hosts_path=known,
            timeout_seconds=3,
            poll_seconds=1,
        )


def test_remote_launcher_rejects_shell_metacharacters_and_reaps_started_workers(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setenv("PIP_NO_INDEX", "1")
    manifest = _manifest(tmp_path, "attempt-v16")
    adoption = tmp_path / "adoption.json"
    adoption.write_text(json.dumps({"status": "PASS", "measured_retrieval_allowed": True}), encoding="ascii")
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("key", encoding="ascii")
    known.write_text("host", encoding="ascii")
    with pytest.raises(launcher.RemoteMeasuredLauncherV16Error, match="remote root"):
        launcher.stage_and_launch_remote_arms(
            bundle_path=bundle,
            manifest_path=manifest,
            adoption_receipt_path=adoption,
            remote_root="/opt/myis/a1.2-test;touch",
            remote_model_root="/opt/myis/a1.2-v16-stage-20260809/models",
            attempt_id="attempt-v16",
            ssh_host="151.237.25.234",
            ssh_port=27068,
            ssh_key_path=key,
            known_hosts_path=known,
        )

    calls: list[tuple[str, list[str], str]] = []
    launch_count = 0

    def failing_native(executable: str, arguments: list[str], *, role: str) -> str:
        nonlocal launch_count
        calls.append((executable, arguments, role))
        if "remote launch" in role:
            launch_count += 1
            if launch_count == 2:
                raise launcher.RemoteMeasuredLauncherV16Error("simulated launch failure")
            return "1234"
        return ""

    monkeypatch.setattr(launcher, "_native", failing_native)
    with pytest.raises(launcher.RemoteMeasuredLauncherV16Error, match="simulated launch failure"):
        launcher.stage_and_launch_remote_arms(
            bundle_path=bundle,
            manifest_path=manifest,
            adoption_receipt_path=adoption,
            remote_root="/opt/myis/a1.2-test",
            remote_model_root="/opt/myis/a1.2-v16-stage-20260809/models",
            attempt_id="attempt-v16",
            ssh_host="151.237.25.234",
            ssh_port=27068,
            ssh_key_path=key,
            known_hosts_path=known,
        )
    assert any(role == "remote sibling cleanup" for _exe, _args, role in calls)


def test_remote_collection_copies_only_attempt_outputs(monkeypatch, tmp_path: Path) -> None:
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("key", encoding="ascii")
    known.write_text("host", encoding="ascii")
    destination = tmp_path / "collected"
    calls: list[tuple[str, list[str], str]] = []

    def fake_native(executable: str, arguments: list[str], *, role: str) -> str:
        calls.append((executable, arguments, role))
        if role.endswith("output collection"):
            arm = role.split()[0]
            screen = destination / arm / "attempt-v16" / "receipts" / "screen.json"
            screen.parent.mkdir(parents=True, exist_ok=True)
            screen.write_text("{}", encoding="ascii")
        return ""

    monkeypatch.setattr(launcher, "_native", fake_native)
    result = launcher.collect_remote_arm_outputs(
        remote_root="/opt/myis/a1.2-test",
        attempt_id="attempt-v16",
        local_output_root=destination,
        ssh_host="151.237.25.234",
        ssh_port=27068,
        ssh_key_path=key,
        known_hosts_path=known,
    )
    assert result == {"status": "PASS", "attempt_id": "attempt-v16", "arms": list(launcher.REMOTE_ARM_SLOTS), "cells": 20, "measured_retrieval": True}
    joined = "\n".join(" ".join(arguments) for _executable, arguments, _role in calls)
    assert "-r root@151.237.25.234:/opt/myis/a1.2-test/output/ARM-02/attempt-v16" in joined
    assert "worker.stdout" not in joined and "worker.stderr" not in joined


def test_remote_transfer_sanitizes_adoption_receipt(monkeypatch, tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, "attempt-v16")
    adoption = tmp_path / "adoption.json"
    adoption.write_text(
        json.dumps(
            {
                "status": "PASS",
                "measured_retrieval_allowed": True,
                "credential": "must-not-transfer",
            }
        ),
        encoding="ascii",
    )
    archive, _digest = launcher._manifest_transfer_archive(manifest, adoption)
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            payload = json.loads(bundle.extractfile("adoption.json").read().decode("ascii"))
        assert payload == {"measured_retrieval_allowed": True, "status": "PASS"}
    finally:
        shutil.rmtree(archive.parent, ignore_errors=True)
