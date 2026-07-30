"""Fixed-action controller for local research tools opened by the Dashboard."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import quote

from ..projections.read_model import build_read_model


class ToolControllerError(RuntimeError):
    """Raised when a fixed local tool action cannot be completed safely."""


class ToolController:
    def __init__(
        self,
        repository_root: Path,
        *,
        mlflow_port: int = 5000,
        store_root: Path | None = None,
        process_factory: Callable[..., Any] = subprocess.Popen,
        uri_opener: Callable[[str], Any] | None = None,
        health_probe: Callable[[int], bool] | None = None,
    ) -> None:
        self.repository_root = repository_root.resolve()
        configured = os.environ.get("MYIS_MLFLOW_STORE")
        self.store_root = (store_root or (Path(configured) if configured else self.repository_root.parent / "01_Stores/00_myIS/mlflow")).resolve()
        if not 1024 <= mlflow_port <= 65535:
            raise ToolControllerError("MLflow port is outside the allowed range")
        self.mlflow_port = mlflow_port
        self.process_factory = process_factory
        self.uri_opener = uri_opener or _open_uri
        self.health_probe = health_probe or _healthy_mlflow
        self._lock = threading.Lock()
        self._process: Any | None = None
        self._database_sha256: str | None = None

    def status(self) -> dict[str, Any]:
        mlflow = self._mlflow_status()
        obsidian = self._obsidian_status()
        return {
            "schema_version": "myis.dashboard-tools.v2",
            "mlflow": mlflow,
            "obsidian": obsidian,
        }

    def start_mlflow(self) -> dict[str, Any]:
        with self._lock:
            status = self._mlflow_status()
            if status["status"] == "ready":
                return {**status, "reused": True}
            if status["status"] == "failed" and status.get("reason") == "port_conflict":
                raise ToolControllerError("MLflow port is occupied by an unknown process")
            database = self._validate_store()
            before = _file_sha256(database)
            command = self._viewer_command()
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            try:
                self._process = self.process_factory(
                    command,
                    cwd=self.repository_root,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=flags,
                    shell=False,
                )
            except OSError as error:
                raise ToolControllerError("read-only MLflow viewer could not start") from error
            deadline = time.monotonic() + 12.0
            while time.monotonic() < deadline:
                if self.health_probe(self.mlflow_port):
                    after = _file_sha256(database)
                    if after != before:
                        self._terminate_owned_process()
                        raise ToolControllerError("MLflow viewer changed the canonical database")
                    self._database_sha256 = before
                    return {"status": "ready", "url": self._mlflow_url(), "reused": False}
                if self._process.poll() is not None:
                    break
                time.sleep(0.1)
            self._terminate_owned_process()
            raise ToolControllerError("read-only MLflow viewer failed its health check")

    def stop_mlflow(self) -> dict[str, Any]:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                if self.health_probe(self.mlflow_port):
                    raise ToolControllerError("refusing to stop a viewer not owned by this Dashboard process")
                self._process = None
                return {"status": "stopped"}
            self._terminate_owned_process()
            return {"status": "stopped"}

    def restart_mlflow(self) -> dict[str, Any]:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._terminate_owned_process()
        return self.start_mlflow()

    def open_obsidian(self, note_id: str = "HOME") -> dict[str, Any]:
        if not isinstance(note_id, str) or not note_id or not all(char.isalnum() or char in ".-" for char in note_id):
            raise ToolControllerError("note_id is invalid")
        manifest, vault_root = self._validated_obsidian_manifest()
        entry = next((item for item in manifest["files"] if item.get("note_id") == note_id), None)
        if entry is None:
            raise ToolControllerError("note_id is not in the generated vault manifest")
        relative = Path(str(entry["relative_path"]))
        note = (vault_root / relative).resolve(strict=True)
        note.relative_to(vault_root)
        if note.is_symlink() or not note.is_file() or _file_sha256(note) != entry.get("sha256"):
            raise ToolControllerError("Obsidian note hash does not match the generated manifest")
        uri = f"obsidian://open?vault={quote('myIS Research Report')}&file={quote(relative.with_suffix('').as_posix())}"
        try:
            self.uri_opener(uri)
        except OSError as error:
            raise ToolControllerError("Obsidian URI handler is unavailable") from error
        return {"status": "opened", "note_id": note_id}

    def _viewer_command(self) -> list[str]:
        app = (self.repository_root / "dashboard/mlflow/readonly_app.py").resolve(strict=True)
        app.relative_to(self.repository_root)
        return [
            sys.executable,
            str(app),
            "serve",
            "--repository-root",
            str(self.repository_root),
            "--store-root",
            str(self.store_root),
            "--port",
            str(self.mlflow_port),
        ]

    def _validate_store(self) -> Path:
        try:
            self.store_root.relative_to(self.repository_root)
        except ValueError:
            pass
        else:
            raise ToolControllerError("MLflow store must be outside Git")
        if self.store_root.is_symlink() or not self.store_root.is_dir():
            raise ToolControllerError("MLflow store is missing or unsafe")
        database = self.store_root / "database/mlflow.db"
        bootstrap = self.store_root / "mlflow-bootstrap.json"
        if not database.is_file() or database.is_symlink() or not bootstrap.is_file():
            raise ToolControllerError("MLflow store has not passed bootstrap")
        try:
            report = json.loads(bootstrap.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ToolControllerError("MLflow bootstrap report is invalid") from error
        if report.get("status") != "PASS":
            raise ToolControllerError("MLflow bootstrap report is not PASS")
        return database

    def _mlflow_status(self) -> dict[str, Any]:
        if self.health_probe(self.mlflow_port):
            if self._process is not None and self._process.poll() is None:
                return {"status": "ready", "url": self._mlflow_url()}
            return {"status": "failed", "reason": "port_conflict"}
        if _port_open(self.mlflow_port):
            return {"status": "failed", "reason": "port_conflict"}
        if not self.store_root.is_dir():
            return {"status": "failed", "reason": "store_missing"}
        return {"status": "stopped"}

    def _obsidian_status(self) -> dict[str, Any]:
        try:
            manifest, _ = self._validated_obsidian_manifest()
        except ToolControllerError as error:
            return {"status": "failed", "reason": str(error)}
        return {"status": "ready", "note_count": len(manifest["files"])}

    def _validated_obsidian_manifest(self) -> tuple[Mapping[str, Any], Path]:
        vault_root = (self.repository_root / "obsidian_report").resolve(strict=True)
        vault_root.relative_to(self.repository_root)
        home = vault_root / "HOME.md"
        manifest_path = vault_root / "00_System/Generated/generated-manifest.json"
        if not home.is_file() or home.is_symlink() or not manifest_path.is_file() or manifest_path.is_symlink():
            raise ToolControllerError("Obsidian vault is missing generated control files")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ToolControllerError("Obsidian generated manifest is invalid") from error
        if manifest.get("schema_version") != "myis.obsidian-generated-manifest.v2" or not isinstance(manifest.get("files"), list):
            raise ToolControllerError("Obsidian generated manifest contract is invalid")
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        if hashlib.sha256(json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest() != manifest.get("manifest_sha256"):
            raise ToolControllerError("Obsidian generated manifest hash is invalid")
        model = build_read_model(self.repository_root)
        for key in ("read_model_revision", "read_model_sha256", "source_commit", "projection_schema_version"):
            if manifest.get(key) != model.get(key):
                raise ToolControllerError("Obsidian vault is stale")
        return manifest, vault_root

    def _mlflow_url(self) -> str:
        return f"http://127.0.0.1:{self.mlflow_port}"

    def _terminate_owned_process(self) -> None:
        process = self._process
        self._process = None
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.kill(int(process.pid), signal.SIGKILL)
            except OSError:
                pass


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _healthy_mlflow(port: int) -> bool:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
    try:
        connection.request("GET", "/health", headers={"Host": f"127.0.0.1:{port}"})
        response = connection.getresponse()
        return response.status == 200 and response.read() == b"OK" and response.getheader("Cache-Control") == "no-store"
    except OSError:
        return False
    finally:
        connection.close()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _open_uri(uri: str) -> None:
    if os.name != "nt" or not hasattr(os, "startfile"):
        raise OSError("Obsidian URI handler is only supported on Windows")
    os.startfile(uri)  # type: ignore[attr-defined]
