## Summary

This PR merges recovery branch changes and adds:
- HS256 auth gating for /life/*, OpenAPI bearerAuth, metrics & dashboards, platform infra.

## Checklist
- [ ] JWT_SECRET configured in envs
- [ ] /life/* with token returns 200/202, metrics visible in Grafana
- [ ] Platform `make -C platform up` works
- [ ] New tests pass (backend + e2e)

## Screenshots/Notes
Add any relevant screenshots or notes.
