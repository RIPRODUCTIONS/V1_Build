# ruff: noqa: I001
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.skip(reason='Run manually when local LLM is running')
def test_llm_ping_manual():
    r = client.get('/llm/ping')
    assert r.status_code == 200
    assert 'reply' in r.json()
