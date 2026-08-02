# Projection Index

`read-model/` is the only generated read model consumed by Dashboard, Brain,
and Paper projections.

## Owner entry point

The only supported user-facing start entry point is
`../dashboard/open-dashboard.cmd`. It owns Dashboard health validation and
provides fixed actions for the external read-only MLflow archive and the
canonical `../obsidian_report/` vault.

The retired `open-dashboard.cmd`, `open-mlflow.cmd`, and
`open-obsidian-report.cmd` sources are preserved under
`../archive/p1-recovery-20260730/legacy-launchers/` and are not runtime entry
points. Restore them only from a reviewed rollback commit; they do not meet the
unified health/security contract.

`run-legacy-p1.cmd` is a protected Owner-local execution command, not a UI
launcher. Never use it for launcher or interface acceptance and never run it
during the recovery freeze. It fails closed unless the Owner explicitly sets
`MYIS_LEGACY_DAPFAM_ROOT` to the protected legacy DAPFAM data directory.

Set `MYIS_DASHBOARD_PORT` before starting the unified Dashboard when a
non-default loopback port is required. `MYIS_MLFLOW_STORE` is a maintenance
override for the safe external store and must never point at `mlflow-p1` during
projection acceptance.
