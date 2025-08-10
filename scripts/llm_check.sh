#!/usr/bin/env bash
set -euo pipefail

API="${API_BASE_URL:-http://127.0.0.1:8000}"
echo "Checking LLM ping at $API/llm/ping"
curl -sS "$API/llm/ping" | sed -e 's/{/{\n  /' -e 's/,/,\n  /g' -e 's/}/\n}/'
