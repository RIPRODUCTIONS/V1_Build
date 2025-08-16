# Alembic Migrations

- Configure DB via `DB_URL` env; defaults to SQLite path from `core.db`.
- Generate migration:
  `alembic -c ai_framework/migrations/alembic.ini revision --autogenerate -m "change"`
- Upgrade to head:
  `alembic -c ai_framework/migrations/alembic.ini upgrade head`


