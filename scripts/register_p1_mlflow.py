"""Mirror a validated, hash-bound P1 manifest and receipt into MLflow.

Only aggregate metric values, counts, hashes, cost, latency and lineage are
logged. The owner-local receipt itself is not uploaded because its structured
keys intentionally include protected-source commitment names.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.mlflow_mirror import MLflowMirror, MirrorSpec, MirrorStage
from myis_research.projections.read_model import validated_p1_pairs


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"canonical artifact must be a JSON object: {path}")
    return value


def load_validated_p1_package(manifest_path: Path, receipt_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reject a receipt unless a valid, active manifest binds it exactly."""

    manifest = _load_json(manifest_path)
    receipt = _load_json(receipt_path)
    matches = validated_p1_pairs([manifest], [receipt])
    if len(matches) != 1:
        raise ValueError("P1 MLflow registration requires a valid manifest with a matching accepted receipt")
    return matches[0]["manifest"], matches[0]["receipt"]


def _metric_name(item: dict[str, Any]) -> str:
    return "_".join(str(item[key]).lower() for key in ("split", "scope", "name"))


def _cost_usd(manifest: dict[str, Any], receipt: dict[str, Any]) -> float:
    resources = manifest.get("resources", {})
    if isinstance(resources, dict):
        for key in ("cost_actual", "cost_usd"):
            value = resources.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
    return float(receipt["cost"]["value"])


def _require_canonical_path(path: Path, directory: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(directory.resolve(strict=True))
    except ValueError as error:
        raise ValueError(f"{label} must be under {directory}") from error
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"{label} must be a regular canonical file")
    return resolved


def register(repository_root: Path, manifest_path: Path, receipt_path: Path, store_root: Path) -> dict[str, object]:
    root = repository_root.resolve()
    campaign_root = root / "campaigns" / "scope-autoindex-v1"
    manifest_path = _require_canonical_path(manifest_path, campaign_root / "manifests", "manifest")
    receipt_path = _require_canonical_path(receipt_path, campaign_root / "evidence", "receipt")
    manifest, receipt = load_validated_p1_package(manifest_path, receipt_path)
    manifest_sha = str(manifest["manifest_sha256"])
    receipt_sha = str(receipt["receipt_sha256"])
    dataset_sha = str(receipt["lineage_hashes"]["dataset_sha256"])
    source_sha = manifest_sha
    git_commit = str(manifest["git"]["commit"])
    method = manifest.get("method", {})
    arm = str(method.get("arm") if isinstance(method, dict) else "")
    if arm not in {"R0", "R0-W"}:
        raise ValueError("P1 manifest method.arm must be R0 or R0-W")
    run_id = str(manifest["run_id"])
    parent_run_id = str(manifest.get("parent_run_id") or f"{run_id}-parent")
    manifest_metrics = manifest["metrics"]
    metrics = {
        _metric_name(item): float(item["value"])
        for item in manifest_metrics
        if isinstance(item, dict) and item.get("value") is not None
    }
    counts = {
        f"{_metric_name(item)}_n": int(item["n"])
        for item in manifest_metrics
        if isinstance(item, dict) and isinstance(item.get("n"), int) and not isinstance(item.get("n"), bool)
    }
    cost_usd = _cost_usd(manifest, receipt)
    mirror = MLflowMirror(store_root)
    parent = mirror.sync(MirrorSpec(
        stage=MirrorStage.P1_CPU_BASELINE,
        run_name=parent_run_id,
        run_id=parent_run_id,
        git_commit=git_commit,
        canonical_source_sha256=source_sha,
        campaign_id="scope-autoindex-v1",
        phase=MirrorStage.P1_CPU_BASELINE.value,
        data_role="train_selection",
        decision_id="D1_START_CAMPAIGN",
        dataset_lineage_sha256=dataset_sha,
        reproducibility_sha256=receipt_sha,
        tags={"scientific_run": "true", "source_manifest_sha256": manifest_sha, "source_receipt_sha256": receipt_sha, "historical_final_872": str(receipt["historical_exposure"].get("active_final_872_global_untouched", "unknown"))},
        parameters={"receipt_status": str(receipt["status"]), "metric_row_count": len(manifest_metrics), "cost_usd": cost_usd, "latency_seconds": float(receipt["latency_seconds"])},
    ))
    child = mirror.sync(MirrorSpec(
        stage=MirrorStage.P1_CPU_BASELINE,
        run_name=run_id,
        run_id=run_id,
        parent_run_id=parent.mirror_key,
        git_commit=git_commit,
        canonical_source_sha256=source_sha,
        campaign_id="scope-autoindex-v1",
        phase=MirrorStage.P1_CPU_BASELINE.value,
        arm=arm,
        track="dapfam",
        data_role="train_selection",
        decision_id="D1_START_CAMPAIGN",
        dataset_lineage_sha256=dataset_sha,
        reproducibility_sha256=receipt_sha,
        tags={"scientific_run": "true", "source_manifest_sha256": manifest_sha, "source_receipt_sha256": receipt_sha, "historical_final_872": str(receipt["historical_exposure"].get("active_final_872_global_untouched", "unknown"))},
        parameters={**counts, "cost_usd": cost_usd, "latency_seconds": float(receipt["latency_seconds"])},
        metrics=metrics,
    ))
    registration = {
        "schema_version": "myis.p1-mlflow-registration.v1",
        "authority": "validated canonical P1 manifest plus matching aggregate receipt",
        "source_manifest_sha256": manifest_sha,
        "source_receipt_sha256": receipt_sha,
        "source_run_id": run_id,
        "dataset_lineage_sha256": dataset_sha,
        "parent": {"status": parent.status, "mirror_key": parent.mirror_key, "mlflow_run_id": parent.mlflow_run_id},
        "children": [{"arm": arm, "status": child.status, "mirror_key": child.mirror_key, "mlflow_run_id": child.mlflow_run_id}],
        "store_external": True,
    }
    output = root / "evidence" / "mlflow-p1-registration.v1.json"
    output.write_text(json.dumps(registration, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--store-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = register(args.repository_root, args.manifest, args.receipt, args.store_root)
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
