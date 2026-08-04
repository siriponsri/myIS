from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from myis_research.mlflow_archive import (
    ACTIVE_CAMPAIGN,
    ArtifactPointer,
    ArchiveContractError,
    ArchiveRun,
    FreezeBundle,
    MLflowEvidenceArchive,
    MetricDefinition,
    RegistrySnapshot,
    RULE_REGISTRY_SCHEMA,
    SCHEMA_REGISTRY_SCHEMA,
    validate_cross_projection_receipt,
)
from myis_research.mlflow_mirror import MirrorReceipt, MirrorSpec, MirrorStage, MirrorValidationError


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


class FakeMirror:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def sync(self, spec: object, artifacts: object = ()) -> MirrorReceipt:
        self.calls.append((spec, artifacts))
        return MirrorReceipt(
            receipt_id="m" * 64,
            mirror_key="m" * 64,
            status="synced",
            experiment_name="myis-system",
            recorded_at_utc="2026-01-01T00:00:00Z",
            canonical_source_sha256=_digest("source"),
            git_commit="a" * 40,
            artifact_hashes={},
            mlflow_run_id="synthetic-mlflow-run",
        )


def _freeze(*, metrics: dict[str, tuple[float, int, MetricDefinition]] | None = None) -> FreezeBundle:
    schema_registry = _registry(SCHEMA_REGISTRY_SCHEMA, "schema")
    rule_registry = _registry(RULE_REGISTRY_SCHEMA, "rule")
    definitions = [definition.as_dict() for _, _, definition in (metrics or {}).values()]
    metric_registry = {"schema_version": "myis.metric-registry.v2", "definitions": sorted(definitions, key=lambda item: str(item["metric_id"]))}
    metric_registry["registry_sha256"] = _digest_json(metric_registry)
    return FreezeBundle(
        freeze_id="freeze-test-1", campaign_id=ACTIVE_CAMPAIGN, phase_id="P0_FOUNDATION",
        scope="archive", status="frozen_development", source_commit="a" * 40,
        rules_sha256=rule_registry.as_dict()["registry_sha256"], metric_registry_sha256=metric_registry["registry_sha256"],
        schema_registry_sha256=schema_registry.as_dict()["registry_sha256"], evaluator_sha256=_digest("evaluator"),
        protocol_sha256=_digest("protocol"), environment_lock_sha256=_digest("environment"),
    )


def _metric() -> MetricDefinition:
    return MetricDefinition(
        metric_id="synthetic_metric", mlflow_key="synthetic_metric", evaluator_sha256=_digest("evaluator"),
        definition={"evaluation_unit": "synthetic", "direction": "higher_is_better", "valid_range": [0.0, 1.0], "sample_count_required": True},
    )


