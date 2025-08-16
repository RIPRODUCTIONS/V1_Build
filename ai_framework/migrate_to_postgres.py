from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config


def migrate(url: str) -> None:
    migrations_dir = Path(__file__).parent / "migrations"
    versions_dir = migrations_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)

    cfg = Config(str(migrations_dir / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)

    # Autogenerate a revision if versions are empty
    if not any(versions_dir.iterdir()):
        command.revision(cfg, autogenerate=True, message="initial extra tables")

    command.upgrade(cfg, "head")


if __name__ == "__main__":
    db_url = os.getenv("DB_URL", "sqlite:///./ai_framework.db")
    migrate(db_url)
    print(f"Upgraded schema on {db_url}")


