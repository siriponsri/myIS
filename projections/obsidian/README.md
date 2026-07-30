# Obsidian Report Projection

This directory contains small, rebuildable Markdown reports generated from `projections/read-model/read-model.v1.json`. The primary vault is `02_Brain`; Research keeps this projection contract and compatibility output only.

- `generated/` is overwritten by `myis-report sync`.
- `templates/` defines pointer-only manual note fields.
- Never enter metrics, costs, decisions, or readiness manually.
- Never store qrels, query IDs, membership, per-query outcomes, or raw payloads.

Run `uv run --no-sync myis-report sync --repository-root .` after validated manifest or decision changes.
