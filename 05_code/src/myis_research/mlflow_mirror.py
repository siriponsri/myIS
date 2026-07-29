"""Governed local MLflow mirror for myIS Research.

Git and immutable validated artifacts remain authoritative.  This module only
creates a searchable, rebuildable projection and deliberately accepts files
one at a time so callers cannot upload a directory accidentally.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import time
import tomllib
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterator, Mapping, Protocol, Sequence


PROGRAM_ID = "myis-research"
DISPLAY_NAME = "myIS Research"
PROTOCOL_VERSION = "1.0"
RESEARCH_VERSION = "0.1"
BOOTSTRAP_EXPERIMENT = "myis-research-bootstrap"
CATALOG_EXPERIMENT = "myis-research-catalog"
TRACK_C_EXPERIMENT = "myis-research-track-c"
TRACK_S_EXPERIMENT = "myis-research-track-s"
JOINT_EXPERIMENT = "myis-research-joint"
PUBLICATION_EXPERIMENT = "myis-research-publication"
EXPERIMENTS = (
    BOOTSTRAP_EXPERIMENT,
    CATALOG_EXPERIMENT,
    TRACK_C_EXPERIMENT,
    TRACK_S_EXPERIMENT,
    JOINT_EXPERIMENT,
    PUBLICATION_EXPERIMENT,
)
RECEIPT_SCHEMA = "myis.mlflow-mirror-receipt.v1"

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_FORBIDDEN_PATH_RE = re.compile(
    r"(?:^|[._/\\-])(qrels?|confirmation|heldout|held-out|membership|"
    r"per[_-]?query|credentials?|secrets?|provider[_-]?payload)(?:[._/\\-]|$)",
    re.IGNORECASE,
)
_FORBIDDEN_STRUCTURED_KEY_RE = re.compile(
    r"(?:qrels?|confirmation(?:_ids?|_outcomes?)?|split_membership|membership_ids?|"
    r"per_query|query_ids?|credentials?|api_keys?|access_tokens?|refresh_tokens?|"
    r"provider_payload|raw_provider)",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}|(?:api[_-]?key|password|secret)\s*[:=]\s*[^\s]{8,})",
    re.IGNORECASE,
)
_TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".toml", ".txt", ".yaml", ".yml"}
_RESERVED_TAGS = {
    "program_id",
    "display_name",
    "protocol_version",
    "research_version",
    "stage",
    "mirror_key",
    "canonical_source_sha256",
    "git_commit",
    "canonical_authority",
    "projection_schema_version",
    "plan_sha256",
    "phase_ids",
    "task_ids",
    "gate_ids",
    "linear_issue_ids",
    "dashboard_content_id",
}


class MirrorValidationError(ValueError):
    """Raised when an attempted mirror crosses an allowlisted boundary."""


class MirrorKind(StrEnum):
    DOC = "docs"
    RESULT = "results"
    METRIC = "metrics"
    RUBRIC = "rubrics"
    RULE = "rules"
    TOOL = "tools"
    SKILL = "skills"
    ENVIRONMENT = "environment"


class MirrorStage(StrEnum):
    BOOTSTRAP = "bootstrap"
    CATALOG = "catalog"
    F1_G1_PREPARATION = "f1-g1-preparation"
    TRACK_C = "track-c"
    TRACK_S = "track-s"
    JOINT = "joint"
    PUBLICATION = "publication"

    @property
    def experiment_name(self) -> str:
        return {
            MirrorStage.BOOTSTRAP: BOOTSTRAP_EXPERIMENT,
            MirrorStage.CATALOG: CATALOG_EXPERIMENT,
            MirrorStage.F1_G1_PREPARATION: TRACK_C_EXPERIMENT,
            MirrorStage.TRACK_C: TRACK_C_EXPERIMENT,
            MirrorStage.TRACK_S: TRACK_S_EXPERIMENT,
            MirrorStage.JOINT: JOINT_EXPERIMENT,
            MirrorStage.PUBLICATION: PUBLICATION_EXPERIMENT,
        }[self]


_STAGE_KINDS = {
    MirrorStage.BOOTSTRAP: frozenset(),
    MirrorStage.CATALOG: frozenset(
        {MirrorKind.DOC, MirrorKind.RUBRIC, MirrorKind.RULE, MirrorKind.TOOL, MirrorKind.SKILL, MirrorKind.ENVIRONMENT}
    ),
    MirrorStage.F1_G1_PREPARATION: frozenset(),
    MirrorStage.TRACK_C: frozenset({MirrorKind.RESULT, MirrorKind.METRIC, MirrorKind.ENVIRONMENT}),
    MirrorStage.TRACK_S: frozenset({MirrorKind.RESULT, MirrorKind.METRIC, MirrorKind.ENVIRONMENT}),
    MirrorStage.JOINT: frozenset({MirrorKind.RESULT, MirrorKind.METRIC, MirrorKind.ENVIRONMENT}),
    MirrorStage.PUBLICATION: frozenset({MirrorKind.DOC, MirrorKind.RESULT, MirrorKind.METRIC, MirrorKind.ENVIRONMENT}),
}


@dataclass(frozen=True, slots=True)
class ProjectionLineage:
    """Cross-projection binding shared by PLAN, Dashboard, Linear and MLflow."""

    plan_sha256: str
    phase_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    gate_ids: tuple[str, ...]
    linear_issue_ids: tuple[str, ...]
    dashboard_content_id: str | None = None
    schema_version: str = "myis.projection-binding.v1"

    def validate(self) -> None:
        if self.schema_version != "myis.projection-binding.v1":
            raise MirrorValidationError("projection lineage schema_version is invalid")
        if not _SHA256_RE.fullmatch(self.plan_sha256):
            raise MirrorValidationError("projection lineage plan_sha256 must be SHA-256")
        for label, values in (
            ("phase_ids", self.phase_ids),
            ("task_ids", self.task_ids),
            ("gate_ids", self.gate_ids),
        ):
            if values != tuple(sorted(set(values))):
                raise MirrorValidationError(f"projection lineage {label} must be sorted and unique")
        if len(self.linear_issue_ids) != len(set(self.linear_issue_ids)):
            raise MirrorValidationError("projection lineage Linear issue IDs must be unique")
        if len(self.linear_issue_ids) != len(self.task_ids):
            raise MirrorValidationError("projection lineage requires one Linear issue ID per Task ID")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9]*", value) for value in self.phase_ids):
            raise MirrorValidationError("projection lineage contains an invalid Phase ID")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9]*\.[0-9]+", value) for value in self.task_ids):
            raise MirrorValidationError("projection lineage contains an invalid Task ID")
        if any(not re.fullmatch(r"G[0-8]", value) for value in self.gate_ids):
            raise MirrorValidationError("projection lineage contains an invalid Gate ID")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+", value) for value in self.linear_issue_ids):
            raise MirrorValidationError("projection lineage contains an invalid Linear issue ID")
        if self.dashboard_content_id is not None and not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]+", self.dashboard_content_id
        ):
            raise MirrorValidationError("projection lineage Dashboard content ID is invalid")

    def tags(self) -> dict[str, str]:
        self.validate()
        return {
            "projection_schema_version": self.schema_version,
            "plan_sha256": self.plan_sha256.lower(),
            "phase_ids": ",".join(self.phase_ids) or "not_applicable",
            "task_ids": ",".join(self.task_ids) or "not_applicable",
            "gate_ids": ",".join(self.gate_ids) or "not_applicable",
            "linear_issue_ids": ",".join(self.linear_issue_ids) or "not_applicable",
            "dashboard_content_id": self.dashboard_content_id or "not_applicable",
        }


@dataclass(frozen=True, slots=True)
class MirrorArtifact:
    """One explicitly selected, validated and redacted canonical file."""

    path: Path
    kind: MirrorKind
    canonical_root: Path
    sha256: str
    validated: bool = True
    redacted: bool = True
    artifact_name: str | None = None

    @classmethod
    def from_path(
        cls,
        path: Path,
        *,
        kind: MirrorKind,
        canonical_root: Path,
        validated: bool = True,
        redacted: bool = True,
        artifact_name: str | None = None,
    ) -> "MirrorArtifact":
        if path.is_symlink():
            raise MirrorValidationError("MLflow mirror rejects symlink artifacts")
        resolved = path.resolve(strict=True)
        return cls(
            path=resolved,
            kind=kind,
            canonical_root=canonical_root.resolve(strict=True),
            sha256=hashlib.sha256(resolved.read_bytes()).hexdigest(),
            validated=validated,
            redacted=redacted,
            artifact_name=artifact_name,
        )

    def validate(self) -> None:
        root = self.canonical_root.resolve(strict=True)
        path = self.path.resolve(strict=True)
        if not path.is_file() or path.is_symlink():
            raise MirrorValidationError("MLflow mirror accepts regular non-symlink files only")
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise MirrorValidationError("mirror artifact is outside its canonical root") from exc
        if not self.validated or not self.redacted:
            raise MirrorValidationError("mirror artifacts must be validated and redacted")
        if path.suffix.lower() not in _TEXT_SUFFIXES:
            raise MirrorValidationError(f"artifact type is not allowlisted: {path.suffix or '<none>'}")
        if path.suffix.lower() == ".pdf" or path.read_bytes()[:5] == b"%PDF-":
            raise MirrorValidationError("PDF content is never mirrored to MLflow")
        relative = path.relative_to(root).as_posix()
        if _FORBIDDEN_PATH_RE.search(relative):
            raise MirrorValidationError(f"protected artifact path is forbidden: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if not _SHA256_RE.fullmatch(self.sha256) or actual.lower() != self.sha256.lower():
            raise MirrorValidationError("artifact SHA-256 does not match current bytes")
        _scan_content(path, self.kind)

    @property
    def relative_path(self) -> str:
        return self.path.resolve().relative_to(self.canonical_root.resolve()).as_posix()


@dataclass(frozen=True, slots=True)
class MirrorSpec:
    """Identity and authority binding for one projection run."""

    stage: MirrorStage
    run_name: str
    git_commit: str
    canonical_source_sha256: str
    program_id: str = PROGRAM_ID
    display_name: str = DISPLAY_NAME
    protocol_version: str = PROTOCOL_VERSION
    research_version: str = RESEARCH_VERSION
    track: str | None = None
    arm: str | None = None
    phase: str | None = None
    data_role: str | None = None
    tags: Mapping[str, str] = field(default_factory=dict)
    parameters: Mapping[str, str | int | float | bool] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)
    projection: ProjectionLineage | None = None

    def validate(self, artifacts: Sequence[MirrorArtifact]) -> None:
        if (
            self.program_id != PROGRAM_ID
            or self.display_name != DISPLAY_NAME
            or self.protocol_version != PROTOCOL_VERSION
            or self.research_version != RESEARCH_VERSION
        ):
            raise MirrorValidationError("mirror identity must be myIS Research protocol 1.0")
        if not self.run_name.strip() or not self.git_commit.strip():
            raise MirrorValidationError("run_name and git_commit are required")
        if not _SHA256_RE.fullmatch(self.canonical_source_sha256):
            raise MirrorValidationError("canonical_source_sha256 must be SHA-256")
        if self.stage == MirrorStage.BOOTSTRAP and (artifacts or self.metrics):
            raise MirrorValidationError("bootstrap runs cannot contain artifacts or scientific metrics")
        if self.stage == MirrorStage.BOOTSTRAP:
            if self.tags.get("scientific_run") != "false":
                raise MirrorValidationError("bootstrap scientific_run tag must be false")
            if self.tags.get("dataset_access") != "none":
                raise MirrorValidationError("bootstrap dataset_access tag must be none")
            if self.parameters.get("artifact_count") != 0:
                raise MirrorValidationError("bootstrap artifact_count must be zero")
            if self.parameters.get("scientific_metric_count") != 0:
                raise MirrorValidationError("bootstrap scientific_metric_count must be zero")
        allowed = _STAGE_KINDS[self.stage]
        disallowed = sorted({artifact.kind.value for artifact in artifacts if artifact.kind not in allowed})
        if disallowed:
            raise MirrorValidationError(f"artifact kinds are not allowed for {self.stage.value}: {disallowed}")
        if self.stage in {MirrorStage.BOOTSTRAP, MirrorStage.CATALOG, MirrorStage.F1_G1_PREPARATION} and self.metrics:
            raise MirrorValidationError("metrics are forbidden in non-scientific mirror stages")
        if self.stage == MirrorStage.F1_G1_PREPARATION:
            if artifacts:
                raise MirrorValidationError("F1/G1 preparation mirrors metadata only")
            if self.track != "C" or self.arm != "G1_PREPARATION" or self.phase != "F1":
                raise MirrorValidationError("F1/G1 preparation lineage must bind C/G1_PREPARATION/F1")
            if self.data_role != "preparation":
                raise MirrorValidationError("F1/G1 preparation data role must be preparation")
            if self.tags.get("scientific_run") != "false":
                raise MirrorValidationError("F1/G1 preparation must declare scientific_run=false")
        active_stages = {MirrorStage.TRACK_C, MirrorStage.TRACK_S, MirrorStage.JOINT, MirrorStage.PUBLICATION}
        if self.stage in active_stages:
            required = {
                "track": self.track,
                "arm": self.arm,
                "phase": self.phase,
                "data_role": self.data_role,
            }
            missing = sorted(key for key, value in required.items() if not isinstance(value, str) or not value.strip())
            if missing:
                raise MirrorValidationError(f"active mirror stages require lineage fields: {', '.join(missing)}")
        if self.stage == MirrorStage.TRACK_C and self.track != "C":
            raise MirrorValidationError("track-c mirrors require track C")
        if self.stage == MirrorStage.TRACK_S and self.track != "S":
            raise MirrorValidationError("track-s mirrors require track S")
        allowed_tracks = {"C", "S", "joint", "publication"}
        if self.track is not None and self.track not in allowed_tracks:
            raise MirrorValidationError("mirror track must be an active track or aggregate projection")
        if _RESERVED_TAGS.intersection(self.tags):
            raise MirrorValidationError("caller tags cannot override reserved mirror lineage tags")
        if self.projection is not None:
            self.projection.validate()
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))
            for value in self.metrics.values()
        ):
            raise MirrorValidationError("metrics must be finite numeric values")
        _validate_metadata(self.tags)
        _validate_metadata(self.parameters)
        _validate_metadata(self.metrics)
        projection_keys = [f"{artifact.kind.value}/{artifact.relative_path}" for artifact in artifacts]
        if len(projection_keys) != len(set(projection_keys)):
            raise MirrorValidationError("duplicate mirror artifact projection path")
        for artifact in artifacts:
            artifact.validate()

    def mirror_key(self, artifacts: Sequence[MirrorArtifact]) -> str:
        body = {
            "stage": self.stage.value,
            "run_name": self.run_name,
            "git_commit": self.git_commit,
            "canonical_source_sha256": self.canonical_source_sha256.lower(),
            "program_id": self.program_id,
            "display_name": self.display_name,
            "protocol_version": self.protocol_version,
            "research_version": self.research_version,
            "track": self.track,
            "arm": self.arm,
            "phase": self.phase,
            "data_role": self.data_role,
            "tags": dict(sorted(self.tags.items())),
            "parameters": dict(sorted(self.parameters.items())),
            "metrics": dict(sorted(self.metrics.items())),
            "projection": asdict(self.projection) if self.projection is not None else None,
            "artifacts": [
                {"kind": item.kind.value, "path": item.relative_path, "sha256": item.sha256.lower()}
                for item in sorted(artifacts, key=lambda value: (value.kind.value, value.relative_path))
            ],
        }
        payload = json.dumps(body, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class MirrorReceipt:
    receipt_id: str
    mirror_key: str
    status: str
    experiment_name: str
    recorded_at_utc: str
    canonical_source_sha256: str
    git_commit: str
    artifact_hashes: Mapping[str, str]
    mlflow_run_id: str | None = None
    reason: str | None = None
    error_type: str | None = None
    error_hash: str | None = None
    schema_version: str = RECEIPT_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MirrorBackend(Protocol):
    """Small injectable boundary used by offline tests and the MLflow adapter."""

    def ensure_experiments(self, names: Sequence[str], artifact_root: Path) -> None: ...

    def find_run(self, experiment_name: str, mirror_key: str) -> str | None: ...

    def log_run(
        self,
        *,
        experiment_name: str,
        run_name: str,
        tags: Mapping[str, str],
        parameters: Mapping[str, str | int | float | bool],
        metrics: Mapping[str, float],
        artifacts: Sequence[MirrorArtifact],
    ) -> str: ...

    def close(self) -> None: ...


class LocalMLflowBackend:
    """MLflow adapter; imported lazily so canonical bundle creation stays offline."""

    def __init__(self, store_root: Path):
        try:
            import mlflow
        except ImportError as exc:
            raise RuntimeError("MLflow is not installed; install the locked tracking extra") from exc
        self.mlflow = mlflow
        self.store_root = store_root.resolve()
        database = self.store_root / "database" / "mlflow.db"
        database.parent.mkdir(parents=True, exist_ok=True)
        (self.store_root / "artifacts").mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(f"sqlite:///{database.resolve().as_posix()}")

    def ensure_experiments(self, names: Sequence[str], artifact_root: Path) -> None:
        artifact_root.mkdir(parents=True, exist_ok=True)
        for name in names:
            if self.mlflow.get_experiment_by_name(name) is None:
                self.mlflow.create_experiment(name, artifact_location=(artifact_root / name).resolve().as_uri())

    def find_run(self, experiment_name: str, mirror_key: str) -> str | None:
        experiment = self.mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            return None
        escaped = mirror_key.replace("'", "''")
        runs = self.mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"tags.mirror_key = '{escaped}'",
            max_results=1,
            output_format="list",
        )
        return runs[0].info.run_id if runs else None

    def log_run(
        self,
        *,
        experiment_name: str,
        run_name: str,
        tags: Mapping[str, str],
        parameters: Mapping[str, str | int | float | bool],
        metrics: Mapping[str, float],
        artifacts: Sequence[MirrorArtifact],
    ) -> str:
        experiment = self.mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise RuntimeError(f"MLflow experiment was not initialized: {experiment_name}")
        with self.mlflow.start_run(experiment_id=experiment.experiment_id, run_name=run_name, tags=dict(tags)) as run:
            if parameters:
                self.mlflow.log_params(dict(parameters))
            for name, value in metrics.items():
                self.mlflow.log_metric(name, float(value))
            for artifact in artifacts:
                parent = Path(artifact.relative_path).parent.as_posix()
                destination = f"mirror/{artifact.kind.value}"
                if parent != ".":
                    destination = f"{destination}/{parent}"
                self.mlflow.log_artifact(str(artifact.path), artifact_path=destination)
            return run.info.run_id

    def close(self) -> None:
        try:
            from mlflow.tracking._tracking_service.utils import _get_store

            store = _get_store()
            if hasattr(store, "_dispose_engine"):
                store._dispose_engine()
        except Exception:
            # Closing an optional private MLflow engine hook must not invalidate
            # an otherwise complete canonical run or receipt.
            return


class MLflowMirror:
    """Serialize, validate and mirror canonical files to the local store."""

    def __init__(
        self,
        store_root: Path | None = None,
        *,
        backend: MirrorBackend | None = None,
        lock_timeout_seconds: float = 30.0,
    ):
        self.store_root = default_store(store_root)
        self.backend = backend
        self.lock_timeout_seconds = lock_timeout_seconds

    def sync(
        self,
        spec: MirrorSpec,
        artifacts: Sequence[MirrorArtifact] = (),
        *,
        receipt_dir: Path | None = None,
    ) -> MirrorReceipt:
        selected = tuple(artifacts)
        spec.validate(selected)
        mirror_key = spec.mirror_key(selected)
        receipt_root = receipt_dir or self.store_root / "receipts" / "mlflow"
        receipt_path = receipt_root / f"mlflow-mirror-{mirror_key}.json"
        if receipt_path.exists():
            return _load_receipt(receipt_path, mirror_key)

        artifact_hashes = {
            f"{item.kind.value}/{item.relative_path}": item.sha256.lower()
            for item in sorted(selected, key=lambda value: (value.kind.value, value.relative_path))
        }
        backend = self.backend
        try:
            with _serialized_writer(self.store_root, self.lock_timeout_seconds):
                backend = backend or LocalMLflowBackend(self.store_root)
                backend.ensure_experiments(EXPERIMENTS, self.store_root / "artifacts")
                existing_run = backend.find_run(spec.stage.experiment_name, mirror_key)
                run_id = existing_run or backend.log_run(
                    experiment_name=spec.stage.experiment_name,
                    run_name=spec.run_name,
                    tags={
                        **dict(spec.tags),
                        **(
                            spec.projection.tags()
                            if spec.projection is not None
                            else {
                                "projection_schema_version": "not_applicable",
                                "plan_sha256": "not_applicable",
                                "phase_ids": spec.phase or "not_applicable",
                                "task_ids": "not_applicable",
                                "gate_ids": "not_applicable",
                                "linear_issue_ids": "not_applicable",
                                "dashboard_content_id": "not_applicable",
                            }
                        ),
                        "program_id": spec.program_id,
                        "display_name": spec.display_name,
                        "protocol_version": spec.protocol_version,
                        "research_version": spec.research_version,
                        "track": spec.track or "not_applicable",
                        "arm": spec.arm or "not_applicable",
                        "phase": spec.phase or "not_applicable",
                        "data_role": spec.data_role or "not_applicable",
                        "stage": spec.stage.value,
                        "mirror_key": mirror_key,
                        "canonical_source_sha256": spec.canonical_source_sha256.lower(),
                        "git_commit": spec.git_commit,
                        "canonical_authority": "git-and-validated-artifacts",
                    },
                    parameters=spec.parameters,
                    metrics=spec.metrics,
                    artifacts=selected,
                )
            receipt = MirrorReceipt(
                receipt_id=mirror_key,
                mirror_key=mirror_key,
                status="already_synced" if existing_run else "synced",
                experiment_name=spec.stage.experiment_name,
                recorded_at_utc=_now(),
                canonical_source_sha256=spec.canonical_source_sha256.lower(),
                git_commit=spec.git_commit,
                artifact_hashes=artifact_hashes,
                mlflow_run_id=run_id,
            )
        except Exception as error:
            receipt = MirrorReceipt(
                receipt_id=mirror_key,
                mirror_key=mirror_key,
                status="sync_deferred",
                experiment_name=spec.stage.experiment_name,
                recorded_at_utc=_now(),
                canonical_source_sha256=spec.canonical_source_sha256.lower(),
                git_commit=spec.git_commit,
                artifact_hashes=artifact_hashes,
                reason="mlflow_error",
                error_type=type(error).__name__,
                error_hash=hashlib.sha256(str(error).encode("utf-8")).hexdigest(),
            )
        finally:
            if backend is not None:
                try:
                    backend.close()
                except Exception:
                    pass
        _write_receipt_once(receipt_path, receipt)
        return receipt


def default_store(root: Path | None = None) -> Path:
    """Resolve the persistent store outside the Git repository."""

    if root is not None:
        return _assert_store_outside_git(root.expanduser().resolve())
    configured = os.environ.get("MYIS_MLFLOW_STORE")
    if configured:
        return _assert_store_outside_git(Path(configured).expanduser().resolve())
    current = Path.cwd().resolve()
    for ancestor in (current, *current.parents):
        numbered = ancestor / "01_Stores" / "00_myIS" / "mlflow"
        legacy = ancestor / "Stores" / "myIS" / "mlflow"
        if numbered.parent.is_dir():
            return _assert_store_outside_git(numbered)
        if legacy.parent.is_dir():
            return _assert_store_outside_git(legacy)
    raise RuntimeError("Cannot locate shared MLflow store; set MYIS_MLFLOW_STORE")


def rebuild_plan(canonical_artifacts: Sequence[MirrorArtifact], *, store_root: Path) -> dict[str, Any]:
    """Return a non-mutating recovery plan sourced only from canonical files."""

    artifacts = tuple(canonical_artifacts)
    for artifact in artifacts:
        artifact.validate()
    return {
        "schema_version": "myis.mlflow-rebuild-plan.v1",
        "authority": "git-and-validated-artifacts",
        "store_root": str(store_root.resolve()),
        "action": "quarantine-corrupt-store-then-replay-mirror-specs",
        "automatic_repair": False,
        "artifact_hashes": {
            f"{item.kind.value}/{item.relative_path}": item.sha256.lower()
            for item in sorted(artifacts, key=lambda value: (value.kind.value, value.relative_path))
        },
    }


def _scan_content(path: Path, kind: MirrorKind) -> None:
    text = path.read_text(encoding="utf-8-sig")
    if _SECRET_VALUE_RE.search(text):
        raise MirrorValidationError("artifact appears to contain a credential or secret")
    if kind not in {MirrorKind.RESULT, MirrorKind.METRIC, MirrorKind.ENVIRONMENT}:
        return
    suffix = path.suffix.lower()
    if suffix == ".json":
        value = json.loads(text)
        _scan_structured_value(value)
    elif suffix == ".jsonl":
        for line in text.splitlines():
            if line.strip():
                _scan_structured_value(json.loads(line))
    elif suffix == ".csv":
        reader = csv.reader(text.splitlines())
        header = next(reader, [])
        for name in header:
            if _FORBIDDEN_STRUCTURED_KEY_RE.search(name):
                raise MirrorValidationError(f"protected structured field is forbidden: {name}")
    elif suffix in {".yaml", ".yml"}:
        import yaml

        _scan_structured_value(yaml.safe_load(text))
    elif suffix == ".toml":
        _scan_structured_value(tomllib.loads(text))


def _scan_structured_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()
            is_commitment = normalized_key.endswith(("_hash", "_sha256"))
            if _FORBIDDEN_STRUCTURED_KEY_RE.search(str(key)) and not is_commitment:
                raise MirrorValidationError(f"protected structured field is forbidden: {key}")
            _scan_structured_value(item)
    elif isinstance(value, list):
        for item in value:
            _scan_structured_value(item)


def _validate_metadata(value: Mapping[str, Any]) -> None:
    for key, item in value.items():
        normalized_key = str(key).lower()
        is_commitment = normalized_key.endswith(("_hash", "_sha256"))
        if _FORBIDDEN_STRUCTURED_KEY_RE.search(normalized_key) and not is_commitment:
            raise MirrorValidationError(f"protected MLflow metadata field is forbidden: {key}")
        if _SECRET_VALUE_RE.search(str(item)):
            raise MirrorValidationError(f"MLflow metadata appears to contain a secret: {key}")


def _assert_store_outside_git(path: Path) -> Path:
    for ancestor in (path, *path.parents):
        marker = ancestor / ".git"
        valid_git_marker = marker.is_file() or (marker.is_dir() and (marker / "HEAD").is_file())
        if valid_git_marker:
            raise MirrorValidationError("persistent MLflow store must be outside the Git worktree")
    return path


@contextmanager
def _serialized_writer(store_root: Path, timeout_seconds: float) -> Iterator[None]:
    store_root.mkdir(parents=True, exist_ok=True)
    lock = store_root / ".mlflow-writer.lock"
    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    while True:
        try:
            descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError("local MLflow SQLite writer is already active")
            time.sleep(0.05)
    try:
        os.write(descriptor, json.dumps({"pid": os.getpid(), "created_at_utc": _now()}).encode("utf-8"))
        os.close(descriptor)
        yield
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        lock.unlink(missing_ok=True)


def _write_receipt_once(path: Path, receipt: MirrorReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(receipt.as_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        existing = _load_receipt(path, receipt.mirror_key)
        if existing.as_dict() != receipt.as_dict():
            raise RuntimeError("conflicting immutable MLflow receipt already exists")


def _load_receipt(path: Path, mirror_key: str) -> MirrorReceipt:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != RECEIPT_SCHEMA or value.get("mirror_key") != mirror_key:
        raise RuntimeError("invalid or conflicting MLflow mirror receipt")
    return MirrorReceipt(**value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
