# myIS Research

`01_Research` is the Git repository and active control plane for the SCOPE / AutoIndex campaign. Git-tracked control records and immutable run bundles are authoritative. MLflow, Dashboard, Obsidian, and Paper are projections.

## Start here

1. `control/program.yaml` - identity, D1-D3 decisions, budget, protected boundary.
2. `control/campaigns/scope-autoindex-v1.yaml` - scientific protocol and arms.
3. `control/source-of-truth.yaml` - ownership matrix and data flow.
4. `campaigns/scope-autoindex-v1/INDEX.md` - active campaign workspace.
5. `archive/INDEX.md` - frozen legacy material and migration history.

## Active tree

| Path | Role |
|---|---|
| `control/` | canonical identity, protocol, decisions, asset registry |
| `campaigns/` | hypotheses, specs, manifests, evidence pointers, reports |
| `src/`, `tests/` | deterministic harness, validators, projections |
| `evidence/` | immutable evidence index; large/protected bytes stay external |
| `projections/` | rebuildable read model, Obsidian, session capsules |
| `dashboard/` | loopback Dashboard and read-only MLflow viewer |
| `schemas/` | machine contracts |
| `scripts/` | migration, cleanup, Owner-local and validation commands |
| `archive/` | read-only legacy provenance; never active authority |

## Data flow

`harness -> validated run bundle -> MLflow mirror -> read model -> Dashboard / Obsidian / Paper`

No projection may recalculate metrics or become a source of truth. Protected rows, qrels, membership, query IDs, and per-query outcomes never enter this repository.

## Commands

```powershell
uv sync --all-extras
uv run --no-sync pytest -q
uv run --no-sync myis-report sync --repository-root .
uv run --no-sync python scripts/mlflow_doctor.py --repository-root . --store-root $env:MYIS_MLFLOW_STORE
uv run --no-sync myis-dashboard serve --repository-root .
```

Dashboard includes operational and presentation views. Owner decisions are only `D1_START_CAMPAIGN`, `D2_OPEN_FINAL`, and `D3_SUBMIT_RELEASE`; D1 is the standing authorization.

This system is decision support, not legal advice.
