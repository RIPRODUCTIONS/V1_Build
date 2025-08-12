#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HOST="${HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
CHECK_FRONTEND="${CHECK_FRONTEND:-1}"

say() { printf "\033[1;36m› %s\033[0m\n" "$*"; }
err() { printf "\033[1;31m✖ %s\033[0m\n" "$*" >&2; }
warn() { printf "\033[1;33m⚠ %s\033[0m\n" "$*" >&2; }

say "🔍 Pre-flight Doctor Check"

# 0) Check required tools
say "Checking required tools..."
if ! command -v lsof >/dev/null 2>&1; then
  err "❌ Missing lsof"
  say "Fix: brew install lsof"
  exit 10
fi

# 1) Check Python venv
say "Checking Python venv..."
if [[ ! -d backend/.venv ]]; then
  err "❌ Missing backend/.venv"
  say "Fix: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 2) Check Python usability
say "Checking Python usability..."
if ! backend/.venv/bin/python --version >/dev/null 2>&1; then
  err "❌ Python not usable in .venv"
  say "Fix: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 3) Check dependencies
say "Checking dependencies..."
if [[ -f backend/requirements.txt ]]; then
  if ! backend/.venv/bin/python -m pip check >/dev/null 2>&1; then
    warn "⚠ Broken dependencies detected"
    say "Run: cd backend && source .venv/bin/activate && pip install -r requirements.txt"
  fi
fi

# 4) Check backend port
say "Checking backend port $BACKEND_PORT..."
if lsof -n -i :"$BACKEND_PORT" -sTCP:LISTEN -Fp >/dev/null 2>&1; then
  PID="$(lsof -n -i :"$BACKEND_PORT" -sTCP:LISTEN -Fp | sed 's/p//')"
  CMD="$(ps -o command= -p "$PID" 2>/dev/null || true)"
  err "❌ Port $BACKEND_PORT is busy (PID $PID)"
  [[ -n "$CMD" ]] && say "→ $CMD"
  say "Fix: AUTO_KILL=1 scripts/dev_up.sh or kill $PID"
  exit 2
fi

# 5) Check frontend port (optional)
if [[ "$CHECK_FRONTEND" == "1" ]]; then
  say "Checking frontend port $FRONTEND_PORT..."
  if lsof -n -i :"$FRONTEND_PORT" -sTCP:LISTEN -Fp >/dev/null 2>&1; then
    PID="$(lsof -n -i :"$FRONTEND_PORT" -sTCP:LISTEN -Fp | sed 's/p//')"
    CMD="$(ps -o command= -p "$PID" 2>/dev/null || true)"
    err "❌ Port $FRONTEND_PORT is busy (PID $PID)"
    [[ -n "$CMD" ]] && say "→ $CMD"
    say "Fix: AUTO_KILL=1 scripts/web_up.sh or kill $PID"
    exit 3
  fi
fi

say "✅ All pre-flight checks passed."
