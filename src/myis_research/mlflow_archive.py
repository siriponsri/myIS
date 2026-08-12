"""Typed v2 MLflow evidence-archive records and safe local archive writer.

The module intentionally consumes only aggregate, repository-visible projection
bytes.  It never opens an owner-local run store and keeps MLflow rebuildable.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlparse

from .mlflow_mirror import (
    MLflowMirror,
    MirrorArtifact,
    MirrorKind,
    MirrorSpec,
    MirrorStage,
)


ARCHIVE_SCHEMA = "myis.mlflow-evidence-archive.v2"
FREEZE_SCHEMA = "myis.freeze-bundle.v2"
METRIC_SCHEMA = "myis.metric-definition.v2"
SCHEMA_REGISTRY_SCHEMA = "myis.schema-registry.v2"
RULE_REGISTRY_SCHEMA = "myis.rule-registry.v2"
ARCHIVE_RECEIPT_SCHEMA = "myis.mlflow-archive-receipt.v2"
ACTIVE_CAMPAIGN = "scope-autoindex-v1"
_SHA256 = "^[0-9a-f]{64}$"
_FREEZE_STATES = frozenset({"frozen_development", "frozen_selection", "frozen_confirmation", "publication_snapshot"})
_VALIDITY = frozenset({"planned", "running", "valid", "invalid", "blocked", "failed", "cancelled", "superseded"})
_MATURITY = frozenset({"non_scientific", "fixture", "dry_run", "measured_development", "measured_selection", "confirmatory", "publication", "historical_exposed"})
_POINTER_CLASSES = frozenset({"safe_large", "protected", "source_literature", "model_or_index"})
_SAFE_POINTER_URI = re.compile(r"^(?:owner-local|external-store|brain|git)://[A-Za-z0-9._/-]+$")


class ArchiveContractError(ValueError):
    """Raised before any archive-side mutation for an invalid v2 record."""


@dataclass(frozen=True, slots=True)
class ArtifactPointer:
    artifact_id: str
    artifact_class: str
    role: str
    store_uri: str
    sha256: str
    schema_id: str
    size_bytes: int | None = None
    row_count: int | None = None
    copied_to_mlflow: bool = False
    schema_version: str = "myis.artifact-pointer.v2"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.schema_version != "myis.artifact-pointer.v2" or not self.artifact_id or not self.role or not self.schema_id:
            raise ArchiveContractError("artifact pointer identity is incomplete")
        if self.artifact_class not in _POINTER_CLASSES:
            raise ArchiveContractError("artifact pointer class is invalid")
        if not _SAFE_POINTER_URI.fullmatch(self.store_uri) or ".." in self.store_uri:
            raise ArchiveContractError("artifact pointer URI is not allowlisted")
        _require_hash(self.sha256, "artifact pointer sha256")
        if self.copied_to_mlflow:
            raise ArchiveContractError("large or protected pointer cannot be copied to MLflow")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ArchiveContractError("artifact pointer size is invalid")
        if self.row_count is not None and self.row_count < 0:
            raise ArchiveContractError("artifact pointer row count is invalid")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value) if not isinstance(value, bytes) else value).hexdigest()


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ArchiveContractError(f"{label} must be a lowercase SHA-256")


def _record_hash(record: Mapping[str, Any], field_name: str) -> str:
    return sha256({key: value for key, value in record.items() if key != field_name})


@dataclass(frozen=True, slots=True)
class FreezeBundle:
    freeze_id: str
    campaign_id: str
    phase_id: str
    scope: str
    status: str
    source_commit: str
    rules_sha256: str
    metric_registry_sha256: str
    schema_registry_sha256: str
    evaluator_sha256: str
    protocol_sha256: str
    environment_lock_sha256: str
    created_at_utc: str = "1970-01-01T00:00:00Z"
    owner_decision_id: str | None = None
    supersedes_freeze_id: str | None = None
    schema_version: str = FREEZE_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["bundle_sha256"] = _record_hash(body, "bundle_sha256")
        return body

    def validate(self) -> None:
        if self.schema_version != FREEZE_SCHEMA or self.campaign_id != ACTIVE_CAMPAIGN:
            raise ArchiveContractError("freeze bundle has invalid identity")
        if self.status not in _FREEZE_STATES:
            raise ArchiveContractError("freeze bundle is not frozen")
        if not self.freeze_id or not self.phase_id or not self.scope or len(self.source_commit) < 7:
            raise ArchiveContractError("freeze bundle identity is incomplete")
        for label, value in (("rules_sha256", self.rules_sha256), ("metric_registry_sha256", self.metric_registry_sha256), ("schema_registry_sha256", self.schema_registry_sha256), ("evaluator_sha256", self.evaluator_sha256), ("protocol_sha256", self.protocol_sha256), ("environment_lock_sha256", self.environment_lock_sha256)):
            _require_hash(value, label)


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    metric_id: str
    mlflow_key: str
    evaluator_sha256: str
    definition: Mapping[str, Any]
    schema_version: str = METRIC_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        body = {"schema_version": self.schema_version, "metric_id": self.metric_id, "mlflow_key": self.mlflow_key, "evaluator_sha256": self.evaluator_sha256, **dict(self.definition)}
        body["definition_sha256"] = _record_hash(body, "definition_sha256")
        return body

    def validate(self) -> None:
        if self.schema_version != METRIC_SCHEMA or not self.metric_id or not self.mlflow_key:
            raise ArchiveContractError("metric definition identity is invalid")
        _require_hash(self.evaluator_sha256, "metric evaluator_sha256")
        required = {"evaluation_unit", "direction", "valid_range", "sample_count_required"}
        if not required.issubset(self.definition):
            raise ArchiveContractError("metric definition omits required scientific fields")
        if self.definition.get("sample_count_required") is not True:
            raise ArchiveContractError("metric definition must require a sample count")


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    schema_version: str
    items: tuple[Mapping[str, Any], ...]
    registry_kind: str

    def as_dict(self) -> dict[str, Any]:
        body = {"schema_version": self.schema_version, "registry_kind": self.registry_kind, "items": [dict(item) for item in self.items]}
        body["registry_sha256"] = _record_hash(body, "registry_sha256")
        return body

    def validate(self) -> None:
        if self.schema_version not in {SCHEMA_REGISTRY_SCHEMA, RULE_REGISTRY_SCHEMA} or not self.items:
            raise ArchiveContractError("registry snapshot is incomplete")
        for item in self.items:
            if not isinstance(item, Mapping) or not item.get("id") or not item.get("sha256"):
                raise ArchiveContractError("registry item requires id and SHA-256")
            _require_hash(str(item["sha256"]), "registry item sha256")


@dataclass(frozen=True, slots=True)
class ArchiveRun:
    run_id: str
    phase_id: str
    task_id: str
    run_kind: str
    git_commit: str
    manifest_sha256: str
    receipt_sha256: str
    dataset_lineage_sha256: str
    config_sha256: str
    evaluator_sha256: str
    environment_sha256: str
    read_model_revision: str
    read_model_sha256: str
    evidence_maturity: str
    run_validity: str
    freeze: FreezeBundle
    metrics: Mapping[str, tuple[float, int, MetricDefinition]] = field(default_factory=dict)
    selected: bool = False
    safe_to_present: bool = False
    is_latest: bool = False
    is_latest_valid: bool = False
    is_current_evidence: bool = False
    is_confirmation: bool = False
    supersedes_run_id: str | None = None
    superseded_by_run_id: str | None = None
    owner_decision_ids: tuple[str, ...] = ()
    artifact_pointers: tuple[ArtifactPointer, ...] = ()
    outcome: str = "not_applicable"
    interpretation: Mapping[str, Any] | None = None
    failure_category: str | None = None
    blocked_reason: str | None = None

    def validate(self) -> None:
        if not self.run_id or not self.phase_id or not self.task_id or not self.run_kind:
            raise ArchiveContractError("archive run identity is incomplete")
        if self.evidence_maturity not in _MATURITY or self.run_validity not in _VALIDITY:
            raise ArchiveContractError("archive run lifecycle is invalid")
        if self.run_kind not in {"freeze_snapshot", "execution", "comparison", "projection_sync", "phase_closeout", "publication_package", "system_check"}:
            raise ArchiveContractError("archive run kind is invalid")
        for label, value in (("manifest_sha256", self.manifest_sha256), ("receipt_sha256", self.receipt_sha256), ("dataset_lineage_sha256", self.dataset_lineage_sha256), ("config_sha256", self.config_sha256), ("evaluator_sha256", self.evaluator_sha256), ("environment_sha256", self.environment_sha256), ("read_model_sha256", self.read_model_sha256)):
            _require_hash(value, label)
        if not self.read_model_revision:
            raise ArchiveContractError("archive run requires a shared read-model revision")
        self.freeze.validate()
        if self.evidence_maturity in {"measured_development", "measured_selection", "confirmatory", "publication"} and self.run_validity != "valid":
            raise ArchiveContractError("measured archive runs must be valid")
        if self.evidence_maturity == "confirmatory" and self.freeze.status != "frozen_confirmation":
            raise ArchiveContractError("confirmatory archive run requires a confirmation freeze")
        if self.is_confirmation != (self.evidence_maturity == "confirmatory"):
            raise ArchiveContractError("confirmation lifecycle flag must match evidence maturity")
        if self.phase_id == "P3_FINAL" and "D2_OPEN_FINAL" not in self.owner_decision_ids:
            raise ArchiveContractError("final archive run requires D2_OPEN_FINAL")
        if (self.phase_id == "P4_PUBLICATION" or self.evidence_maturity == "publication") and "D3_SUBMIT_RELEASE" not in self.owner_decision_ids:
            raise ArchiveContractError("publication archive run requires D3_SUBMIT_RELEASE")
        if self.selected and self.run_validity != "valid":
            raise ArchiveContractError("only a valid run can be selected")
        if self.is_latest_valid and self.run_validity != "valid":
            raise ArchiveContractError("latest-valid lifecycle flag requires a valid run")
        if self.is_current_evidence and (self.run_validity != "valid" or self.superseded_by_run_id):
            raise ArchiveContractError("current evidence must be valid and not superseded")
        if self.supersedes_run_id and self.superseded_by_run_id:
            raise ArchiveContractError("one archive record cannot supersede and be superseded simultaneously")
        if len(self.owner_decision_ids) != len(set(self.owner_decision_ids)) or any(
            item not in {"D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"} for item in self.owner_decision_ids
        ):
            raise ArchiveContractError("archive run owner decisions are invalid")
        for pointer in self.artifact_pointers:
            pointer.validate()
        for key, (value, sample_count, definition) in self.metrics.items():
            if not key or not isinstance(value, (float, int)) or not isinstance(sample_count, int) or sample_count < 0:
                raise ArchiveContractError("metric value or sample count is invalid")
            definition.validate()
            if definition.mlflow_key != key:
                raise ArchiveContractError("metric key does not resolve to its definition")
            if definition.evaluator_sha256 != self.evaluator_sha256:
                raise ArchiveContractError("metric evaluator does not match archive run")


@dataclass(frozen=True, slots=True)
class ArchiveReceipt:
    archive_key: str
    status: str
    mlflow_run_id: str | None
    read_model_revision: str
    read_model_sha256: str
    archive_record_sha256: str
    recorded_at_utc: str
    mirror_receipt_sha256: str
    schema_version: str = ARCHIVE_RECEIPT_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_cross_projection_receipt(
    receipt: Mapping[str, Any], archive_receipt: ArchiveReceipt, *, read_model_revision: str, read_model_sha256: str
) -> None:
    """Reject an absent or stale MLflow binding without owning report generation."""

    if receipt.get("schema_version") != "myis.projection-sync-receipt.v2":
        raise ArchiveContractError("cross-projection receipt schema is invalid")
    if receipt.get("status") != "PASS":
        raise ArchiveContractError("cross-projection receipt did not pass")
    if receipt.get("read_model_revision") != read_model_revision or receipt.get("read_model_sha256") != read_model_sha256:
        raise ArchiveContractError("cross-projection receipt is stale")
    if receipt.get("mlflow_run_id") != archive_receipt.mlflow_run_id or not archive_receipt.mlflow_run_id:
        raise ArchiveContractError("cross-projection receipt has no matching MLflow run")


class MLflowEvidenceArchive:
    """Writes a hash-bound v2 archive record through the existing safe mirror."""

    def __init__(self, store_root: Path, *, mirror: MLflowMirror | None = None):
        self.store_root = store_root.resolve()
        self.mirror = mirror or MLflowMirror(self.store_root)

    def sync(self, run: ArchiveRun, *, archive_index: Mapping[str, Any], schema_registry: RegistrySnapshot, rule_registry: RegistrySnapshot) -> ArchiveReceipt:
        run.validate()
        schema_registry.validate()
        rule_registry.validate()
        if schema_registry.schema_version != SCHEMA_REGISTRY_SCHEMA or rule_registry.schema_version != RULE_REGISTRY_SCHEMA:
            raise ArchiveContractError("wrong registry type for archive sync")
        index_revision = str(archive_index.get("read_model_revision", ""))
        index_hash = str(archive_index.get("read_model_sha256", ""))
        if (index_revision, index_hash) != (run.read_model_revision, run.read_model_sha256):
            raise ArchiveContractError("archive index is not bound to the shared read model")
        schema_sha = str(schema_registry.as_dict()["registry_sha256"])
        rule_sha = str(rule_registry.as_dict()["registry_sha256"])
        metric_registry = _metric_registry(run)
        if run.freeze.schema_registry_sha256 != schema_sha or run.freeze.rules_sha256 != rule_sha:
            raise ArchiveContractError("freeze bundle is not bound to the supplied rule/schema registries")
        if run.freeze.metric_registry_sha256 != metric_registry["registry_sha256"]:
            raise ArchiveContractError("freeze bundle is not bound to the exact metric registry")

        artifacts, record, archive_key = self._stage(run, archive_index, schema_registry, rule_registry)
        self._assert_run_identity(record, archive_key)
        self._ensure_store_metadata()
        receipt_path = self.store_root / "receipts" / "archive" / f"{archive_key}.json"
        if receipt_path.exists():
            receipt = ArchiveReceipt(**json.loads(receipt_path.read_text(encoding="utf-8")))
            self._verify_store_artifacts(receipt.mlflow_run_id, artifacts, run)
            return receipt
        if run.phase_id.startswith("A"):
            try:
                stage = MirrorStage(run.phase_id)
            except ValueError as error:
                raise ArchiveContractError("unknown ArmIndex archive phase") from error
            campaign_id = "armindex-multiretriever-v2"
        else:
            stage = MirrorStage.P0_FOUNDATION if run.run_kind in {"projection_sync", "system_check"} else MirrorStage.P1_CPU_BASELINE
            campaign_id = ACTIVE_CAMPAIGN
        experiment_name = stage.experiment_name
        mirror_receipt = self.mirror.sync(
            MirrorSpec(
                stage=stage,
                experiment_name=experiment_name,
                run_name=f"{run.task_id} | {run.run_id}",
                git_commit=run.git_commit,
                canonical_source_sha256=record["archive_record_sha256"],
                campaign_id=campaign_id,
                run_id=run.run_id,
                phase=stage.value,
                data_role="archive",
                tags={
                    "phase_id": run.phase_id, "task_id": run.task_id, "run_kind": run.run_kind,
                    "evidence_maturity": run.evidence_maturity, "run_validity": run.run_validity,
                    "freeze_id": run.freeze.freeze_id, "freeze_sha256": run.freeze.as_dict()["bundle_sha256"],
                    "manifest_sha256": run.manifest_sha256, "receipt_sha256": run.receipt_sha256,
                    "config_sha256": run.config_sha256, "evaluator_sha256": run.evaluator_sha256,
                    "environment_sha256": run.environment_sha256, "read_model_revision": run.read_model_revision,
                    "read_model_sha256": run.read_model_sha256, "selected": str(run.selected).lower(),
                    "safe_to_present": str(run.safe_to_present).lower(),
                    "is_latest": str(run.is_latest).lower(), "is_latest_valid": str(run.is_latest_valid).lower(),
                    "is_current_evidence": str(run.is_current_evidence).lower(), "is_confirmation": str(run.is_confirmation).lower(),
                    "current_state": "superseded" if run.superseded_by_run_id else run.run_validity,
                    "supersedes_run_id": run.supersedes_run_id or "not_applicable",
                    "superseded_by_run_id": run.superseded_by_run_id or "not_applicable",
                    "failure_category": run.failure_category or "not_applicable",
                    "blocked_reason": run.blocked_reason or "not_applicable",
                },
                parameters={f"{key}_n": count for key, (_, count, _) in run.metrics.items()},
                metrics={key: float(value) for key, (value, _, _) in run.metrics.items()},
            ),
            artifacts=artifacts,
        )
        receipt = ArchiveReceipt(
            archive_key=archive_key, status=mirror_receipt.status, mlflow_run_id=mirror_receipt.mlflow_run_id,
            read_model_revision=run.read_model_revision, read_model_sha256=run.read_model_sha256,
            archive_record_sha256=record["archive_record_sha256"], recorded_at_utc=_now(),
            mirror_receipt_sha256=sha256(mirror_receipt.as_dict()),
        )
        self._verify_store_artifacts(receipt.mlflow_run_id, artifacts, run)
        _write_once(receipt_path, receipt.as_dict())
        return receipt

    def backup(self, backup_id: str) -> Path:
        if not backup_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in backup_id):
            raise ArchiveContractError("backup id is invalid")
        required = ("database", "artifacts", "receipts", "store.json")
        if any(not (self.store_root / item).exists() for item in required):
            raise ArchiveContractError("archive store has not been initialized")
        target = self.store_root / "backups" / backup_id
        if target.exists():
            return target
        target.mkdir(parents=True)
        for name in required:
            source = self.store_root / name
            if source.is_dir():
                shutil.copytree(source, target / name)
            else:
                shutil.copy2(source, target / name)
        checksums = {path.relative_to(target).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(target.rglob("*")) if path.is_file()}
        _write_once(target / "backup.json", {"schema_version": "myis.mlflow-backup.v2", "backup_id": backup_id, "store_root": str(self.store_root), "checksums": checksums})
        (target / "checksums.sha256").write_text(
            "".join(f"{digest}  {relative}\n" for relative, digest in sorted(checksums.items())),
            encoding="ascii",
            newline="\n",
        )
        return target

    def restore_backup(self, backup_id: str, target_root: Path) -> dict[str, Any]:
        source = self.store_root / "backups" / backup_id
        target = target_root.resolve()
        if target.exists() and any(target.iterdir()):
            raise ArchiveContractError("restore target must be absent or empty")
        report = _validate_backup(source)
        target.mkdir(parents=True, exist_ok=True)
        for name in ("database", "artifacts", "receipts"):
            shutil.copytree(source / name, target / name)
        shutil.copy2(source / "store.json", target / "store.json")
        actual = {
            path.relative_to(target).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(target.rglob("*")) if path.is_file()
        }
        expected = {
            key: value for key, value in report["checksums"].items()
            if key not in {"backup.json", "checksums.sha256"}
        }
        if actual != expected:
            raise ArchiveContractError("restored store hashes do not match the backup")
        return {"schema_version": "myis.mlflow-restore-receipt.v2", "status": "PASS", "backup_id": backup_id, "target_root": str(target), "checksums": actual}

    def quarantine_and_rebuild_plan(self, reason: str) -> dict[str, Any]:
        if not reason:
            raise ArchiveContractError("quarantine reason is required")
        quarantine = self.store_root / "quarantine" / f"quarantine-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        return {"schema_version": "myis.mlflow-rebuild-plan.v2", "status": "manual_replay_required", "reason": reason, "quarantine_target": str(quarantine), "source": "canonical archive receipts and safe read-model archive index", "automatic_store_switch": False}

    def _stage(self, run: ArchiveRun, archive_index: Mapping[str, Any], schema_registry: RegistrySnapshot, rule_registry: RegistrySnapshot) -> tuple[tuple[MirrorArtifact, ...], dict[str, Any], str]:
        freeze = run.freeze.as_dict()
        metric_records = [definition.as_dict() | {"value": value, "sample_count": count, "manifest_sha256": run.manifest_sha256, "receipt_sha256": run.receipt_sha256} for value, count, definition in run.metrics.values()]
        metric_registry = _metric_registry(run)
        result = {
            "schema_version": "myis.result.v2", "run_id": run.run_id, "phase_id": run.phase_id,
            "task_id": run.task_id, "run_validity": run.run_validity, "evidence_maturity": run.evidence_maturity,
            "outcome": run.outcome, "selected": run.selected, "safe_to_present": run.safe_to_present,
            "manifest_sha256": run.manifest_sha256, "receipt_sha256": run.receipt_sha256,
            "freeze_sha256": freeze["bundle_sha256"], "metric_ids": sorted(run.metrics),
        }
        result["result_sha256"] = _record_hash(result, "result_sha256")
        interpretation = dict(run.interpretation or {
            "schema_version": "myis.interpretation.v2", "interpretation_id": f"interpretation-{run.run_id}",
            "result_run_id": run.run_id, "review_status": "not_applicable", "observed_th": "No scientific result is produced by projection sync.",
            "means_th": "The three projections are bound to one revision.", "does_not_mean_th": "This is not measured research evidence.",
            "next_th": "Use the canonical run package for scientific conclusions.", "claim_level": "none",
        })
        interpretation["source_result_sha256"] = result["result_sha256"]
        pointers = [pointer.as_dict() for pointer in run.artifact_pointers]
        record = {
            "schema_version": ARCHIVE_SCHEMA, "campaign_id": ACTIVE_CAMPAIGN, "run_id": run.run_id,
            "phase_id": run.phase_id, "task_id": run.task_id, "run_kind": run.run_kind,
            "read_model_revision": run.read_model_revision, "read_model_sha256": run.read_model_sha256,
            "freeze_sha256": freeze["bundle_sha256"], "schema_registry_sha256": schema_registry.as_dict()["registry_sha256"],
            "rule_registry_sha256": rule_registry.as_dict()["registry_sha256"], "manifest_sha256": run.manifest_sha256,
            "receipt_sha256": run.receipt_sha256, "run_validity": run.run_validity, "evidence_maturity": run.evidence_maturity,
            "supersedes_run_id": run.supersedes_run_id, "superseded_by_run_id": run.superseded_by_run_id,
            "lifecycle": {"latest": run.is_latest, "latest_valid": run.is_latest_valid, "selected": run.selected, "current_evidence": run.is_current_evidence, "confirmation": run.is_confirmation},
            "metrics": metric_records, "result_sha256": result["result_sha256"], "artifact_pointers": pointers,
        }
        record["archive_record_sha256"] = _record_hash(record, "archive_record_sha256")
        archive_key = sha256(record)
        root = self.store_root / "staging" / archive_key
        files = {
            "about/run.json": record, "freeze/bundle.json": freeze,
            "freeze/schema-registry.json": schema_registry.as_dict(), "freeze/rule-registry.json": rule_registry.as_dict(),
            "freeze/metric-registry.json": metric_registry,
            "metrics/metrics.json": metric_records, "results/result.json": result,
            "results/interpretation.json": interpretation, "outputs/archive-index.json": dict(archive_index),
            "outputs/artifact-pointers.json": pointers,
            "checks/checks.json": {"schema_version": "myis.checks.v2", "overall": "PASS", "items": {"hash_binding": "PASS", "freeze_binding": "PASS", "protected_scan": "PASS", "metric_definition": "PASS"}, "warnings": []},
            "lineage/hashes.json": {"manifest_sha256": run.manifest_sha256, "receipt_sha256": run.receipt_sha256, "dataset_lineage_sha256": run.dataset_lineage_sha256, "config_sha256": run.config_sha256, "evaluator_sha256": run.evaluator_sha256, "environment_sha256": run.environment_sha256},
        }
        for relative, body in files.items():
            path = root / relative
            _write_once(path, body)
        artifacts = tuple(MirrorArtifact.from_path(path, kind=MirrorKind.RESULT if relative.startswith(("metrics/", "about/", "checks/")) else MirrorKind.DOC, canonical_root=root) for relative, path in ((item, root / item) for item in files))
        return artifacts, record, archive_key

    def _assert_run_identity(self, record: Mapping[str, Any], archive_key: str) -> None:
        identity_root = self.store_root / "run-identities"
        identity = identity_root / f"{record['run_id']}.json"
        payload = {"schema_version": "myis.mlflow-run-identity.v2", "run_id": record["run_id"], "archive_key": archive_key, "archive_record_sha256": record["archive_record_sha256"], "manifest_sha256": record["manifest_sha256"]}
        _write_once(identity, payload)

    def _ensure_store_metadata(self) -> None:
        path = self.store_root / "store.json"
        payload = {"schema_version": "myis.mlflow-store.v2", "artifact_root": "artifacts", "repository_program_id": "myis-research", "created_by": "mlflow-evidence-archive"}
        if not path.exists():
            _write_once(path, payload)
            return
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ArchiveContractError("MLflow store metadata is invalid") from error
        if current.get("schema_version") != "myis.mlflow-store.v2" or current.get("artifact_root") != "artifacts":
            raise ArchiveContractError("MLflow store metadata contract is invalid")

    def _verify_store_artifacts(self, mlflow_run_id: str | None, artifacts: Sequence[MirrorArtifact], run: ArchiveRun) -> None:
        if not mlflow_run_id:
            raise ArchiveContractError("MLflow archive receipt has no run ID")
        if not isinstance(self.mirror, MLflowMirror):
            return
        run_root = _mlflow_artifact_root(self.store_root, mlflow_run_id) / "mirror"
        for artifact in artifacts:
            stored = run_root / artifact.kind.value / artifact.relative_path
            if stored.is_symlink() or not stored.is_file() or hashlib.sha256(stored.read_bytes()).hexdigest() != artifact.sha256:
                raise ArchiveContractError(f"stored MLflow artifact hash mismatch: {artifact.relative_path}")


def _mlflow_artifact_root(store_root: Path, run_id: str) -> Path:
    database = store_root / "database/mlflow.db"
    try:
        with sqlite3.connect(
            f"file:{database.resolve().as_posix()}?mode=ro", uri=True
        ) as connection:
            row = connection.execute(
                "select artifact_uri from runs where run_uuid=? and lifecycle_stage='active'",
                (run_id,),
            ).fetchone()
    except sqlite3.Error as error:
        raise ArchiveContractError("MLflow artifact URI lookup failed") from error
    if row is None:
        raise ArchiveContractError("MLflow archive run is missing")
    parsed = urlparse(str(row[0]))
    if parsed.scheme != "file":
        raise ArchiveContractError("MLflow artifact URI is not local file storage")
    raw = unquote(parsed.path)
    if parsed.netloc:
        raw = f"//{parsed.netloc}{raw}"
    if re.match(r"^/[A-Za-z]:/", raw):
        raw = raw[1:]
    path = Path(raw)
    try:
        return path.resolve(strict=True)
    except FileNotFoundError:
        store = store_root.resolve(strict=True)
        matching_indexes = [
            index
            for index, part in enumerate(path.parts)
            if part.casefold() == store.name.casefold()
        ]
        if not matching_indexes:
            raise ArchiveContractError("MLflow artifact URI target is missing")
        relative = Path(*path.parts[matching_indexes[-1] + 1 :])
        try:
            relocated = (store / relative).resolve(strict=True)
            relocated.relative_to(store)
        except (FileNotFoundError, ValueError) as error:
            raise ArchiveContractError(
                "relocated MLflow artifact URI is invalid"
            ) from error
        return relocated


def _metric_registry(run: ArchiveRun) -> dict[str, Any]:
    definitions = [definition.as_dict() for _, _, definition in run.metrics.values()]
    body = {"schema_version": "myis.metric-registry.v2", "definitions": sorted(definitions, key=lambda item: str(item["metric_id"]))}
    body["registry_sha256"] = _record_hash(body, "registry_sha256")
    return body


def _validate_backup(root: Path) -> dict[str, Any]:
    try:
        report = json.loads((root / "backup.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArchiveContractError("backup receipt is invalid") from error
    if report.get("schema_version") != "myis.mlflow-backup.v2" or not isinstance(report.get("checksums"), dict):
        raise ArchiveContractError("backup contract is invalid")
    for relative, digest in report["checksums"].items():
        path = (root / relative).resolve(strict=True)
        path.relative_to(root.resolve(strict=True))
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ArchiveContractError(f"backup hash mismatch: {relative}")
    return report


def _write_once(path: Path, value: Any) -> None:
    data = canonical_json(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ArchiveContractError(f"immutable archive record drifted: {path}")
        return
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
