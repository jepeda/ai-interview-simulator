#!/usr/bin/env bash
# macOS / Linux setup. Windows: use setup.cmd
set -euo pipefail
cd "$(dirname "$0")"

missing=0
command -v uv >/dev/null || { echo "Missing uv:   brew install uv   (or: curl -LsSf https://astral.sh/uv/install.sh | sh)"; missing=1; }
command -v node >/dev/null || { echo "Missing Node.js 20+:   brew install node"; missing=1; }
[ "$missing" -eq 0 ] || exit 1

echo "==> uv sync (Python 3.12 + backend deps)"; uv sync
echo "==> npm install (root tools)"; npm install --no-fund --no-audit
echo "==> npm install (frontend)"; npm install --prefix frontend --no-fund --no-audit
echo "==> exercise working copies"; uv run python scripts/workspace.py init
echo "==> self-check"; uv run pytest backend/tests/trainer -q

echo
echo "Setup complete. Start everything with: ./start.sh"
