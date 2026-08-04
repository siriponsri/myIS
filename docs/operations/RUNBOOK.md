# ArmIndex Operations Runbook

## Development checks

```powershell
uv sync --locked --all-extras
uv run --no-sync pytest -q tests/test_armindex_contracts.py
uv run --no-sync pytest -q
uv run --no-sync myis-report check --repository-root .
uv run --no-sync python scripts/validate_layout_v2.py
git diff --check
```

These commands do not authorize model downloads or measured retrieval. Use
`dashboard/open-dashboard.cmd` for the Owner-facing local interface.

## Phase closeout

Validate manifests and receipts, freeze phase/task/Research Flow state, update
registries and budget, mirror safe aggregates to MLflow, build the shared read
model once, regenerate all projections, run sync/check twice, run integrity and
protected-content scans, then commit and push coherent bytes.

## Failure handling

Stop before Selection on a model-lock, evaluator, split, baseline, freeze,
budget, or protected-boundary failure. Preserve the failed attempt and recovery
pointer. Do not change a frozen model, adapter, evaluator, or scientific surface
as an operational retry.
