# Builder

A clean, well-structured foundation for AI project scaffolding. Centralized env, consistent tooling, and clear entry points.

## Quick start

```bash
# create and activate venv, install safe deps
make venv
make safe-install

# run health check
make health
```

## Layout

- `src/builder`: Typed Python package for scaffolding and orchestration
- `scripts/`: Operational scripts and automation entrypoints
- `toolkits/`: Symlinked, space-free pointers to external tool/resource dirs
- `.venv/`: Project virtual environment

## Environment

Paths are defined in `.env` and also exposed via `toolkits/` symlinks. Update `.env` if locations change.

### Backend `.env` keys

- `DATABASE_URL` (default sqlite:///./dev.db)
- `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- `SENTRY_DSN` (optional)
- `ALLOWED_ORIGINS` (comma separated, e.g. http://localhost:3000)
- `CI_ENV` (true/false), `CI_CLEANUP_TOKEN` (secret for cleanup)

### Web `.env` keys

- `NEXT_PUBLIC_API_BASE` (e.g. http://127.0.0.1:8000)
- `NEXT_PUBLIC_WEB_ORIGIN` (e.g. http://localhost:3000)

## Testing with cleanup

Run API and web locally, then run Playwright. To enable auto-clean after tests:

1. Set API envs while running the API:
   - `CI_ENV=true`
   - `CI_CLEANUP_TOKEN=<secret>`
2. Set Playwright envs:
   - `API_BASE_URL=http://127.0.0.1:8000`
   - `CI_ENV=true`
   - `CI_CLEANUP_TOKEN=<secret>`
3. Execute tests from `apps/web`:
   - `npm run test`

The teardown calls `DELETE /admin/cleanup/all` with `X-CI-Token` to clear test data.

### Notes

- Cleanup endpoints are rate limited: 5 requests/min/IP. The 6th within a minute returns `429 {"detail":"Rate limit exceeded"}`.
- `ALLOWED_ORIGINS` should be a comma-separated list of valid http/https origins (scheme + host). Invalid entries are ignored. If unset, defaults to `http://localhost:3000`.
- Example local `.env` values:
  - API: `DATABASE_URL=sqlite:///./dev.db`, `ALLOWED_ORIGINS=http://localhost:3000`, `CI_ENV=true`, `CI_CLEANUP_TOKEN=local-secret`
  - Web: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`


## Coding standards

- Black, Ruff, Mypy configured via `pyproject.toml`
- Keep functions short, explicit names, early returns, handle edge cases first
- Add concise docstrings for non-trivial functions
