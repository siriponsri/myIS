#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
RESEARCH_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
MLFLOW_LAUNCHER="$RESEARCH_ROOT/dashboard/mlflow/mlflow.sh"

[[ -f "$MLFLOW_LAUNCHER" ]] || { printf 'ERROR: MLflow launcher is missing: %s\n' "$MLFLOW_LAUNCHER" >&2; exit 2; }
command -v bash >/dev/null 2>&1 || { printf 'ERROR: bash is required\n' >&2; exit 2; }

exec bash "$MLFLOW_LAUNCHER" start
