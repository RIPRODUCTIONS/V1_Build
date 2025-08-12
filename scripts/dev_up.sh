#!/usr/bin/env bash
set -Eeuo pipefail

# Timestamp function for logging
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
say() { printf "[$(timestamp)] \033[1;36m› %s\033[0m\n" "$*"; }
err() { printf "[$(timestamp)] \033[1;31m✖ %s\033[0m\n" "$*" >&2; }

# Resolve repo root robustly
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load environment if present
if [[ -f .env ]]; then
  say "Loading .env file..."
  # macOS-safe: auto-export variables and source .env (handles quoted values)
  # Also strip potential CRLFs from checked-out files.
  dos2unix_cmd="$(command -v dos2unix || true)"
  if [[ -n "$dos2unix_cmd" ]]; then "$dos2unix_cmd" -q .env || true; fi
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Configuration
HOST="${HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-20}"
AUTO_KILL="${AUTO_KILL:-0}"
# Optional modes
DETACH="${DETACH:-0}"             # 1 = start and exit once healthy
DEBUG_STARTUP="${DEBUG_STARTUP:-0}" # 1 = verbose curl + extra diagnostics
DISABLE_LIFESPAN="${DISABLE_LIFESPAN:-0}" # 1 = uvicorn --lifespan off

# Create required directories
mkdir -p "$ROOT/logs"
mkdir -p "$ROOT/.dev"

# Log file setup
LOG_FILE="$ROOT/logs/dev_up.log"
exec > >(tee -a "$LOG_FILE") 2>&1
export PYTHONUNBUFFERED=1  # flush python logs quickly

say "🚀 Starting backend development server..."

# 0) Pre-flight doctor check
say "Running pre-flight checks..."
CHECK_FRONTEND=0 "$ROOT/scripts/doctor.sh" || exit $?

# 0.1) Ensure venv python & uvicorn are available
if [[ ! -x "$ROOT/backend/.venv/bin/python" ]]; then
  err "Python venv missing: $ROOT/backend/.venv/bin/python not found."
  err "Run: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
if ! "$ROOT/backend/.venv/bin/python" -m uvicorn --help >/dev/null 2>&1; then
  err "uvicorn not installed in venv."
  err "Run: cd backend && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 1) Smoke test (import and build app)
say "Running smoke test..."
if [[ -f "$ROOT/backend/scripts/smoke_check.py" ]]; then
  if ! "$ROOT/backend/.venv/bin/python" "$ROOT/backend/scripts/smoke_check.py"; then
    err "❌ Smoke test failed - app cannot be imported or built"
    err "Check the error above and fix import issues before starting server"
    exit 5
  fi
else
  say "No smoke_check.py found; performing quick import probe..."
  if ! "$ROOT/backend/.venv/bin/python" - <<'PY'
import importlib, sys
try:
    mod = importlib.import_module("app.main")
    # try both patterns; don't run server
    if hasattr(mod, "create_app"):
        app = mod.create_app()
    elif hasattr(mod, "app"):
        app = mod.app
    else:
        raise AttributeError("Neither create_app() nor app found in app.main")
except Exception as e:
    import traceback; traceback.print_exc(); sys.exit(1)
PY
  then
    err "❌ Import probe failed. Consider adding backend/scripts/smoke_check.py."
    exit 5
  fi
fi

# 2) Kill stale processes safely
say "Checking for stale processes..."
STALE_PIDS=()
while IFS= read -r pid; do
  if [[ -n "$pid" ]]; then
    STALE_PIDS+=("$pid")
  fi
done < <(pgrep -f "uvicorn.*app\.main:create_app" 2>/dev/null || true)

