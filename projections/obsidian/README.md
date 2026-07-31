# Obsidian Report Projection

This directory contains the retired small-report compatibility projection built
from `projections/read-model/read-model.v2.json`. The canonical reporting vault
is `obsidian_report/`; `02_Brain` remains pointer-only research memory and is not
the Phase/Task reporting vault.

- `generated/` is overwritten by `myis-report sync`.
- `templates/` defines pointer-only manual note fields.
- Never enter metrics, costs, decisions, or readiness manually.
- Never store qrels, query IDs, membership, per-query outcomes, or raw payloads.

Run `uv run --no-sync myis-report sync --repository-root .` after validated manifest or decision changes.
