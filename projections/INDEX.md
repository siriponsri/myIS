# Projection Index

`read-model/` is the only generated read model consumed by Dashboard, Brain,
and Paper projections.

## One-click launchers

Double-click these files in Windows Explorer:

- `open-dashboard.cmd`: starts the loopback Dashboard and opens `http://127.0.0.1:8765`.
- `open-mlflow.cmd`: starts the read-only MLflow viewer for the external active store (`01_Stores/00_myIS/mlflow-p1`) and opens `http://127.0.0.1:5000`.
- `open-obsidian-report.cmd`: rebuilds the read model and generated reports, then opens the `02_Brain` Obsidian vault.
- `run-legacy-p1.cmd`: certifies the legacy DAPFAM tree and runs only P1 `R0/R0-W` on train/selection inside the owner-local process.

Set `MYIS_DASHBOARD_PORT`, `MYIS_MLFLOW_PORT`, or `MYIS_MLFLOW_STORE` before launching when a non-default local configuration is required. Dashboard and MLflow run in minimized PowerShell windows; close those windows to stop the services.
