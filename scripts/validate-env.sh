#!/usr/bin/env bash
set -euo pipefail

echo "Validating Builder platform environment..."
required_vars=("INTERNAL_API_KEY" "DATABASE_URL" "REDIS_URL")
missing=0
for var in "${required_vars[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "❌ Required environment variable $var is not set"
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  exit 1
fi
echo "✅ All required environment variables are set"


