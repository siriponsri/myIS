# Read-Only MLflow Viewer

This folder contains the Owner-facing launcher for the local MLflow 3.14.0
mirror. The UI is a rebuildable projection only. Git, validated run bundles,
and immutable manifests remain canonical.

## Start

Run from Git Bash on Windows, not WSL:

```bash
cd /c/Users/Siripon\ Sri/Desktop/My_Research/00_Projects/00_myIS/01_Research
bash 06_forntend/mlflow/mlflow.sh doctor
bash 06_forntend/mlflow/mlflow.sh start
```

Open `http://127.0.0.1:5000`. The server runs in the foreground and stops with
Ctrl+C. Use `status` or `url` for a machine-readable state or URL. Set an
alternative absolute store/port with `MYIS_MLFLOW_STORE` and
`MYIS_MLFLOW_PORT`.

If the governed mirror store does not exist, run:

```bash
bash 06_forntend/mlflow/mlflow.sh bootstrap
```

Bootstrap uses the repository's locked environment and canonical bootstrap
script. The launcher never runs `uv sync`, installs packages, or accesses the
network.

## Security Boundary

- The backend SQLite URI is `sqlite+pysqlite:///file:...?mode=ro&uri=true`.
- Only loopback requests with an allowlisted Host and same-origin Origin pass.
- Only UI/static, health/version, experiment/run reads and searches, metric
  history, and safe artifact reads are exposed.
- Create, update, delete, log, upload, gateway, jobs, telemetry writes,
  GraphQL, unknown routes, protected artifact names, and route/version drift
  fail closed.
- Responses use `no-store`, deny framing, and remove CORS headers.
- The viewer rejects a store inside Git, unsafe links/reparse points, invalid
  bootstrap state, artifact URIs outside the approved root, and initialization
  that changes the database hash.

Do not use the MLflow UI to create scientific truth. Rebuild the mirror from
canonical validated sources if it is lost or corrupt.
