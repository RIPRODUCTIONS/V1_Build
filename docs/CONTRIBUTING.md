### Contributing

Workflow
- Branch from `recovery/kisor-crash-2025-08-10` until merge.
- Keep changes additive; no deletions.
- Run: backend tests (pytest), web typecheck, smoke script.
- PR template checklist: auth set, metrics visible, docs updated.

Migrations
- Use Alembic for production.
- In dev/CI sqlite, rely on additive migration shim for nullable columns only.

CI
- Backend tests, Playwright e2e (life button), Schemathesis (public endpoints), k6 smoke (optional).
