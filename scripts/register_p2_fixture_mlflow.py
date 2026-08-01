"""Register the validated P2 fixture in an isolated aggregate-only MLflow store."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from myis_research.kernel.canonical import canonical_sha256
from myis_research.mlflow_mirror import (
    SYSTEM_EXPERIMENT,
    MLflowMirror,
    MirrorArtifact,
    MirrorKind,
    MirrorSpec,
    MirrorStage,
)
from myis_research.p2.fixture import (
    P2FixtureError,
    validate_fixture_execution_manifest,
    validate_fixture_receipt,
)


REGISTRATION_SCHEMA = "myis.p2-fixture-mlflow-registration.v1"
RECEIPT_PATH = Path("outputs/fixtures/p2/p2-fixture-pilot-v1.receipt.json")
MANIFEST_PATH = Path(
    "outputs/fixtures/p2/p2-fixture-pilot-v1.execution-manifest.json"
)
REGISTRATION_PATH = Path(
    "outputs/fixtures/p2/p2-fixture-pilot-v1.mlflow-registration.json"
)
STORE_METADATA = {
    "schema_version": "myis.mlflow-store.v2",
    "artifact_root": "artifacts",
    "repository_program_id": "myis-research",
    "created_by": "register_p2_fixture_mlflow.py",
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise P2FixtureError(f"fixture artifact must be a JSON object: {path.name}")
    return value


def _write_new_or_identical(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != encoded:
            raise P2FixtureError("immutable fixture MLflow registration differs from existing bytes")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def _ensure_store_metadata(store: Path) -> None:
    (store / "artifacts").mkdir(parents=True, exist_ok=True)
    (store / "receipts").mkdir(parents=True, exist_ok=True)
    metadata_path = store / "store.json"
    encoded = (json.dumps(STORE_METADATA, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if metadata_path.exists():
        if metadata_path.is_symlink() or not metadata_path.is_file():
            raise P2FixtureError("isolated fixture MLflow store metadata path is invalid")
        existing = _load_json(metadata_path)
        if existing.get("schema_version") != "myis.mlflow-store.v2" or existing.get("artifact_root") != "artifacts":
            raise P2FixtureError("isolated fixture MLflow store metadata is incompatible")
        return
    metadata_path.write_bytes(encoded)


def register(
    repository_root: Path,
    store_root: Path,
    *,
    mirror: MLflowMirror | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    store = store_root.resolve()
    if store == root or root in store.parents:
        raise P2FixtureError("fixture MLflow store must be outside the Git repository")
    _ensure_store_metadata(store)

    receipt_path = root / RECEIPT_PATH
    manifest_path = root / MANIFEST_PATH
    receipt = validate_fixture_receipt(_load_json(receipt_path), repository_root=root)
    manifest = validate_fixture_execution_manifest(
        _load_json(manifest_path),
        receipt=receipt,
    )

    artifacts = (
        MirrorArtifact.from_path(
            receipt_path,
            kind=MirrorKind.RESULT,
            canonical_root=root,
        ),
        MirrorArtifact.from_path(
            manifest_path,
            kind=MirrorKind.ENVIRONMENT,
            canonical_root=root,
        ),
    )
    selected_mirror = mirror or MLflowMirror(store)
    mirrored = selected_mirror.sync(
        MirrorSpec(
            stage=MirrorStage.P2_SCOPE_DEVELOPMENT,
            experiment_name=SYSTEM_EXPERIMENT,
            run_name="p2-fixture-pilot-v1",
            run_id="p2-fixture-pilot-v1",
            git_commit=str(receipt["git_commit"]),
            canonical_source_sha256=str(receipt["receipt_sha256"]),
            campaign_id="scope-autoindex-v1",
            phase="P2_SCOPE_DEVELOPMENT",
            arm="R1",
            track="dapfam",
            data_role="synthetic_fixture",
            decision_id="D1_START_CAMPAIGN",
            dataset_lineage_sha256=str(receipt["train_signature_sha256"]),
            reproducibility_sha256=str(receipt["fixture_package_sha256"]),
            tags={
                "run_type": "fixture_pilot",
                "evidence_class": "fixture",
                "scientific_authority": "false",
                "measured_execution": "false",
                "protected_data_accessed": "false",
                "fixture_status": "passed",
            },
            parameters={
                "synthetic_candidates": int(receipt["synthetic_candidates"]),
                "synthetic_iterations": int(receipt["synthetic_adaptive_iterations"]),
                "synthetic_shortlist": int(receipt["synthetic_shortlist_count"]),
                "fixture_selection_exposures": int(receipt["fixture_selection_exposures"]),
                "negative_check_count": int(receipt["negative_check_count"]),
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
            },
            metrics={},
        ),
        artifacts,
    )
    if mirrored.status not in {"synced", "already_synced"} or not mirrored.mlflow_run_id:
        raise P2FixtureError(f"fixture MLflow registration failed: {mirrored.status}")

    registration: dict[str, Any] = {
        "schema_version": REGISTRATION_SCHEMA,
        "fixture_id": "p2-fixture-pilot-v1",
        "experiment": SYSTEM_EXPERIMENT,
        "run_type": "fixture_pilot",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "measured_execution": False,
        "protected_data_accessed": False,
        "source_receipt_uri": RECEIPT_PATH.as_posix(),
        "source_receipt_sha256": receipt["receipt_sha256"],
        "execution_manifest_uri": MANIFEST_PATH.as_posix(),
        "execution_manifest_sha256": manifest["manifest_sha256"],
        "fixture_package_sha256": receipt["fixture_package_sha256"],
        "mirror_key": mirrored.mirror_key,
        "mlflow_run_id": mirrored.mlflow_run_id,
        "status": "registered",
        "store_external": True,
        "protected_artifacts_mirrored": False,
    }
    registration["registration_sha256"] = canonical_sha256(registration)
    _write_new_or_identical(root / REGISTRATION_PATH, registration)
    return registration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--store-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = register(args.repository_root, args.store_root)
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
