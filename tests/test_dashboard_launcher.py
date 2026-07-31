from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.dashboard.launcher import DashboardLauncherError, _expected_health_payload, launch_dashboard


ROOT = Path(__file__).resolve().parents[1]


class FakeProcess:
    pid = 4321

    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self):
        return 0 if self.terminated or self.killed else None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: int) -> int:
        return 0


def test_launcher_reuses_only_a_healthy_dashboard() -> None:
    created = []
    opened = []
    result = launch_dashboard(
        ROOT,
        health_probe=lambda port: True,
        port_probe=lambda port: True,
        process_factory=lambda *args, **kwargs: created.append((args, kwargs)),
        browser_opener=opened.append,
    )
    assert result == {
        "status": "ready",
        "url": "http://127.0.0.1:8765",
        "reused": True,
        "pid": None,
    }
    assert created == []
    assert opened == ["http://127.0.0.1:8765"]


def test_launcher_refuses_an_unknown_process_on_the_port() -> None:
    with pytest.raises(DashboardLauncherError, match="unknown process"):
        launch_dashboard(
            ROOT,
            health_probe=lambda port: False,
            port_probe=lambda port: True,
        )


def test_launcher_waits_for_health_and_uses_loopback_cli() -> None:
    process = FakeProcess()
    calls = []
    health = iter((False, False, True))

    def factory(command, **kwargs):
        calls.append((command, kwargs))
        return process

    result = launch_dashboard(
        ROOT,
        open_browser=False,
        process_factory=factory,
        health_probe=lambda port: next(health),
        port_probe=lambda port: False,
        monotonic=iter((0.0, 0.1, 0.2, 0.3)).__next__,
        sleep=lambda seconds: None,
    )
    command, options = calls[0]
    assert command[1:3] == ["-m", "myis_research.dashboard.cli"]
    assert "--port" in command and "8765" in command
    assert "--launch-token" in command
    assert "--host" not in command
    assert options["shell"] is False
    assert result["reused"] is False
    assert result["pid"] == process.pid


def test_launcher_rolls_back_a_failed_child() -> None:
    process = FakeProcess()
    clock = iter((0.0, 0.1, 1.1))
    with pytest.raises(DashboardLauncherError, match="rolled back"):
        launch_dashboard(
            ROOT,
            open_browser=False,
            process_factory=lambda *args, **kwargs: process,
            health_probe=lambda port: False,
            port_probe=lambda port: False,
            timeout_seconds=1.0,
            monotonic=clock.__next__,
            sleep=lambda seconds: None,
        )
    assert process.terminated is True


def test_launcher_refuses_an_in_progress_startup_lock() -> None:
    from myis_research.dashboard.launcher import _startup_lock

    with _startup_lock(ROOT, 8765):
        with pytest.raises(DashboardLauncherError, match="already in progress"):
            launch_dashboard(ROOT, open_browser=False)


def test_reuse_accepts_only_the_optional_child_token_health_payload() -> None:
    base = {
        "status": "ok",
        "program_id": "myis-research",
        "protocol_version": "1.0",
        "research_version": "0.1",
    }
    assert _expected_health_payload(base, None)
    assert _expected_health_payload({**base, "launch_token": "child-token"}, None)
    assert _expected_health_payload({**base, "launch_token": "child-token"}, "child-token")
    assert not _expected_health_payload({**base, "launch_token": "other-child"}, "child-token")
    assert not _expected_health_payload({**base, "launch_token": "child-token", "extra": True}, None)
