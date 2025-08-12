### Next 5 Steps

1. Open PR from `recovery/kisor-crash-2025-08-10` to `master`; merge on green CI.
2. Set `JWT_SECRET` and (optional) `REDIS_URL`; validate `./scripts/smoke_life.sh` and `/runs` API.
3. Implement Redis Streams consumer for manager orchestrator prototype.
4. Persist run status transitions; expose filters on `/runs`.
5. Add Playwright e2e for `/runs` list rendering in dashboard.
