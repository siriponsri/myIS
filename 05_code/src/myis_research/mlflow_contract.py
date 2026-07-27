"""Small dependency-free local MLflow run contract.

When the optional ``mlflow`` package is available, a caller may additionally
mirror the run to a tracking server. The local artifact ledger is always
written, so offline demos and failed runs remain auditable.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = ("prompt.json", "flow.json", "progress.jsonl", "result.json", "metrics.json")


@dataclass(frozen=True)
class AgentRunSpec:
    component: str
    agent_id: str
    experiment: str
    prompt_version: str
    skill_version: str
    model_id: str = "offline-fixture"
    source_manifest_hash: str = "unavailable"
    owner_approval_source: str = "owner-approved-offline-demo"
    git_sha: str = "unknown"
    tags: dict[str, str] = field(default_factory=dict)


class AgentRun:
    """Write the five required artifacts to one immutable local run folder."""

    def __init__(self, root: Path, spec: AgentRunSpec):
        self.root = root
        self.spec = spec
        self.run_id = uuid.uuid4().hex
        self.run_dir = root / "runs" / self.run_id
        self._started = False

    @classmethod
    def start(cls, root: Path, spec: AgentRunSpec) -> "AgentRun":
        run = cls(root, spec)
        run.run_dir.mkdir(parents=True, exist_ok=False)
        run._started = True
        run._write_json("run.json", {
            "run_id": run.run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "RUNNING",
            "backend": "local-mlflow-ledger",
            "python": platform.python_version(),
            "platform": platform.platform(),
            "spec": spec.__dict__,
        })
        return run

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("AgentRun.start(...) must be called before logging")

    def _write_json(self, name: str, value: Any) -> None:
        self.run_dir.joinpath(name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def log_prompt(self, prompt: str, *, version: str | None = None, rules: list[str] | None = None) -> None:
        self._ensure_started()
        self._write_json("prompt.json", {"prompt": prompt, "version": version or self.spec.prompt_version, "rules": rules or []})

    def log_flow(self, steps: list[str], *, engine: str = "brain-drive") -> None:
        self._ensure_started()
        self._write_json("flow.json", {"engine": engine, "steps": steps})

    def progress(self, event: str, **details: Any) -> None:
        self._ensure_started()
        payload = {"at": datetime.now(timezone.utc).isoformat(), "event": event, **details}
        with self.run_dir.joinpath("progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True) + "\n")

    def log_result(self, result: dict[str, Any]) -> None:
        self._ensure_started()
        self._write_json("result.json", result)

    def log_metric(self, name: str, value: float) -> None:
        self._ensure_started()
        metrics = {}
        path = self.run_dir / "metrics.json"
        if path.exists():
            metrics = json.loads(path.read_text(encoding="utf-8"))
        metrics[name] = float(value)
        self._write_json("metrics.json", metrics)

    def close(self, status: str = "FINISHED") -> Path:
        self._ensure_started()
        missing = [name for name in REQUIRED_ARTIFACTS if not (self.run_dir / name).exists()]
        if missing:
            raise RuntimeError(f"Cannot close run; missing artifacts: {', '.join(missing)}")
        run_meta = json.loads((self.run_dir / "run.json").read_text(encoding="utf-8"))
        run_meta.update({"status": status, "finished_at": datetime.now(timezone.utc).isoformat()})
        self._write_json("run.json", run_meta)
        manifest = {name: hashlib.sha256((self.run_dir / name).read_bytes()).hexdigest() for name in REQUIRED_ARTIFACTS}
        self._write_json("artifact_manifest.json", manifest)
        self._mirror_to_mlflow(status)
        return self.run_dir

    def _mirror_to_mlflow(self, status: str) -> bool:
        """Mirror the ledger to local MLflow when the optional extra is installed."""
        try:
            import mlflow
        except ImportError:
            return False
        database_dir = self.root / "database"
        artifacts = self.root / "artifacts"
        database_dir.mkdir(parents=True, exist_ok=True)
        artifacts.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(f"sqlite:///{(database_dir / 'mlflow.db').resolve().as_posix()}")
        experiment = mlflow.get_experiment_by_name(self.spec.experiment)
        experiment_id = (
            experiment.experiment_id
            if experiment
            else mlflow.create_experiment(self.spec.experiment, artifact_location=artifacts.resolve().as_uri())
        )
        tags = {
            "component": self.spec.component,
            "agent_id": self.spec.agent_id,
            "git_sha": self.spec.git_sha,
            "source_manifest_hash": self.spec.source_manifest_hash,
            "prompt_version": self.spec.prompt_version,
            "skill_version": self.spec.skill_version,
            "model_id": self.spec.model_id,
            "status": status,
            "owner_approval_source": self.spec.owner_approval_source,
            **self.spec.tags,
        }
        with mlflow.start_run(experiment_id=experiment_id, run_name=self.run_id, tags=tags):
            mlflow.log_artifacts(str(self.run_dir), artifact_path="agent_contract")
            metrics = json.loads((self.run_dir / "metrics.json").read_text(encoding="utf-8"))
            for name, value in metrics.items():
                mlflow.log_metric(name, float(value))
        return True

    def fail(self, error: BaseException | str) -> Path:
        """Close a failed run while preserving a complete audit record."""
        self._ensure_started()
        message = str(error)
        defaults: dict[str, Any] = {
            "prompt.json": {"prompt": "unavailable", "version": self.spec.prompt_version, "rules": []},
            "flow.json": {"engine": "unknown", "steps": []},
            "result.json": {"status": "FAILED", "error": message},
            "metrics.json": {},
        }
        for name, value in defaults.items():
            if not (self.run_dir / name).exists():
                self._write_json(name, value)
        self.progress("run_failed", error=message)
        return self.close("FAILED")


def default_store(root: Path | None = None) -> Path:
    if root:
        return root
    configured = os.environ.get("MYIS_MLFLOW_STORE")
    if configured:
        return Path(configured).expanduser().resolve()
    current = Path.cwd().resolve()
    for ancestor in (current, *current.parents):
        candidate = ancestor / "01_Stores" / "00_myIS" / "mlflow"
        if candidate.parent.is_dir():
            return candidate
    raise RuntimeError("Cannot locate shared MLflow store; set MYIS_MLFLOW_STORE")
