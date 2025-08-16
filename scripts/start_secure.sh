#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${INTERNAL_API_KEY:-}" ]; then
  export INTERNAL_API_KEY=$(python3 - <<'PY'
import secrets;print(secrets.token_hex(16))
PY
)
  echo "Generated INTERNAL_API_KEY: $INTERNAL_API_KEY"
fi

export SECURE_MODE=${SECURE_MODE:-true}

docker-compose up --build -d
echo "Stack started. API at http://localhost:8000, Web at http://localhost:3000"

