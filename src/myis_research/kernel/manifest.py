from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .canonical import canonical_sha256


def build_manifest(
    *,
    run_id: str,
    experiment_id: str,
    campaign_id: str,
    stage: str,
    status: str,
    source: dict[str, Any],
    data: dict[str, Any],
    method: dict[str, Any],
    resources: dict[str, Any],
    metrics: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    evidence_class: str,
    git_commit: str,
    owner_local_receipt_sha256: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    if stage not in {"fixture", "train", "selection", "final", "report"}:
        raise ValueError("invalid manifest stage")
    if status not in {"valid", "invalid", "exploratory", "blocked", "superseded", "aggregate_pending"}:
        raise ValueError("invalid manifest status")
    body: dict[str, Any] = {
        "schema_version": "myis.run-manifest.v2",
        "run_id": run_id,
        "experiment_id": experiment_id,
        "campaign_id": campaign_id,
        "status": status,
        "stage": stage,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": source,
        "data": data,
        "method": method,
        "resources": resources,
        "metrics": metrics,
        "artifacts": artifacts,
        "evidence_class": evidence_class,
        "git_commit": git_commit,
        "owner_local_receipt_sha256": owner_local_receipt_sha256,
    }
    body["manifest_sha256"] = canonical_sha256({key: value for key, value in body.items() if key != "manifest_sha256"})
    return body
