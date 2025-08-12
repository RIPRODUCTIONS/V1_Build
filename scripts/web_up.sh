#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/apps/web"

PORT="${PORT:-3000}"
AUTO_KILL="${AUTO_KILL:-0}"

say() { printf "\033[1;35m› %s\033[0m\n" "$*"; }

# Pre-flight doctor check
say "Running pre-flight checks…"
"$ROOT/scripts/doctor.sh" || exit $?

# Port check (already checked by doctor, but handle auto-kill)
if lsof -n -i :"$PORT" -sTCP:LISTEN -Fp >/dev/null 2>&1; then
  PID="$(lsof -n -i :"$PORT" -sTCP:LISTEN -Fp | sed 's/p//')"
  say "Port :$PORT busy (PID $PID)"
  if [[ "$AUTO_KILL" == "1" ]]; then
    say "AUTO_KILL=1 → killing $PID"
    kill "$PID" && sleep 0.5
  else
    say "Export AUTO_KILL=1 to terminate it automatically, or run: kill $PID"
    exit 2
  fi
fi

say "Starting Next.js on http://127.0.0.1:$PORT …"
npm run dev
