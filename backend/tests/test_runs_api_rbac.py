from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import jwt
from starlette.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def _mk(sub: str, scopes: list[str] | None) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        'sub': sub,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=5)).timestamp()),
    }
    if scopes is not None:
        payload['scopes'] = scopes
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


client = TestClient(app)


def test_runs_read_rbac_disabled_allows():
    os.environ['SECURE_MODE'] = '0'
    r = client.get('/runs?limit=1&offset=0&sort=created_desc')
    assert r.status_code == 200


def test_runs_read_rbac_enabled_requires_scope():
    os.environ['SECURE_MODE'] = '1'
    r = client.get('/runs?limit=1&offset=0&sort=created_desc')
    assert r.status_code == 401


def test_runs_read_rbac_enabled_with_scope_allows():
    os.environ['SECURE_MODE'] = '1'
    tok = _mk('user-1', ['life.read'])  # minimal scope to read
    r = client.get(
        '/runs?limit=1&offset=0&sort=created_desc', headers={'Authorization': f'Bearer {tok}'}
    )
    assert r.status_code == 200
