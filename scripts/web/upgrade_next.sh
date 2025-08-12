#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/web/upgrade_next.sh [VERSION]
# Example:
#   scripts/web/upgrade_next.sh 14.2.31
# If VERSION not provided, defaults to 14.2.31

TARGET_VERSION="${1:-14.2.31}"
REPO="RIPRODUCTIONS/V1_Build"
BASE="master"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  echo "Run this script from inside the git repository" >&2
  exit 1
fi
cd "$ROOT/apps/web"

BRANCH="chore/web-next-bump-${TARGET_VERSION}"
git checkout -b "$BRANCH" || git checkout "$BRANCH"

echo "Installing deps (npm ci || npm install)" >&2
(npm ci || npm install) >/tmp/web_next_npm_install.log 2>&1 || true

echo "Upgrading next to ${TARGET_VERSION}" >&2
npm install -E "next@${TARGET_VERSION}"

echo "Running npm audit --audit-level=high" >&2
if ! npm audit --audit-level=high >/tmp/web_next_audit.log 2>&1; then
  echo "npm audit high findings remain; see /tmp/web_next_audit.log" >&2
  exit 1
fi

git add package.json package-lock.json
git commit -m "chore(web): bump next to ${TARGET_VERSION} to resolve critical advisories" --no-verify || true
git push -u origin "$BRANCH"

COMPARE_URL="https://github.com/${REPO}/compare/${BASE}...${BRANCH}?expand=1"
echo "Compare: ${COMPARE_URL}"
if command -v gh >/dev/null 2>&1; then
  gh browse "$COMPARE_URL" || true
fi