def _digest_json(value: dict[str, object]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "registry_sha256"}
    return hashlib.sha256(json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def _registry(schema: str, kind: str) -> RegistrySnapshot:
    return RegistrySnapshot(schema_version=schema, registry_kind=kind, items=({"id": f"{kind}-1", "sha256": _digest(kind)},))


def _run() -> ArchiveRun:
    metrics = {"synthetic_metric": (0.5, 2, _metric())}
    return ArchiveRun(
        run_id="synthetic-sync-1", phase_id="P0_FOUNDATION", task_id="P0.3", run_kind="projection_sync",
        git_commit="a" * 40, manifest_sha256=_digest("manifest"), receipt_sha256=_digest("receipt"),
        dataset_lineage_sha256=_digest("dataset"), config_sha256=_digest("config"), evaluator_sha256=_digest("evaluator"),
        environment_sha256=_digest("environment"), read_model_revision="revision-1", read_model_sha256=_digest("model"),
        evidence_maturity="non_scientific", run_validity="valid", freeze=_freeze(metrics=metrics),
        metrics=metrics, safe_to_present=True, is_latest=True, is_latest_valid=True,
    )


def _index() -> dict[str, str]:
    return {"read_model_revision": "revision-1", "read_model_sha256": _digest("model")}


def _script_module(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_archive_writes_hash_bound_safe_artifacts_and_is_idempotent(tmp_path: Path) -> None:
    mirror = FakeMirror()
    archive = MLflowEvidenceArchive(tmp_path, mirror=mirror)  # type: ignore[arg-type]
    receipt = archive.sync(_run(), archive_index=_index(), schema_registry=_registry(SCHEMA_REGISTRY_SCHEMA, "schema"), rule_registry=_registry(RULE_REGISTRY_SCHEMA, "rule"))
    assert receipt.mlflow_run_id == "synthetic-mlflow-run"
    assert len(mirror.calls) == 1
    repeat = archive.sync(_run(), archive_index=_index(), schema_registry=_registry(SCHEMA_REGISTRY_SCHEMA, "schema"), rule_registry=_registry(RULE_REGISTRY_SCHEMA, "rule"))
    assert repeat == receipt
    assert len(mirror.calls) == 1
    staged = next((tmp_path / "staging").glob("*/freeze/bundle.json"))
    assert json.loads(staged.read_text(encoding="utf-8"))["schema_version"] == "myis.freeze-bundle.v2"


def test_archive_uses_armindex_a0_stage_and_campaign_for_receipt_driven_closeout(tmp_path: Path) -> None:
    mirror = FakeMirror()
    archive = MLflowEvidenceArchive(tmp_path, mirror=mirror)  # type: ignore[arg-type]
    run = replace(
        _run(),
        run_id="a010-receipt-sync",
        phase_id="A0_MIGRATION_FOUNDATION",
        task_id="A0.10",
        run_kind="phase_closeout",
    )
    archive.sync(run, archive_index=_index(), schema_registry=_registry(SCHEMA_REGISTRY_SCHEMA, "schema"), rule_registry=_registry(RULE_REGISTRY_SCHEMA, "rule"))
    spec, _ = mirror.calls[0]
    assert isinstance(spec, MirrorSpec)
    assert spec.stage == MirrorStage.A0_MIGRATION_FOUNDATION
    assert spec.campaign_id == "armindex-multiretriever-v2"
    assert spec.experiment_name == "myis-system"
    spec.validate(())


def test_v2_archive_rejects_unshared_revision_and_invalid_metric_contract(tmp_path: Path) -> None:
    archive = MLflowEvidenceArchive(tmp_path, mirror=FakeMirror())  # type: ignore[arg-type]
    with pytest.raises(ArchiveContractError, match="shared read model"):
        archive.sync(_run(), archive_index={"read_model_revision": "other", "read_model_sha256": _digest("model")}, schema_registry=_registry(SCHEMA_REGISTRY_SCHEMA, "schema"), rule_registry=_registry(RULE_REGISTRY_SCHEMA, "rule"))
    bad = MetricDefinition(metric_id="bad", mlflow_key="bad", evaluator_sha256=_digest("evaluator"), definition={"evaluation_unit": "synthetic", "direction": "higher_is_better", "valid_range": [0, 1], "sample_count_required": False})
    with pytest.raises(ArchiveContractError, match="sample count"):
        bad.validate()


def test_archive_backup_restore_cli_and_manual_rebuild_plan_are_local_and_non_destructive(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for name in ("database", "artifacts", "receipts"):
        (tmp_path / name).mkdir(parents=True)
    (tmp_path / "database" / "mlflow.db").write_bytes(b"SQLite format 3\x00synthetic")
    (tmp_path / "artifacts" / "safe.json").write_text("{}", encoding="utf-8")
    (tmp_path / "receipts" / "safe.json").write_text("{}", encoding="utf-8")
    (tmp_path / "store.json").write_text('{"schema_version":"myis.mlflow-store.v2","artifact_root":"artifacts"}', encoding="utf-8")
    archive = MLflowEvidenceArchive(tmp_path, mirror=FakeMirror())  # type: ignore[arg-type]
    backup = archive.backup("synthetic-1")
    assert (backup / "backup.json").is_file()
    restored = tmp_path.parent / "restored-synthetic-store"
    module = _script_module("mlflow_archive")
    assert module.main(["restore", "--store-root", str(tmp_path), "--backup-id", "synthetic-1", "--target-root", str(restored)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    assert (restored / "database/mlflow.db").read_bytes() == b"SQLite format 3\x00synthetic"
    plan = archive.quarantine_and_rebuild_plan("synthetic corruption")
    assert plan["automatic_store_switch"] is False
    assert not (tmp_path / "quarantine").exists()


def test_archive_rejects_run_identity_collision_and_unsafe_lifecycle(tmp_path: Path) -> None:
    archive = MLflowEvidenceArchive(tmp_path, mirror=FakeMirror())  # type: ignore[arg-type]
    schemas = _registry(SCHEMA_REGISTRY_SCHEMA, "schema")
    rules = _registry(RULE_REGISTRY_SCHEMA, "rule")
    archive.sync(_run(), archive_index=_index(), schema_registry=schemas, rule_registry=rules)
    conflicting = replace(_run(), manifest_sha256=_digest("other"))
    with pytest.raises(ArchiveContractError, match="immutable archive record drifted"):
        archive.sync(conflicting, archive_index=_index(), schema_registry=schemas, rule_registry=rules)

    final = replace(_run(), phase_id="P3_FINAL")
    with pytest.raises(ArchiveContractError, match="D2_OPEN_FINAL"):
        final.validate()


def test_typed_pointer_rejects_paths_and_copied_protected_bytes() -> None:
    valid = ArtifactPointer(
        artifact_id="safe-pointer", artifact_class="protected", role="ranking",
        store_uri="owner-local://runs/opaque-1", sha256=_digest("pointer"), schema_id="ranking.v1",
    )
    valid.validate()
    with pytest.raises(ArchiveContractError, match="URI"):
        ArtifactPointer(
            artifact_id="unsafe", artifact_class="protected", role="ranking",
            store_uri="C:/Users/example/secret", sha256=_digest("pointer"), schema_id="ranking.v1",
        ).validate()


def test_cross_projection_receipt_rejects_missing_or_stale_mlflow_binding(tmp_path: Path) -> None:
    receipt = MLflowEvidenceArchive(tmp_path, mirror=FakeMirror()).sync(
        _run(), archive_index=_index(), schema_registry=_registry(SCHEMA_REGISTRY_SCHEMA, "schema"),
        rule_registry=_registry(RULE_REGISTRY_SCHEMA, "rule"),
    )
    valid = {"schema_version": "myis.projection-sync-receipt.v2", "status": "PASS", **_index(), "mlflow_run_id": receipt.mlflow_run_id}
    validate_cross_projection_receipt(valid, receipt, **_index())
    with pytest.raises(ArchiveContractError, match="no matching MLflow run"):
        validate_cross_projection_receipt({**valid, "mlflow_run_id": None}, receipt, **_index())
    with pytest.raises(ArchiveContractError, match="stale"):
        validate_cross_projection_receipt({**valid, "read_model_revision": "stale"}, receipt, **_index())


def test_bootstrap_preserves_legacy_report_and_appends_v2_migration(tmp_path: Path) -> None:
    module = _script_module("bootstrap_mlflow")
    legacy = tmp_path / "mlflow-bootstrap.json"
    legacy_bytes = b'{"schema_version":"myis.mlflow-bootstrap-report.v1"}\n'
    legacy.write_bytes(legacy_bytes)
    report = {"schema_version": "myis.mlflow-bootstrap-report.v2", "status": "PASS"}
    path = module._write_bootstrap_report(tmp_path, report)
    assert path.name == "mlflow-bootstrap-v2.json"
    assert legacy.read_bytes() == legacy_bytes
    assert json.loads(path.read_text(encoding="utf-8")) == report


@pytest.mark.parametrize(
    "metadata",
    [
        {"confirmation_ids": "opaque"},
        {"confirmation": "true"},
        {"provider_payload": "raw"},
        {"query_ids": "never"},
    ],
)
def test_mirror_metadata_whitelist_rejects_confirmation_ids_and_protected_payload(metadata: dict[str, object]) -> None:
    spec = MirrorSpec(
        stage=MirrorStage.P0_FOUNDATION, run_name="synthetic", git_commit="a" * 40,
        canonical_source_sha256=_digest("source"), phase="P0_FOUNDATION", parameters=metadata,
    )
    with pytest.raises(MirrorValidationError, match="forbidden"):
        spec.validate(())
    allowed = MirrorSpec(
        stage=MirrorStage.P0_FOUNDATION, run_name="synthetic", git_commit="a" * 40,
        canonical_source_sha256=_digest("source"), phase="P0_FOUNDATION", parameters={"confirmation": True},
    )
    allowed.validate(())


def _doctor_fixture(store: Path) -> tuple[sqlite3.Connection, Path]:
    database = store / "database/mlflow.db"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.execute("create table runs (run_uuid text, artifact_uri text, lifecycle_stage text)")
    connection.execute("create table tags (run_uuid text, key text, value text)")
    key = _digest("archive-key")
    run_id = "synthetic-run"
    archive_record_sha = _digest("archive-record")
    revision = _digest("revision")
    mirror = {"schema_version": "myis.mlflow-mirror-receipt.v1", "mirror_key": "mirror-key", "mlflow_run_id": run_id}
    mirror_sha = hashlib.sha256(json.dumps(mirror, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
    receipt = {"schema_version": "myis.mlflow-archive-receipt.v2", "archive_key": key, "archive_record_sha256": archive_record_sha, "mirror_receipt_sha256": mirror_sha, "read_model_sha256": revision, "read_model_revision": revision, "mlflow_run_id": run_id}
    (store / "receipts/archive").mkdir(parents=True)
    (store / "receipts/archive" / f"{key}.json").write_text(json.dumps(receipt), encoding="utf-8")
    (store / "receipts/mlflow").mkdir(parents=True)
    (store / "receipts/mlflow/mlflow-mirror-mirror-key.json").write_text(json.dumps(mirror), encoding="utf-8")
    staging = store / "staging" / key / "about"
    staging.mkdir(parents=True)
    (staging / "run.json").write_text(json.dumps({"archive_record_sha256": archive_record_sha, "freeze_sha256": _digest("freeze")}), encoding="utf-8")
    artifact_root = store / "artifacts" / run_id
    stored = artifact_root / "mirror" / "docs" / "about"
    stored.mkdir(parents=True)
    (stored / "run.json").write_bytes((staging / "run.json").read_bytes())
    connection.execute("insert into runs values (?, ?, 'active')", (run_id, artifact_root.as_uri()))
    connection.executemany("insert into tags values (?, ?, ?)", [(run_id, "read_model_revision", revision), (run_id, "read_model_sha256", revision), (run_id, "mirror_key", "mirror-key"), (run_id, "freeze_sha256", _digest("freeze"))])
    connection.commit()
    return connection, stored / "run.json"


def test_doctor_archive_checks_detect_lineage_hash_and_protected_content(tmp_path: Path) -> None:
    module = _script_module("mlflow_doctor")
    connection, artifact = _doctor_fixture(tmp_path)
    ok, _, failures = module._validate_archives(tmp_path, connection)
    assert ok and not failures
    connection.execute("update tags set value='bad' where key='freeze_sha256'")
    connection.commit()
    ok, _, failures = module._validate_archives(tmp_path, connection)
    assert not ok and "freeze lineage mismatch" in failures[0]
    connection.execute("update tags set value=? where key='freeze_sha256'", (_digest("freeze"),))
    connection.commit()
    artifact.write_text('{"provider_payload":"forbidden"}', encoding="utf-8")
    ok, _, failures = module._validate_archives(tmp_path, connection)
    assert not ok and "protected or secret content" in failures[0]
    connection.close()
    with pytest.raises(ArchiveContractError, match="cannot be copied"):
        ArtifactPointer(
            artifact_id="copied", artifact_class="protected", role="ranking",
            store_uri="owner-local://runs/opaque-1", sha256=_digest("pointer"), schema_id="ranking.v1", copied_to_mlflow=True,
        ).validate()
