"""Health-checked one-click launcher for the loopback Dashboard."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import http.client
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable, Iterator

from ..identity import PROGRAM_ID, PROTOCOL_VERSION, RESEARCH_VERSION
from .contract import DASHBOARD_API_CONTRACT


class DashboardLauncherError(RuntimeError):
    """Raised when the Dashboard cannot be started without ambiguity."""


def launch_dashboard(
    repository_root: Path,
    *,
    port: int = 8765,
    open_browser: bool = True,
    process_factory: Callable[..., Any] = subprocess.Popen,
    health_probe: Callable[[int], bool] | None = None,
    port_probe: Callable[[int], bool] | None = None,
    browser_opener: Callable[[str], Any] = webbrowser.open,
    timeout_seconds: float = 12.0,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Start one Dashboard process, or reuse the verified loopback instance."""

    if not 1024 <= port <= 65535:
        raise DashboardLauncherError("Dashboard port is outside the allowed range")
    root = repository_root.resolve(strict=True)
    if root.is_symlink() or not (root / "pyproject.toml").is_file():
        raise DashboardLauncherError("repository root is missing or unsafe")
    healthy = health_probe or dashboard_health
    occupied = port_probe or port_open
    url = f"http://127.0.0.1:{port}"
    with _startup_lock(root, port):
        if healthy(port):
            if open_browser:
                browser_opener(url)
            return {"status": "ready", "url": url, "reused": True, "pid": None}
        if occupied(port):
            raise DashboardLauncherError("Dashboard port is occupied by an unknown process")

        launch_token = secrets.token_urlsafe(32)
        command = [
            sys.executable,
            "-m",
            "myis_research.dashboard.cli",
            "--repository-root",
            str(root),
            "--port",
            str(port),
            "--launch-token",
            launch_token,
        ]
        creationflags = 0
        if os.name == "nt":
            creationflags = (
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "CREATE_NO_WINDOW", 0)
                | getattr(subprocess, "DETACHED_PROCESS", 0)
            )
        try:
            process = process_factory(
                command,
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                shell=False,
            )
        except OSError as error:
            raise DashboardLauncherError("Dashboard process could not start") from error

        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if process.poll() is not None:
                break
            # The production probe requires the nonce emitted only by this child.
            child_is_healthy = dashboard_health(port, launch_token) if health_probe is None else healthy(port)
            if child_is_healthy:
                if open_browser:
                    browser_opener(url)
                return {
                    "status": "ready",
                    "url": url,
                    "reused": False,
                    "pid": int(process.pid),
                }
            sleep(0.1)
        _rollback_process(process)
        raise DashboardLauncherError("Dashboard failed its health check; child process rolled back")


def dashboard_health(port: int, launch_token: str | None = None) -> bool:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
    try:
        connection.request("GET", "/healthz", headers={"Host": f"127.0.0.1:{port}"})
        response = connection.getresponse()
        payload = json.loads(response.read())
        return (
            response.status == 200
            and response.getheader("Cache-Control") == "no-store, max-age=0"
            and _expected_health_payload(payload, launch_token)
        )
    except (OSError, json.JSONDecodeError):
        return False
    finally:
        connection.close()


def _expected_health_payload(payload: Any, launch_token: str | None) -> bool:
    expected = {
        "status": "ok",
        "program_id": PROGRAM_ID,
        "protocol_version": PROTOCOL_VERSION,
        "research_version": RESEARCH_VERSION,
        "api_contract": DASHBOARD_API_CONTRACT,
    }
    if launch_token is not None:
        return payload == {**expected, "launch_token": launch_token}
    # A live instance started by this launcher includes a per-child nonce.
    # Reuse it only when every other field still matches the canonical health contract.
    return payload == expected or (
        isinstance(payload, dict)
        and set(payload) == {*expected, "launch_token"}
        and all(payload.get(key) == value for key, value in expected.items())
        and isinstance(payload.get("launch_token"), str)
        and bool(payload["launch_token"])
    )


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _rollback_process(process: Any) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass


@contextmanager
def _startup_lock(root: Path, port: int) -> Iterator[None]:
    """Serialize the port check and child start across local launcher processes."""

    lock_root = root / "projections" / "dashboard-private"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / f"launcher-{port}.lock"
    handle = lock_path.open("a+b")
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise DashboardLauncherError("another Dashboard launch is already in progress") from error
        yield
    finally:
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-dashboard-open")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = launch_dashboard(
            args.repository_root,
            port=args.port,
            open_browser=not args.no_browser,
        )
    except DashboardLauncherError as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}, ensure_ascii=True))
        return 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
