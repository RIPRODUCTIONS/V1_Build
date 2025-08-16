#!/usr/bin/env bash
set -euo pipefail

BASE=${BASE:-http://127.0.0.1:8001}
API_KEY=${API_KEY:-dev-key}

echo "==> /health"
curl -sS "$BASE/health" | python -m json.tool

echo "==> /ready"
curl -sS "$BASE/ready" | python -m json.tool

echo "==> enqueue sample task"
curl -sS -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"agent_id":"ai_ceo","task":{"task_id":"smoke","task_type":"strategic_planning","description":"smoke","priority":"normal","requirements":{},"metadata":{}}}' \
  "$BASE/api/tasks/create" | python -m json.tool

echo "==> DLQ recent"
curl -sS -H "X-API-Key: $API_KEY" "$BASE/api/dlq/recent" | python -m json.tool || true







