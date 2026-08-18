#!/usr/bin/env bash
# Phase 1 Railway start: ingest catalog if needed, then bind 0.0.0.0:$PORT.
# Nixpacks puts deps in /opt/venv; `bash script.sh` does not source .profile,
# so PATH must include the venv or imports (fastapi/pandas) fail immediately.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${PYTHONPATH:-$ROOT}"
if [ -x /opt/venv/bin/python ]; then
  export PATH="/opt/venv/bin:${PATH}"
fi
echo "start-api: python=$(command -v python) PORT=${PORT:-8000} ROOT=${ROOT}" >&2
exec python -m src.app.run
