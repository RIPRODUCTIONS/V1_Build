#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Creating Python venv"
python3 -m venv "$ROOT_DIR/.venv" || true
source "$ROOT_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt"

echo "==> Ensuring Redis is reachable (optional)"
if command -v redis-cli >/dev/null 2>&1; then
  redis-cli ping || true
else
  echo "Redis CLI not found; ensure REDIS_URL is reachable"
fi

echo "==> Initializing database"
python3 - <<'PY'
from core.db import init_db
init_db()
print("DB initialized")
PY

echo "==> Setup complete"







