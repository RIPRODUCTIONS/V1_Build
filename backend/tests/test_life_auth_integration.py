from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from app.core.config import get_settings
from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def _mk(payload: dict) -> str:
    settings = get_settings()
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _auth(h: str | None):
    return {"Authorization": f"Bearer {h}"} if h else {}


def test_public_health_and_metrics_ok():
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_protected_requires_auth():
    r = client.post("/life/finance/investments")
    assert r.status_code in (401, 403)


def test_protected_with_valid_token():
    now = datetime.now(UTC)
    tok = _mk(
        {
            "sub": "user-42",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "scopes": ["life.finance"],
        }
    )
    r = client.post("/life/finance/bills", headers=_auth(tok), json={})
    assert r.status_code in (200, 202)


def test_invalid_signature_is_401_invalid_token():
    settings = get_settings()
    now = datetime.now(UTC)
    tok = jwt.encode(
        {"sub": "user-42", "exp": int((now + timedelta(minutes=1)).timestamp())},
        settings.jwt_secret + "-wrong",
        algorithm=settings.jwt_algorithm,
    )
    r = client.post("/life/security/sweep", headers=_auth(tok), json={})
    assert r.status_code == 401


def test_expired_is_401():
    now = datetime.now(UTC)
    tok = _mk({"sub": "user-42", "exp": int((now - timedelta(seconds=1)).timestamp())})
    r = client.post("/life/travel/plan", headers=_auth(tok), json={})
    assert r.status_code == 401


def test_not_active_is_401():
    now = datetime.now(UTC)
    tok = _mk(
        {
            "sub": "user-42",
            "nbf": int((now + timedelta(seconds=30)).timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        }
    )
    r = client.post("/life/calendar/organize", headers=_auth(tok), json={})
    assert r.status_code == 401


def test_missing_sub_is_403():
    now = datetime.now(UTC)
    tok = _mk({"exp": int((now + timedelta(minutes=5)).timestamp())})
    r = client.post("/life/shopping/optimize", headers=_auth(tok), json={})
    assert r.status_code == 403
