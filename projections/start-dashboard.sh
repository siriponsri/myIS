#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
RESEARCH_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
PORT="${MYIS_DASHBOARD_PORT:-8765}"

[[ "$PORT" =~ ^[0-9]+$ ]] || { printf 'ERROR: MYIS_DASHBOARD_PORT must be an integer\n' >&2; exit 2; }
(( PORT >= 1024 && PORT <= 65535 )) || { printf 'ERROR: dashboard port must be 1024-65535\n' >&2; exit 2; }
command -v uv >/dev/null 2>&1 || { printf 'ERROR: uv is required\n' >&2; exit 2; }

exec uv run --no-sync myis-dashboard --repository-root "$RESEARCH_ROOT" --port "$PORT"
