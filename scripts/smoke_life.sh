#!/usr/bin/env bash
set -euo pipefail

# Simple smoke to verify life routes and metrics.
# Starts API if not running, mints a JWT, triggers a life route, and checks metrics increment.

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
JWT_SECRET="${JWT_SECRET:-change-me}"

start_api() {
  if curl -sf "${API_BASE_URL}/health" >/dev/null 2>&1; then
    echo "API already running at ${API_BASE_URL}"
    return 0
  fi
  echo "Starting API..."
  (
    cd backend
    nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > ../.smoke_api.log 2>&1 &
    echo $! > ../.smoke_api.pid
  )
  for i in {1..30}; do
    if curl -sf "${API_BASE_URL}/health" >/dev/null 2>&1; then
      echo "API is healthy"
      return 0
    fi
    sleep 1
  done
  echo "API failed to become healthy" >&2
  exit 1
}

mint_token() {
  python3 - <<PY
from app.security.jwt_hs256 import HS256JWT
from app.core.config import get_settings
import os

secret = os.environ.get("JWT_SECRET", "change-me")
helper = HS256JWT(secret=secret)
print(helper.mint(subject="smoke-user", ttl_override_seconds=300))
PY
}

trigger_life() {
  local token="$1"
  curl -sf -X POST \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d '{}' \
    "${API_BASE_URL}/life/calendar/organize" | jq -r '.run_id' >/dev/null
}

check_metrics() {
  local before after
  before=$(curl -sf "${API_BASE_URL}/metrics" | awk -F' ' '/^life_requests_total\{/ {sum+=$2} END {print sum+0}')
  trigger_life "$1"
  sleep 1
  after=$(curl -sf "${API_BASE_URL}/metrics" | awk -F' ' '/^life_requests_total\{/ {sum+=$2} END {print sum+0}')
  echo "life_requests_total before=${before} after=${after}"
  if [ "${after}" -le "${before}" ]; then
    echo "Metrics did not increase" >&2
    exit 1
  fi
}

main() {
  start_api
  export PYTHONPATH=backend
  tok=$(mint_token)
  check_metrics "${tok}"
  echo "Smoke passed"
}

main "$@"
