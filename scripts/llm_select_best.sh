#!/usr/bin/env bash
set -euo pipefail
API="${API_BASE_URL:-http://127.0.0.1:8000}"
curl -sS -X POST "$API/llm/select_best" -H 'content-type: application/json' | sed -e 's/{/{\n  /' -e 's/,/,\n  /g' -e 's/}/\n}/'
