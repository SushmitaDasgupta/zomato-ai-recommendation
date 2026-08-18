#!/usr/bin/env bash
# Phase 1 Railway start: ingest catalog if needed, then bind 0.0.0.0:$PORT.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${PYTHONPATH:-$ROOT}"
exec python -m src.app.run
