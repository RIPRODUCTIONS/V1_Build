import re

from starlette.testclient import TestClient

from app.main import app


def test_life_metrics_labeled():
    c = TestClient(app)
    # obtain token
    email = 'metrics_tests@example.com'
    password = 'secret123'
    c.post('/users/register', json={'email': email, 'password': password})
    tok = c.post('/users/login', json={'email': email, 'password': password}).json()['access_token']
    r = c.post('/life/calendar/organize', json={}, headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code in (200, 202)
    m = c.get('/metrics')
    assert m.status_code == 200
    text = m.text
    assert 'life_requests_total' in text
    # Accept either exact code labels or class labels like 2xx
    assert re.search(r'life_request_latency_seconds_bucket\{.*status="2', text)
