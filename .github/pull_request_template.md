## Summary

Describe the change, motivation, and scope.

## Security & Quality Checklist
- [ ] No secrets committed (pre-commit gitleaks passes)
- [ ] Backend type checks pass (mypy)
- [ ] Linting/formatting pass (ruff/black, eslint/prettier)
- [ ] New/changed endpoints require `X-API-Key` when `SECURE_MODE=true`
- [ ] Request limits considered (size/timeout/rate)
- [ ] Unit/integration tests added/updated; CI green
- [ ] SBOM generated and image scans (Trivy) pass (if applicable)

## Ops & Observability
- [ ] Metrics and logs added for critical paths
- [ ] Alerts updated if needed (5xx, latency, queue depth)

## Docs
- [ ] Updated README/CONTRIBUTING if needed

## Screenshots/Notes
Add any relevant screenshots or notes.
