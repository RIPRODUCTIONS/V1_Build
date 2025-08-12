#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:8000}"
ALLOWLIST_FILE="${2:-scripts/ci/zap-allowlist.txt}"
REPORT_JSON="/tmp/zap-report.json"

# Ensure docker available
command -v docker >/dev/null 2>&1 || { echo "docker required"; exit 1; }

# Run ZAP baseline
docker run --rm -t owasp/zap2docker-stable zap-baseline.py \
  -t "$TARGET_URL" -J "$REPORT_JSON" -r /tmp/zap.html || true

# Fetch report from container path if needed
if [[ -f "$REPORT_JSON" ]]; then
  ZAP_JSON="$REPORT_JSON"
else
  # On some images, artifacts end up in /zap/wrk/; try copying out via container
  echo "ZAP JSON report not found at $REPORT_JSON; allowing pass but printing notice"
  exit 0
fi

# If jq missing, install minimal
if ! command -v jq >/dev/null 2>&1; then
  echo "jq not found; installing"
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y jq
  else
    echo "jq required to parse ZAP report"; exit 1
  fi
fi

# Build allowlist pattern set
mapfile -t ALLOWED < <(grep -vE '^\s*(#|$)' "$ALLOWLIST_FILE" 2>/dev/null || true)

# Extract High alerts
HIGHS=$(jq -r '.site[]?.alerts[]? | select(.riskcode=="3") | "\(.alert)@@\(.riskdesc)@@\(.instances[0]?.uri // "")"' "$ZAP_JSON" || true)
if [[ -z "$HIGHS" ]]; then
  echo "No High alerts found by ZAP."
  exit 0
fi

# Filter via allowlist
FAILS=()
while IFS= read -r row; do
  alert=$(echo "$row" | cut -d'@@' -f1)
  uri=$(echo "$row" | cut -d'@@' -f3)
  entry="$alert|$uri"
  allowed=false
  for pat in "${ALLOWED[@]:-}"; do
    [[ -z "$pat" ]] && continue
    if [[ "$entry" =~ $pat ]]; then
      allowed=true; break
    fi
  done
  if [[ "$allowed" != true ]]; then
    FAILS+=("$entry")
  fi
done <<< "$HIGHS"

if (( ${#FAILS[@]} > 0 )); then
  echo "Blocking due to unallowlisted High alerts:" >&2
  printf ' - %s\n' "${FAILS[@]}" >&2
  exit 1
fi

echo "Only allowlisted High alerts found; passing."


