import json
import os
import sys

import pytest

# Environment defaults for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///./local.sqlite")
os.environ.setdefault("SECURE_MODE", "0")
os.environ.setdefault('CI_ENV', 'true')

# Ensure the backend package root and repo root are on sys.path so imports work
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, '..'))
for p in (BACKEND_ROOT, REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    Base.metadata.create_all(bind=engine)
    # minimal seed
    try:
        from app.models import User
        from app.routers.users import hash_password

        with SessionLocal() as db:
            if not db.query(User).first():
                db.add(User(email="test@example.com", password_hash=hash_password("secret123")))
                db.commit()
    except Exception:
        pass
    yield


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _ensure_catalog_file():
    try:
        from app.routers.departments import CATALOG_PATH  # type: ignore
        path = CATALOG_PATH
    except Exception:
        path = os.path.join("platform", "shared", "catalog", "tasks.json")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(
                {
                    "departments": ["life", "finance", "ops"],
                    "tasks": [
                        {
                            "id": "echo",
                            "title": "Echo Task",
                            "department": "ops",
                            "summary": "No-op test task",
                        }
                    ],
                },
                f,
            )


@pytest.fixture(scope="session", autouse=True)
def _relax_security_for_tests(app):
    """Override auth dependency so tests can call protected routes without JWT."""
    try:
        from app.dependencies.auth import get_current_user  # type: ignore
        from app.models import User
    except Exception:
        yield
        return

    def _fake_user():
        with SessionLocal() as db:
            u = db.query(User).first()
            if u:
                return u
        # Fallback stub
        class _U:
            id = 1
            email = "test@example.com"
            is_active = True

        return _U()

    app.dependency_overrides[get_current_user] = _fake_user
    yield
    app.dependency_overrides.pop(get_current_user, None)
