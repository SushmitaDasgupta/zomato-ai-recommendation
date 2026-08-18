#!/usr/bin/env bash
# Start Tablepick Next.js using a project-local Node if system Node is missing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -x "$ROOT/.tools/node/bin/node" ]; then
  export PATH="$ROOT/.tools/node/bin:$PATH"
fi
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Install Node 18+ or place a binary at .tools/node/bin/node" >&2
  exit 1
fi
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install
fi
exec npm run dev -- --hostname 0.0.0.0 --port 3000
