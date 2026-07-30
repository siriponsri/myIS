#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
RESEARCH_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

command -v uv >/dev/null 2>&1 || { printf 'ERROR: uv is required\n' >&2; exit 2; }
exec uv run --no-sync myis-report sync --repository-root "$RESEARCH_ROOT"
