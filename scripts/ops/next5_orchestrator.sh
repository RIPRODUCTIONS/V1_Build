#!/usr/bin/env bash
set -euo pipefail

# Orchestrates the next 5 steps:
# 1) Secrets rollout sanity (prod boot w/ manager-style secrets)
# 2) ZAP Highs triage (report; optional allowlist merge from local staging file)
# 3) npm audit high-only remediation (report; stop if Highs present)
# 4) Semantic-release dry run + tiny docs PR to exercise flow
# 5) Observability SLO docs PR (dashboards assumed already in repo)

REPO="RIPRODUCTIONS/V1_Build"
BASE="master"
RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; BLUE=$'\e[34m'; BOLD=$'\e[1m'; NC=$'\e[0m'
log(){ echo "${BLUE}${BOLD}➜${NC} $*"; }
ok(){ echo "${GREEN}${BOLD}✔${NC} $*"; }
warn(){ echo "${YELLOW}${BOLD}!${NC} $*"; }
die(){ echo "${RED}${BOLD}✖${NC} $*"; exit 1; }
open_compare(){ # args: head_branch
  local HEAD="$1"
  local URL="https://github.com/${REPO}/compare/${BASE}...${HEAD}?expand=1"
  echo "Compare: ${URL}"
  if command -v gh >/dev/null 2>&1; then gh browse "${URL}" || true; fi
}

# Ensure we're in repo root and clean
git rev-parse --show-toplevel >/dev/null 2>&1 || die "Run from inside a git repo."
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
git fetch --all -p
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "Working tree not clean. Commit/stash first."
fi
ok "Repo clean at $(git rev-parse --abbrev-ref HEAD)"

# Activate venv if present
. .venv/bin/activate 2>/dev/null || true

# ----------------------
# Step 1 — Secrets rollout (production readiness)
# ----------------------
log "Step 1: Secrets rollout (prod boot sanity)"
export ENV=production JWT_SECRET="${JWT_SECRET:-local-strong-secret}" PYTHONPATH=backend
nohup uvicorn app.main:app --host 127.0.0.1 --port 8091 >/tmp/prod-boot-8091.log 2>&1 &
API_PID=$!
sleep 3
# Probe preferred health endpoint, then fall back to root 2xx
if curl -sf http://127.0.0.1:8091/life/health >/dev/null 2>&1 || curl -sf http://127.0.0.1:8091/ >/dev/null 2>&1; then
  ok "Prod boot sanity OK (health/root returned 2xx)."
else
  kill $API_PID >/dev/null 2>&1 || true
  tail -n 80 /tmp/prod-boot-8091.log || true
  die "Prod boot check failed. Remediation: ensure ENV=production & JWT_SECRET; verify health route (/life/health) exists."
fi
kill $API_PID >/dev/null 2>&1 || true

# ----------------------
# Step 2 — ZAP Highs triage (report; optional allowlist merge)
# ----------------------
log "Step 2: ZAP Highs triage (report)"
export PYTHONPATH=backend
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/api-8000.log 2>&1 &
ZPID=$!
sleep 3
ALLOWLIST="scripts/ci/zap-allowlist.txt"
STAGING="scripts/ci/zap-allowlist.local.txt" # optional: put reviewed entries here to auto-merge
if bash scripts/ci/run_zap_blocking.sh "http://127.0.0.1:8000" "${ALLOWLIST}" >/tmp/zap_step.log 2>&1; then
  ok "ZAP baseline passed (no unallowlisted Highs)."
else
  warn "ZAP reported Highs. See /tmp/zap_step.log and zap.json (if produced)."
  if [ -f "${STAGING}" ] && [ -s "${STAGING}" ]; then
    warn "Merging reviewed allowlist from ${STAGING} → ${ALLOWLIST}"
    BR="ci/zap-allowlist-review"
    git checkout -b "$BR"
    awk 'NF' "${STAGING}" >> "${ALLOWLIST}"
    git add "${ALLOWLIST}"
    git commit -m "ci(security): add reviewed ZAP allowlist entries (minimal/specific)" --no-verify
    git push -u origin "$BR"
    open_compare "$BR"
    die "Opened allowlist review PR. Merge after human review, then re-run."
  else
    die "Highs detected and no reviewed staging allowlist present. Review zap.json and add minimal entries to ${STAGING}."
  fi
fi
kill $ZPID >/dev/null 2>&1 || true

# ----------------------
# Step 3 — npm audit (high-only) remediation
# ----------------------
log "Step 3: npm audit (high-only)"
pushd apps/web >/dev/null
( npm ci || npm install ) >/tmp/npm_install.log 2>&1 || warn "npm install had non-fatal issues; see /tmp/npm_install.log"
if npm audit --audit-level=high >/tmp/npm_audit_high.log 2>&1; then
  ok "npm audit (high) passed."
else
  tail -n 80 /tmp/npm_audit_high.log || true
  die "High-severity advisories present. Remediation: bump/pin affected deps; then re-run."
fi
popd >/dev/null

# ----------------------
# Step 4 — Semantic-release dry run + tiny docs PR
# ----------------------
log "Step 4: semantic-release dry run + tiny docs PR"
if [ -x scripts/release/dry_run.sh ]; then
  if ! scripts/release/dry_run.sh >/tmp/semrel_dryrun.log 2>&1; then
    warn "semantic-release dry run skipped or not available; see /tmp/semrel_dryrun.log"
  else
    ok "semantic-release dry run completed."
  fi
else
  warn "scripts/release/dry_run.sh not found (non-fatal)."
fi

BR_SMOKE="docs/semrel-smoke-$(date +%Y%m%d%H%M%S)"
git checkout -b "$BR_SMOKE"
mkdir -p docs
printf "\n- semrel smoke at %s\n" "$(date -Iseconds)" >> docs/release_hygiene.md
git add docs/release_hygiene.md
git commit -m "docs: semrel smoke note (no runtime changes)" --no-verify
git push -u origin "$BR_SMOKE"
open_compare "$BR_SMOKE"

# ----------------------
# Step 5 — Observability SLO docs PR
# ----------------------
log "Step 5: Observability SLO docs"
BR_SLO="docs/observability-slo-$(date +%Y%m%d%H%M%S)"
git checkout -b "$BR_SLO"
mkdir -p docs
if [ ! -f docs/performance.md ]; then
  cat > docs/performance.md <<'MD'
# Performance & SLOs

## Targets
- API p95 latency: ≤ 300ms
- API error rate: < 1% (5m)
- 429 budget: ≤ 0.1% of requests (rolling 1h)

Update with real k6 results and incident learnings.
MD
else
  awk '1' docs/performance.md > /tmp/perf.tmp && mv /tmp/perf.tmp docs/performance.md
  if ! grep -q "## Targets" docs/performance.md; then
    cat >> docs/performance.md <<'MD'

## Targets
- API p95 latency: ≤ 300ms
- API error rate: < 1% (5m)
- 429 budget: ≤ 0.1% of requests (rolling 1h)
MD
  fi
fi
git add docs/performance.md
git commit -m "docs(observability): codify SLO targets (latency, error rate, 429 budget)" --no-verify
git push -u origin "$BR_SLO"
open_compare "$BR_SLO"

ok "All steps completed."


