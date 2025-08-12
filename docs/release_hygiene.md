# Release Hygiene

Pre-release checklist:
- CI all-green (Ruff=0 warnings, pytest green)
- ZAP Highs: none or allowlisted with justification
- npm audit high: 0
- Semantic-release dry-run (scripts/release/dry_run.sh) outputs next version
- Grafana dashboards updated if metrics changed

After merge to master:
- Semantic-release publishes GitHub Release and updates CHANGELOG.md
- For hotfix: branch fix/*, conventional commit title, merge after checks

- semrel smoke at 2025-08-12T14:03:43-05:00
