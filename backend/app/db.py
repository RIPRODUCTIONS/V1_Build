from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import suppress

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./dev.db')

connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_dev_sqlite() -> None:
    """Additive, best-effort migration for sqlite in dev/CI.

    Creates missing columns on known tables to keep tests green when models evolve.
    """
    if not DATABASE_URL.startswith('sqlite'):  # only for sqlite
        return
    with engine.begin() as conn:
        with suppress(Exception):
            conn.execute(text('ALTER TABLE agent_runs ADD COLUMN intent VARCHAR(128)'))
        with suppress(Exception):
            conn.execute(text('ALTER TABLE agent_runs ADD COLUMN department VARCHAR(64)'))
        with suppress(Exception):
            conn.execute(text('ALTER TABLE agent_runs ADD COLUMN correlation_id VARCHAR(64)'))
