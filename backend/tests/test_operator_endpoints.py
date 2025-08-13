import os

import pytest
from starlette.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/operator/status",
        "/operator/web/tasks",
        "/operator/desktop/tasks",
        "/operator/ai/analyze_task",
        "/operator/ai/next_action",
        "/operator/execute",
    ],
)
def test_operator_endpoints_disabled_ok(path: str):
    r = client.get(path) if path.endswith("status") else client.post(path, json={})
    assert r.status_code in (200, 201, 202)
    js = r.json()
    assert isinstance(js, dict)


