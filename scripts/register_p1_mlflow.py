"""Mirror one validated P1 package as one parent and four MLflow children.

Only aggregate metric values, counts, hashes, cost, latency, and lineage are
logged. Canonical request, receipt, manifest, and protected artifacts remain
outside MLflow.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from myis_research.dapfam_p1 import load_package
from myis_research.mlflow_mirror import MLflowMirror, MirrorReceipt, MirrorSpec, MirrorStage


REGISTRATION_SCHEMA = "myis.p1-mlflow-registration.v2"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"canonical artifact must be a JSON object: {path}")
    return value


def _metric_name(item: dict[str, Any]) -> str:
    return "_".join(str(item[key]).lower().replace("@", "_at_") for key in ("scope", "name"))


def _cost_usd(manifest: dict[str, Any], receipt: dict[str, Any]) -> float:
    resources = manifest.get("resources", {})
    if isinstance(resources, dict):
        for key in ("cost_actual", "cost_usd"):
            value = resources.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
    return float(receipt["cost"]["value"])


def _require_synced(receipt: MirrorReceipt, label: str) -> None:
    if receipt.status not in {"synced", "already_synced"} or not receipt.mlflow_run_id:
        raise RuntimeError(f"MLflow {label} registration failed: {receipt.status}")


def _write_new_or_identical(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != encoded:
            raise ValueError(f"immutable MLflow registration already exists with different bytes: {path}")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def load_validated_p1_matrix(
    package_path: Path,
    repository_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Load a complete, internally hash-bound package for additive mirroring."""

    root = repository_root.resolve()
    package = load_package(package_path, root)
    receipt = _load_json(root / package["receipt_uri"])
    manifests = [_load_json(root / slot["manifest_uri"]) for slot in package["slots"]]
    manifests.sort(key=lambda item: (str(item["method"]["arm_id"]), str(item["stage"])))
    return package, manifests, receipt


def register(repository_root: Path, package_path: Path, store_root: Path) -> dict[str, object]:
    root = repository_root.resolve()
    package, manifests, receipt = load_validated_p1_matrix(package_path, root)
    package_sha = str(package["package_sha256"])
    receipt_sha = str(receipt["receipt_sha256"])
    dataset_sha = str(receipt["lineage_hashes"]["dataset_sha256"])
    git_commit = str(package["source_commit"])
    parent_values = [manifest.get("parent_run_id") for manifest in manifests]
    if any(not isinstance(value, str) or not value for value in parent_values):
        raise ValueError("P1 package manifests must bind one parent run")
    parent_ids = set(parent_values)
    if len(parent_ids) != 1:
        raise ValueError("P1 package manifests must bind one parent run")
    parent_run_id = parent_ids.pop()
    mirror = MLflowMirror(store_root)
    common_tags = {
        "scientific_run": "true",
        "source_package_sha256": package_sha,
        "source_receipt_sha256": receipt_sha,
        "historical_final_872": str(
            receipt["historical_exposure"].get("active_final_872_global_untouched", "unknown")
        ),
    }
    parent = mirror.sync(MirrorSpec(
        stage=MirrorStage.P1_CPU_BASELINE,
        run_name=parent_run_id,
        run_id=parent_run_id,
        git_commit=git_commit,
        canonical_source_sha256=package_sha,
        campaign_id="scope-autoindex-v1",
        phase=MirrorStage.P1_CPU_BASELINE.value,
        track="dapfam",
        data_role="train_selection",
        decision_id="D1_START_CAMPAIGN",
        dataset_lineage_sha256=dataset_sha,
        reproducibility_sha256=receipt_sha,
        tags=common_tags,
        parameters={
            "receipt_status": str(receipt["status"]),
            "child_count": len(manifests),
            "metric_row_count": len(receipt["metrics"]),
            "cost_usd": float(receipt["cost"]["value"]),
            "latency_seconds": float(receipt["latency_seconds"]),
        },
    ))
    _require_synced(parent, "parent")

    children: list[dict[str, Any]] = []
    for manifest in manifests:
        method = manifest["method"]
        arm = str(method.get("arm_id", ""))
        split = str(manifest["stage"])
        if arm not in {"R0", "R0-W"} or split not in {"train", "selection"}:
            raise ValueError("P1 package contains an invalid arm/split child")
        metrics = {
            _metric_name(item): float(item["value"])
            for item in manifest["metrics"]
            if isinstance(item, dict) and item.get("value") is not None
        }
        counts = {
            f"{_metric_name(item)}_n": int(item["n"])
            for item in manifest["metrics"]
            if isinstance(item, dict) and isinstance(item.get("n"), int) and not isinstance(item.get("n"), bool)
        }
        manifest_sha = str(manifest["manifest_sha256"])
        run_id = str(manifest["run_id"])
        child = mirror.sync(MirrorSpec(
            stage=MirrorStage.P1_CPU_BASELINE,
            run_name=run_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            git_commit=git_commit,
            canonical_source_sha256=manifest_sha,
            campaign_id="scope-autoindex-v1",
            phase=MirrorStage.P1_CPU_BASELINE.value,
            arm=arm,
            track="dapfam",
            data_role=split,
            decision_id="D1_START_CAMPAIGN",
            dataset_lineage_sha256=dataset_sha,
            reproducibility_sha256=receipt_sha,
            tags={**common_tags, "source_manifest_sha256": manifest_sha, "split": split},
            parameters={
                **counts,
                "cost_usd": _cost_usd(manifest, receipt),
                "latency_seconds": float(receipt["latency_seconds"]),
                "top_k": int(method["top_k"]),
            },
            metrics=metrics,
        ))
        _require_synced(child, f"child {arm}/{split}")
        children.append({
            "arm": arm,
            "split": split,
            "source_run_id": run_id,
            "source_manifest_sha256": manifest_sha,
            "status": child.status,
            "mirror_key": child.mirror_key,
            "mlflow_run_id": child.mlflow_run_id,
        })

    registration: dict[str, Any] = {
        "schema_version": REGISTRATION_SCHEMA,
        "authority": "validated canonical four-slot P1 package",
        "package_sha256": package_sha,
        "source_receipt_sha256": receipt_sha,
        "dataset_lineage_sha256": dataset_sha,
        "parent": {
            "source_run_id": parent_run_id,
            "status": parent.status,
            "mirror_key": parent.mirror_key,
            "mlflow_run_id": parent.mlflow_run_id,
        },
        "children": sorted(children, key=lambda item: (item["arm"], item["split"])),
        "store_external": True,
        "protected_artifacts_mirrored": False,
    }
    output = root / "evidence" / "mlflow-p1-registration.v2.json"
    _write_new_or_identical(output, registration)
    return registration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--store-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = register(args.repository_root, args.package, args.store_root)
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
