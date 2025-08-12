#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <backup_filename>" >&2
  exit 1
fi
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL not set" >&2
  exit 1
fi

aws --endpoint-url "$S3_ENDPOINT_URL" s3 cp "s3://${S3_BUCKET}/backups/$1" /tmp/restore.sql
psql "$DATABASE_URL" -f /tmp/restore.sql

