# Projection Index

`read-model/` is the only generated read model consumed by Dashboard, Brain,
and Paper projections.

## Bash launchers

Run each surface separately from Git Bash:

```bash
bash projections/start-dashboard.sh
bash projections/start-mlflow.sh
bash projections/start-obsidian-report.sh
```

- `start-dashboard.sh`: loopback Dashboard, default port `8765`.
- `start-mlflow.sh`: read-only MLflow viewer, default port `5000`.
- `start-obsidian-report.sh`: rebuilds Research read model and generated reports for `02_Brain`, local Obsidian projection, and Paper.

Dashboard and MLflow remain foreground processes. Stop them with `Ctrl-C`.
Set `MYIS_DASHBOARD_PORT`, `MYIS_MLFLOW_PORT`, and `MYIS_MLFLOW_STORE` when a non-default local configuration is required.
