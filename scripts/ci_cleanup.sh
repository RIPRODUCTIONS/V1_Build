#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
if [ -z "${CI_CLEANUP_TOKEN:-}" ]; then
  echo "CI_CLEANUP_TOKEN not set; skipping cleanup."
  exit 0
fi

echo "Calling cleanup at ${API_BASE_URL}/admin/cleanup/all"
curl -fsSL -X DELETE \
  -H "X-CI-Token: ${CI_CLEANUP_TOKEN}" \
  "${API_BASE_URL}/admin/cleanup/all" \
  || { echo "Cleanup call failed"; exit 0; }
echo "Cleanup done."
