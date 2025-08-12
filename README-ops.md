# Ops Runner Guide

This document covers the orchestration scripts and Make targets for post-merge and follow-up operational steps.

---

## Prerequisites

Before running these targets, ensure you have:

- **[GitHub CLI (`gh`)](https://cli.github.com/)** installed and authenticated:
  ```bash
  gh auth login
  ```
- **`GH_TOKEN`** set in your environment or repo secrets (for PR creation & semantic-release).
- **Docker** installed and running (for `k6` baseline and ZAP scans).
- **Node.js + npm** installed (for frontend audit steps).
- **Python virtualenv** set up if backend dependencies are needed:

  ```bash
  python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt
  ```

---

## Make Targets

### 1. Post-Merge Runner

Runs Steps 4–10 from the ops checklist:

```bash
make post-merge
```

**Includes:**

- npm audit high-only triage
- Grafana dashboard alignment check
- k6 baseline export
- DB pool/env toggle report
- Route-to-scope docs seed
- Security header Playwright test placeholder
- Release hygiene doc creation & PR push

Stops on **real failures**.
If Step 10 pushes a docs branch, prints & auto-opens the compare link.

---

### 2. Next 5 Orchestrator

Runs the next 5 operational steps (post Steps 4–10):

```bash
make next5
```

**Behavior:**

- Stops on failure and prints remediation instructions.
- Auto-opens compare links for any tiny PRs it creates.

---

### 3. Full Chain

Runs both `post-merge` and `next5` sequentially:

```bash
make all-post-merge
```

**Flow:**

1. Executes Steps 4–10.
2. Executes the next 5 orchestrated steps.
3. Stops on failures with log tail & notes.
4. Auto-opens compare links for any PRs created.

---

## Expected Outputs

- **Pass:** ✅ messages for each step, followed by PR compare links (if any).
- **Fail:** ❌ messages for blocking steps, with last 50 lines of logs.
- **Report-only steps:** Always show info but never fail the run.

---

## Troubleshooting

- **Missing `gh` command:** Install [GitHub CLI](https://cli.github.com/) and re-run.
- **No compare link after Step 10:** This means no docs changes were staged for commit.
- **ZAP/k6 skipped:** Will be skipped locally if Docker isn’t available; runs fully in CI.
- **Permission denied for scripts:** Ensure scripts are executable:

  ```bash
  chmod +x scripts/ops/*.sh
  ```

---

**Branch Protection Reminder**
After merges, enforce branch protection:

```bash
REPO=RIPRODUCTIONS/V1_Build BRANCH=master ./scripts/ops/enforce_branch_protection.sh
```

---

*Last updated: $(date +"%Y-%m-%d")*
