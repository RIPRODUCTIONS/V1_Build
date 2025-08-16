#!/usr/bin/env bash
set -euo pipefail

TMP=$(mktemp)
printf '%s' '{"topics":["digital forensics timeline","apt tracking","insurance fraud signals"]}' > "$TMP"

curl -sS -X POST http://127.0.0.1:8000/assistant/expand_coverage \
  -H 'Content-Type: application/json' -H "X-API-Key: ${INTERNAL_API_KEY}" \
  --data-binary @"$TMP"

echo


