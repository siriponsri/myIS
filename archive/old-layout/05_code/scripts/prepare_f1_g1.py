"""Prepare a sealed F1/G1 Owner-value batch without scientific execution."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from myis_research.harness.dapfam_contracts import SAFE_PROJECTION_SCHEMA, validate_owner_value_batch
from myis_research.harness.owner_local import (
    OwnerLocalPreparationError,
    discover_source_root,
    describe_source_schema,
    prepare_owner_value_batch,
)
from myis_research.mlflow_mirror import MLflowMirror, MirrorSpec, MirrorStage, default_store


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def default_owner_root(repository_root: Path) -> Path:
    for ancestor in (repository_root.resolve(), *repository_root.resolve().parents):
        store_parent = ancestor / "01_Stores" / "00_myIS"
        if store_parent.is_dir():
            return store_parent / "owner-local" / "f1-g1"
    raise OwnerLocalPreparationError("OWNER_LOCAL_STORE_NOT_FOUND")


def prepare(
    *,
    repository_root: Path = REPOSITORY_ROOT,
    source_root: Path | None = None,
    owner_root: Path | None = None,
    mlflow_root: Path | None = None,
    execute_notebook: bool = True,
) -> dict[str, Any]:
    repository_root = repository_root.resolve(strict=True)
    source_root = (source_root or discover_source_root(repository_root)).resolve(strict=True)
    owner_root = (owner_root or default_owner_root(repository_root)).resolve()
    _assert_outside_repository(owner_root, repository_root)
    for relative in ("config", "sealed/splits", "safe/batches", "safe/validation", "safe/evidence", "safe/projections", "notebooks"):
        (owner_root / relative).mkdir(parents=True, exist_ok=True)

    batch, prepared_split, private_paths = prepare_owner_value_batch(repository_root, source_root)
    proposal = batch.proposal_sha256
    owner_paths = {
        "schema_version": "myis.owner-local-paths.v1",
        "source_root": str(source_root),
        "owner_root": str(owner_root),
        "sources": private_paths,
    }
    _write_current(owner_root / "config" / "owner-paths.json", owner_paths)

    sealed_path = owner_root / "sealed" / "splits" / proposal / "membership.json"
    sealed = {
        "schema_version": "myis.sealed-shared-membership.v1",
        "proposal_sha256": proposal,
        "seed": 42,
        "counts": batch.split.counts,
        "membership_sha256": batch.split.membership_sha256,
        "membership": {role: list(ids) for role, ids in prepared_split.membership.items()},
    }
    _write_once(sealed_path, sealed)

    batch_path = owner_root / "safe" / "batches" / f"g1-owner-value-batch-{proposal}.json"
    if batch_path.exists():
        existing_batch = validate_owner_value_batch(json.loads(batch_path.read_text(encoding="utf-8")))
        if existing_batch.proposal_sha256 != proposal:
            raise OwnerLocalPreparationError("IMMUTABLE_OWNER_LOCAL_CONFLICT")
        batch = existing_batch
    else:
        _write_once(batch_path, batch.model_dump(mode="json"))
    batch_sha = _sha256(batch_path)
    validation_path = owner_root / "safe" / "validation" / f"g1-owner-value-batch-{proposal}.json"
    validation = {
        "schema_version": "myis.f1-g1-validation-receipt.v1",
        "status": "PASS",
        "proposal_sha256": proposal,
        "safe_batch_sha256": batch_sha,
        "sealed_membership_sha256": _sha256(sealed_path),
        "checks": batch.validation.checks,
    }
    _write_once(validation_path, validation)

    resolved_mlflow = default_store(mlflow_root)
    _validate_existing_bootstrap(resolved_mlflow, batch.generator.git_commit)
    receipt = MLflowMirror(resolved_mlflow).sync(
        MirrorSpec(
            stage=MirrorStage.F1_G1_PREPARATION,
            run_name=f"f1-g1-preparation-{proposal[:12]}",
            git_commit=batch.generator.git_commit,
            canonical_source_sha256=batch_sha,
            track="C",
            arm="G1_PREPARATION",
            phase="F1",
            data_role="preparation",
            tags={
                "scientific_run": "false",
                "gate": "G1",
                "gate_status": "pending",
                "authorization": "NOT_AUTHORIZED",
                "dataset_payload_logged": "false",
            },
            parameters={
                "proposal_sha256": proposal,
                "query_count": batch.inventory_counts["queries"],
                "corpus_count": batch.inventory_counts["corpus"],
                "artifact_count": 0,
                "scientific_metric_count": 0,
            },
            metrics={},
        )
    )

    notebook = {"status": "SKIPPED", "reason": "disabled"}
    if execute_notebook:
        notebook = _execute_notebook(repository_root, owner_root, batch_path)
    prior_proposal = None
    projection_path = owner_root / "safe" / "projections" / "current.json"
    if projection_path.is_file():
        prior = json.loads(projection_path.read_text(encoding="utf-8"))
        if prior.get("proposal_sha256") != proposal:
            prior_proposal = prior.get("proposal_sha256")
    projection = {
        "schema_version": SAFE_PROJECTION_SCHEMA,
        "status": "READY_FOR_OWNER_REVIEW",
        "readiness": "F1/G1 preparation only",
        "gate": "G1",
        "gate_status": "pending",
        "authorization": "NOT_AUTHORIZED",
        "scientific_run": False,
        "scientific_metric_count": 0,
        "proposal_sha256": proposal,
        "supersedes_proposal_sha256": prior_proposal,
        "safe_batch_sha256": batch_sha,
        "safe_batch_id": batch_path.name,
        "validation_receipt_id": validation_path.name,
        "inventory_counts": batch.inventory_counts,
        "qrels_domain_distribution": batch.qrels_domain_distribution,
        "split": batch.split.model_dump(mode="json"),
        "source_commitments": [item.model_dump(mode="json") for item in batch.sources],
        "family_commitment_sha256": batch.family_commitment_sha256,
        "evaluator": batch.evaluator.model_dump(mode="json"),
        "field_protocol": batch.field_protocol,
        "published_targets": batch.published_targets.model_dump(mode="json"),
        "unresolved_owner_decisions": batch.unresolved_owner_decisions,
        "mlflow": {
            "status": receipt.status,
            "experiment_name": receipt.experiment_name,
            "run_id": receipt.mlflow_run_id,
            "mirror_key": receipt.mirror_key,
        },
        "notebook": notebook,
    }
    _write_current(projection_path, projection)
    return {
        "status": "PASS",
        "readiness": projection["readiness"],
        "gate_status": "pending",
        "scientific_run": False,
        "proposal_sha256": proposal,
        "safe_batch_sha256": batch_sha,
        "owner_root": str(owner_root),
        "mlflow_status": receipt.status,
        "mlflow_run_id": receipt.mlflow_run_id,
        "notebook_status": notebook["status"],
        "unresolved_owner_decisions": batch.unresolved_owner_decisions,
    }


def _execute_notebook(repository_root: Path, owner_root: Path, batch_path: Path) -> dict[str, str]:
    try:
        import nbformat
        from nbclient import NotebookClient
        from jupyter_client.kernelspec import NoSuchKernel
    except ImportError:
        return {"status": "SYNC_DEFERRED", "reason": "notebook_extra_unavailable"}
    source = repository_root / "03_experiments" / "notebooks" / "Data_Review.ipynb"
    target = owner_root / "notebooks" / "Data_Review.executed.ipynb"
    notebook = nbformat.read(source, as_version=4)
    previous = os.environ.get("MYIS_F1G1_SAFE_BATCH")
    os.environ["MYIS_F1G1_SAFE_BATCH"] = str(batch_path)
    try:
        try:
            NotebookClient(notebook, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(owner_root / "notebooks")}}).execute()
            runner = "nbclient"
        except NoSuchKernel:
            _execute_notebook_in_process(notebook, nbformat)
            runner = "deterministic_in_process"
    finally:
        if previous is None:
            os.environ.pop("MYIS_F1G1_SAFE_BATCH", None)
        else:
            os.environ["MYIS_F1G1_SAFE_BATCH"] = previous
    nbformat.write(notebook, target)
    return {"status": "PASS", "artifact_id": target.name, "sha256": _sha256(target), "runner": runner}


def _execute_notebook_in_process(notebook: Any, nbformat_module: Any) -> None:
    namespace: dict[str, Any] = {"__name__": "__main__"}
    execution_count = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        execution_count += 1
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exec(compile(cell.source, f"Data_Review.ipynb:cell-{execution_count}", "exec"), namespace)
        cell.execution_count = execution_count
        output = stream.getvalue()
        cell.outputs = [nbformat_module.v4.new_output("stream", name="stdout", text=output)] if output else []


def _validate_existing_bootstrap(store_root: Path, git_commit: str) -> None:
    reports = sorted((store_root / "bootstrap-reports").glob(f"mlflow-bootstrap-{git_commit}-*.json"))
    if len(reports) != 1:
        raise OwnerLocalPreparationError("MLFLOW_BOOTSTRAP_FOR_HEAD_REQUIRED")
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    required = {
        "status": "PASS",
        "scientific_run": False,
        "dataset_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
        "git_commit": git_commit,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        raise OwnerLocalPreparationError("MLFLOW_BOOTSTRAP_INVALID")


def _assert_outside_repository(path: Path, repository_root: Path) -> None:
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return
    raise OwnerLocalPreparationError("OWNER_LOCAL_STORE_INSIDE_GIT")


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    encoded = _json_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise OwnerLocalPreparationError("IMMUTABLE_OWNER_LOCAL_CONFLICT")


def _write_current(path: Path, payload: dict[str, Any]) -> None:
    encoded = _json_bytes(payload)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a hash/count-only F1/G1 Owner batch")
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--owner-root", type=Path)
    parser.add_argument("--mlflow-root", type=Path)
    parser.add_argument("--skip-notebook", action="store_true")
    parser.add_argument("--describe-schema", action="store_true", help="print field names only and write nothing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.describe_schema:
            source_root = (args.source_root or discover_source_root(REPOSITORY_ROOT)).resolve(strict=True)
            result = describe_source_schema(source_root)
        else:
            result = prepare(
            source_root=args.source_root,
            owner_root=args.owner_root,
            mlflow_root=args.mlflow_root,
            execute_notebook=not args.skip_notebook,
            )
    except Exception as error:
        result = {
            "status": "BLOCKED",
            "reason": str(error) if isinstance(error, OwnerLocalPreparationError) else "F1_G1_PREPARATION_FAILED",
            "error_type": type(error).__name__,
            "scientific_run": False,
            "gate_status": "pending",
        }
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
