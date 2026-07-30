# myIS Local Frontends

This directory contains the local browser surfaces for myIS Research protocol 1.0.
They are operational projections, not canonical research authorities.

## Layout

- `dashboard/` contains the Owner Research Dashboard static frontend and its
  exact content allowlist.
- `mlflow/` contains the separately launched read-only MLflow viewer.

Both services are local-only. They must bind to `127.0.0.1`, use no remote
assets, and must not expose confirmation data or protected evaluation
artifacts. Git and validated immutable artifacts remain authoritative.

Start the Owner Dashboard with:

```powershell
uv run --no-sync myis-dashboard --repository-root . --port 8765
```

Start the read-only MLflow viewer from Git Bash with:

```bash
bash 06_frontend/mlflow/mlflow.sh doctor
bash 06_frontend/mlflow/mlflow.sh start
```

The local URLs are `http://127.0.0.1:8765` and `http://127.0.0.1:5000`.

## One-click Owner use

Open this folder in Windows Explorer and double-click:

- `START_OWNER_CONSOLE.cmd` to start both services and open both browser tabs;
- `STOP_OWNER_CONSOLE.cmd` to stop only these local Owner services.

The launcher detects services that are already running and does not start
duplicates. It never installs packages, runs `uv sync`, or changes canonical
research files.

See the component README in each subdirectory for startup and verification
instructions.
