"""Non-executable DAPFAM reproduction command scaffold.

This module intentionally has no dataset, qrels, provider, MLflow, or harness
executor imports. A future executor requires separate Owner-approved work.
"""

from __future__ import annotations

from pathlib import Path

from .drafts import DRAFT_RUNSPEC_SCHEMA, DraftValidationError, load_draft_document


WAITING_GATE_EXIT_CODE = 2


def reproduce_dapfam(
    *,
    repository_root: Path,
    manifest: Path | None,
    validate_draft: bool,
) -> dict[str, object]:
    """Return a fail-closed F1/G1 preparation result without executing anything."""

    result: dict[str, object] = {
        "status": "WAITING_GATE",
        "gate": "G1",
        "gate_status": "pending",
        "reason": "G1_REPRODUCTION_APPROVAL_REQUIRED",
        "executor_available": False,
        "scientific_run": False,
        "dataset_access": "none",
        "network_access": "none",
        "provider_access": "none",
        "gpu_access": "none",
        "mlflow_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
    }
    # A normal invocation refuses before opening a caller-supplied path. The
    # explicit dry-run/validation mode is limited to checked-in planning files.
    if validate_draft:
        if manifest is None:
            raise DraftValidationError("--manifest is required for draft validation")
        result["draft_validation"] = load_draft_document(
            manifest,
            template_root=repository_root / "03_experiments" / "templates",
            expected_schema=DRAFT_RUNSPEC_SCHEMA,
        )
    return result
