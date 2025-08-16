import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)


@pytest.fixture(scope="session", autouse=True)
def _configure_env() -> None:
    os.environ.setdefault("SECURE_MODE", "false")
    os.environ.setdefault("INTERNAL_API_KEY", "test-api-key")
    # Force default admin creds in tests to keep fixtures stable regardless of .env
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD"] = "admin"


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app
    return TestClient(app)


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": os.getenv("INTERNAL_API_KEY", "test-api-key")}


@pytest.fixture(autouse=True, scope="session")
def _suppress_asyncio_redis_warning():
    """Suppress noisy 'Event loop is closed' warnings from redis asyncio destructor in tests."""
    import warnings
    warnings.filterwarnings(
        "ignore",
        message="Exception ignored in: <function AbstractConnection.__del__",
        category=pytest.PytestUnraisableExceptionWarning,
    )

import os
import sys

# Ensure the backend package root and repo root are on sys.path so imports work
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, ".."))
for p in (BACKEND_ROOT, REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

# Ensure API runs agent synchronously during tests to avoid Redis requirement
os.environ.setdefault("CI_ENV", "true")
