#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
say(){ printf "\033[1;36m› %s\033[0m\n" "$*"; }
cd "$ROOT"

if [[ -f .dev/backend.pid ]]; then
  PID="$(cat .dev/backend.pid || true)"
  if [[ -n "${PID:-}" ]] && kill -0 "$PID" 2>/dev/null; then
    say "Stopping backend (PID $PID)…"
    kill "$PID" 2>/dev/null || true
    sleep 1
  fi
  rm -f .dev/backend.pid
fi

# Belt-and-suspenders kill by pattern
pkill -f "uvicorn.*app\.main:create_app" 2>/dev/null || true
say "Done."
