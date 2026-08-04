"""Active repository layout validation."""

from __future__ import annotations

from pathlib import Path

REQUIRED = (
    "control/program.yaml", "control/source-of-truth.yaml",
    "control/campaigns/scope-autoindex-v1.yaml", "control/assets/reusable_assets.yaml",
    "campaigns/scope-autoindex-v1/INDEX.md", "src/myis_research", "tests",
    "dashboard/index.html", "dashboard/mlflow/mlflow.sh", "projections/obsidian",
    "schemas/run-manifest.v2.json", "archive/INDEX.md",
)
# ``inbox`` is a governed specification input, not a legacy runtime tree.
FORBIDDEN_ACTIVE = (
    "00_governance",
    "01_evidence",
    "02_tracks",
    "03_experiments",
    "04_outputs",
    "05_code",
    "06_frontend",
    "07_obsidian_note",
    "output",
)


def validate(root: Path) -> dict[str, object]:
    root = root.resolve()
    missing = [item for item in REQUIRED if not (root / item).exists()]
    stale = [item for item in FORBIDDEN_ACTIVE if (root / item).exists()]
    return {"schema_version": "myis.layout-validation.v2", "status": "PASS" if not missing and not stale else "FAIL", "missing": missing, "stale_active_roots": stale}
