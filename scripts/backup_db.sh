#!/usr/bin/env bash
set -euo pipefail

DATE=$(date +%F_%H-%M-%S)
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL not set" >&2
  exit 1
fi
if [[ -z "${S3_ENDPOINT_URL:-}" || -z "${S3_BUCKET:-}" ]]; then
  echo "S3_ENDPOINT_URL or S3_BUCKET not set" >&2
  exit 1
fi

pg_dump "$DATABASE_URL" > "/tmp/db_${DATE}.sql"
aws --endpoint-url "$S3_ENDPOINT_URL" s3 cp "/tmp/db_${DATE}.sql" "s3://${S3_BUCKET}/backups/db_${DATE}.sql"