if [[ ${#STALE_PIDS[@]} -gt 0 ]]; then
  say "Found ${#STALE_PIDS[@]} stale uvicorn process(es): ${STALE_PIDS[*]}"
  if [[ "$AUTO_KILL" == "1" ]]; then
    say "AUTO_KILL=1 → killing stale processes..."
    for pid in "${STALE_PIDS[@]}"; do
      kill "$pid" 2>/dev/null || true
    done
    sleep 1
  else
    err "Export AUTO_KILL=1 to terminate them automatically, or run: kill ${STALE_PIDS[*]}"
    err "Pattern used to find them: 'uvicorn.*app.main:create_app'"
    exit 2
  fi
fi

# 3) Start uvicorn with explicit args
say "Starting Uvicorn on http://$HOST:$BACKEND_PORT..."
cd "$ROOT/backend"

# Activate venv and set environment
source .venv/bin/activate
export SKIP_DB_INIT="${SKIP_DB_INIT:-true}"
export ALLOW_START_WITHOUT_REDIS="${ALLOW_START_WITHOUT_REDIS:-true}"
export CELERY_EAGER="${CELERY_EAGER:-true}"

# Decide lifespan flag
LIFEFLAG=()
if [[ "$DISABLE_LIFESPAN" == "1" ]]; then
  LIFEFLAG+=(--lifespan off)
fi

# Start uvicorn in background with explicit args
python -m uvicorn "app.main:create_app" \
  --factory \
  --host "$HOST" \
  --port "$BACKEND_PORT" \
  --log-level debug \
  --reload \
  "${LIFEFLAG[@]}" \
  >"$ROOT/logs/backend-dev.log" 2>&1 &
UV_PID=$!

# Write PID to file
echo "$UV_PID" > "$ROOT/.dev/backend.pid"

# Cleanup function (must preserve original exit code)
cleanup() {
  say "Cleaning up..."
  if [[ -f "$ROOT/.dev/backend.pid" ]]; then
    PID_FROM_FILE=$(cat "$ROOT/.dev/backend.pid")
    if kill -0 "$PID_FROM_FILE" 2>/dev/null; then
      kill "$PID_FROM_FILE" 2>&1 >/dev/null || true
    fi
    rm -f "$ROOT/.dev/backend.pid"
  fi
  # Also kill by pattern as backup
  pkill -f "uvicorn.*app\.main:create_app" 2>/dev/null || true
}

# Set trap for cleanup, but re-emit the original exit code
trap 'rc=$?; cleanup; exit $rc' EXIT INT TERM

# 4) Health poll loop (no GNU timeout)
say "Waiting for health check (timeout: ${STARTUP_TIMEOUT}s)..."
deadline=$((SECONDS + STARTUP_TIMEOUT))

while true; do
  # Try health endpoints in order
  for endpoint in "/health" "/healthz" "/"; do
    CODE="$(curl -s ${DEBUG_STARTUP:+-v} -o /dev/null -w "%{http_code}" --connect-timeout 1 --max-time 2 "http://$HOST:$BACKEND_PORT$endpoint" || echo "000")"
    if [[ "$CODE" == "200" || "$CODE" == "204" || "$CODE" == "302" ]]; then
      say "✅ Health check passed (${CODE}) at: $endpoint"
      say "🚀 Backend ready at http://$HOST:$BACKEND_PORT (PID: $UV_PID)"
      say "📝 Logs: $ROOT/logs/backend-dev.log"
      if [[ "$DETACH" == "1" ]]; then
        say "Detaching (DETACH=1)."
        exit 0
      else
        say "🛑 Ctrl+C to stop (tailing logs)…"
        # Tail logs until process exits (macOS-safe)
        tail -f "$ROOT/logs/backend-dev.log" &
        TAIL_PID=$!
        wait "$UV_PID"
        kill "$TAIL_PID" 2>/dev/null || true
        exit $?
      fi
    elif [[ "$CODE" != "000" ]]; then
      [[ "$DEBUG_STARTUP" == "1" ]] && err "Probe ${endpoint} → HTTP ${CODE}"
    fi
  done

  # Extra: is the TCP socket open yet?
  if command -v nc >/dev/null 2>&1; then
    if nc -z "$HOST" "$BACKEND_PORT" 2>/dev/null; then
      [[ "$DEBUG_STARTUP" == "1" ]] && say "TCP port $BACKEND_PORT is open; waiting for healthy response…"
    fi
  fi
  
  # Check if uvicorn died
  if ! kill -0 "$UV_PID" 2>/dev/null; then
    err "❌ Uvicorn exited during startup"
    err "Last 200 lines of log:"
    tail -n 200 "$ROOT/logs/backend-dev.log" || true
    err "Check $ROOT/logs/backend-dev.log for details"
    exit 3
  fi
  
  # Check timeout
  if (( SECONDS > deadline )); then
    err "❌ Health check failed after ${STARTUP_TIMEOUT}s"
    err "Last 200 lines of log:"
    tail -n 200 "$ROOT/logs/backend-dev.log" || true
    err "💡 Tips:"
    err "   - Increase STARTUP_TIMEOUT=30 if models take time to warm up"
    err "   - Check $ROOT/logs/backend-dev.log for startup errors"
    err "   - Run scripts/doctor.sh to check system state"
    err "   - Set DEBUG_STARTUP=1 for verbose probes"
    err "   - Try DISABLE_LIFESPAN=1 if startup events hang"
    exit 4
  fi
  
  sleep 0.5
done
