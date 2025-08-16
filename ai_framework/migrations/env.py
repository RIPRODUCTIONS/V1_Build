from __future__ import annotations

import os
from contextlib import suppress

from alembic import context
from sqlalchemy import engine_from_config, pool

from core.db import DB_URL, Base

# ensure extra models are imported so Alembic sees them in metadata
with suppress(Exception):
    from ai_framework import models_extra  # noqa: F401
with suppress(Exception):
    import models_extra  # type: ignore  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Skip logging configuration to avoid linter/type issues


target_metadata = Base.metadata


def get_url() -> str:
    env_url = os.getenv("DB_URL")
    return env_url or DB_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


