#!/usr/bin/env bash
# Starts the trainer API (:8710), the clinic, booking and payouts APIs (:8711-:8713) and the dashboard (:5173). Ctrl+C stops all.
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules ] && [ -d frontend/node_modules ] && [ -d .venv ] || { echo "Run ./setup.sh first"; exit 1; }
TRAINER_OPEN_BROWSER=1 exec npm run dev
