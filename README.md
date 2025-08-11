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
- `REDIS_URL` (e.g., redis://127.0.0.1:6379/0)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (e.g., redis://127.0.0.1:6379/1 and /2)
- `OTEL_EXPORTER_OTLP_ENDPOINT` (optional)
- `ALLOWED_ORIGINS` (comma separated, e.g. http://localhost:3000)
- `CI_ENV` (true/false), `CI_CLEANUP_TOKEN` (secret for cleanup)

### Web `.env` keys

- `NEXT_PUBLIC_API_BASE_URL` (e.g. http://127.0.0.1:8000)
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

- Cleanup endpoints are rate-limited: 5 requests/min/IP. The 6th within a minute returns `429 {"detail":"Rate limit exceeded"}`.
- `ALLOWED_ORIGINS` should be a comma-separated list of valid http/https origins (scheme + host). Invalid entries are ignored. If unset, defaults to `http://localhost:3000`.
- Example local `.env` values:
  - API: `DATABASE_URL=sqlite:///./dev.db`, `ALLOWED_ORIGINS=http://localhost:3000`, `CI_ENV=true`, `CI_CLEANUP_TOKEN=local-secret`
  - Web: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`


## API Overview

### Skills → DAG → Endpoint Map

| Endpoint | Method | Purpose | Auth | Status Codes | Request Example | Response Example |
|---|---|---|---|---|---|---|
| /life/finance/investments | POST | Investment analysis / rebalance | none | 200/202, 400/422 | See OpenAPI examples (happy_path, validation_error) | EnqueuedResponse |
| /life/finance/bills | POST | Detect and schedule bills | none | 200/202, 400/422 | OpenAPI | EnqueuedResponse |
| /life/security/sweep | POST | Weekly security sweep | none | 200/202, 400/422 | OpenAPI | EnqueuedResponse |
| /life/travel/plan | POST | Build travel plan | none | 200/202, 400/422 | OpenAPI | EnqueuedResponse |
| /life/calendar/organize | POST | Organize daily schedule | none | 200/202 | OpenAPI | EnqueuedResponse |
| /life/shopping/optimize | POST | Optimize shopping | none | 200/202 | OpenAPI | EnqueuedResponse |

Notes:
- Correlation: header `X-Correlation-Id` is accepted and echoed on responses.
- Metrics: Prometheus counters/histograms at `/metrics` with labels `{route, dag_id, skill, status}`.
- Auth is currently none for these routes (will change in a follow-up PR).


## Coding standards

- Black, Ruff, Mypy configured via `pyproject.toml`
- Keep functions short, explicit names, early returns, handle edge cases first
- Add concise docstrings for non-trivial functions
