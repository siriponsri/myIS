#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
APP="$SCRIPT_DIR/readonly_app.py"
WORKSPACE_ROOT="$(cd "$REPOSITORY_ROOT/../../.." && pwd -P)"
DEFAULT_STORE="$WORKSPACE_ROOT/01_Stores/00_myIS/mlflow"
STORE_ROOT="${MYIS_MLFLOW_STORE:-$DEFAULT_STORE}"
PORT="${MYIS_MLFLOW_PORT:-5000}"

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 2
}

case "$(uname -s 2>/dev/null || true)" in
  *[Mm]icrosoft*|*WSL*) fail "WSL is not supported; run this launcher from Git Bash on Windows" ;;
esac
if [[ -r /proc/version ]] && grep -qiE 'microsoft|wsl' /proc/version; then
  fail "WSL is not supported; run this launcher from Git Bash on Windows"
fi
[[ "$PORT" =~ ^[0-9]+$ ]] || fail "MYIS_MLFLOW_PORT must be an integer"
(( PORT >= 1 && PORT <= 65535 )) || fail "MYIS_MLFLOW_PORT must be between 1 and 65535"
command -v uv >/dev/null 2>&1 || fail "uv is required; this launcher never installs dependencies"
[[ -f "$APP" ]] || fail "read-only viewer entry point is missing"

run_app() {
  uv run --no-sync python "$APP" "$1" \
    --store-root "$STORE_ROOT" \
    --repository-root "$REPOSITORY_ROOT" \
    --port "$PORT"
}

usage() {
  printf '%s\n' \
    "Usage: bash dashboard/mlflow/mlflow.sh {doctor|bootstrap|start|status|url}" \
    "" \
    "Environment:" \
    "  MYIS_MLFLOW_STORE  Absolute persistent store outside Git" \
    "  MYIS_MLFLOW_PORT   Loopback port (default: 5000)"
}

command_name="${1:-}"
case "$command_name" in
  doctor)
    uv run --no-sync python "$REPOSITORY_ROOT/scripts/mlflow_doctor.py" --repository-root "$REPOSITORY_ROOT" --store-root "$STORE_ROOT"
    ;;
  bootstrap)
    run_app target
    uv run --no-sync python -c 'import mlflow,sys; assert sys.version_info[:2] == (3, 11); assert mlflow.__version__ == "3.14.0"'
    uv run --no-sync python "$REPOSITORY_ROOT/scripts/bootstrap_mlflow.py" \
      --repository-root "$REPOSITORY_ROOT" \
      --store-root "$STORE_ROOT"
    run_app doctor
    ;;
  start)
    run_app doctor >/dev/null
    run_app serve
    ;;
  status)
    run_app status
    ;;
  url)
    run_app url
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    fail "unknown command: $command_name"
    ;;
esac
