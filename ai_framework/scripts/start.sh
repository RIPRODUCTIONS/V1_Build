#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/.venv/bin/activate" 2>/dev/null || true

export API_KEY=${API_KEY:-dev-key}
export REDIS_URL=${REDIS_URL:-redis://127.0.0.1:6379/0}
export ENABLE_SCHEDULER=${ENABLE_SCHEDULER:-1}

nohup python3 server.py > server.out 2>&1 & echo $! > server.pid
echo "Server started (pid $(cat server.pid))"







