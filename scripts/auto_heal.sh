#!/usr/bin/env bash
set -Eeuo pipefail

HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
RESTART_CMD="${RESTART_CMD:-DETACH=1 scripts/dev_up.sh}"
MAX_RETRIES="${MAX_RETRIES:-3}"
SLEEP_SECS="${SLEEP_SECS:-5}"

echo "↪ auto-heal: probing $HEALTH_URL"
for i in $(seq 1 "$MAX_RETRIES"); do
  code=$(curl -sS -m 3 -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo "✓ healthy"
    exit 0
  fi
  echo "✖ unhealthy (try $i/$MAX_RETRIES); http=$code"
  sleep "$SLEEP_SECS"
done

echo "⚠ restarting service…"
eval $RESTART_CMD || true

echo "↪ verifying after restart…"
code=$(curl -sS -m 5 -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
[[ "$code" == "200" ]] && echo "✓ recovered" && exit 0

echo "✖ still unhealthy. attempting queue clear (optional)…"
# Example: clear Celery stuck tasks if you use Celery (safe no-op if not present)
if command -v celery >/dev/null 2>&1; then
  celery -A app.celery_app purge -f || true
fi

exit 1
