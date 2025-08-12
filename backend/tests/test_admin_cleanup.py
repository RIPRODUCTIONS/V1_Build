from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cleanup_gated():
    # cleanup disabled by default
    res = client.delete('/admin/cleanup/leads')
    assert res.status_code in (401, 403)


def test_cleanup_with_token(monkeypatch):
    monkeypatch.setenv('CI_ENV', 'true')
    monkeypatch.setenv('CI_CLEANUP_TOKEN', 'secret-ci')
    # seed a lead
    client.post('/users/register', json={'email': 'ci@example.com', 'password': 'x'})
    login = client.post('/users/login', json={'email': 'ci@example.com', 'password': 'x'}).json()
    token = login['access_token']
    client.post('/leads/', json={'name': 'X'}, headers={'Authorization': f'Bearer {token}'})
    # call cleanup
    res = client.delete('/admin/cleanup/all', headers={'X-CI-Token': 'secret-ci'})
    assert res.status_code == 204


def test_cleanup_missing_token(monkeypatch):
    monkeypatch.setenv('CI_ENV', 'true')
    monkeypatch.setenv('CI_CLEANUP_TOKEN', 'secret-ci')
    res = client.delete('/admin/cleanup/all')
    assert res.status_code == 401


def test_cleanup_wrong_token(monkeypatch):
    monkeypatch.setenv('CI_ENV', 'true')
    monkeypatch.setenv('CI_CLEANUP_TOKEN', 'secret-ci')
    res = client.delete('/admin/cleanup/all', headers={'X-CI-Token': 'wrong'})
    assert res.status_code == 401


def test_cleanup_ci_disabled(monkeypatch):
    monkeypatch.setenv('CI_ENV', 'false')
    monkeypatch.setenv('CI_CLEANUP_TOKEN', 'secret-ci')
    res = client.delete('/admin/cleanup/all', headers={'X-CI-Token': 'secret-ci'})
    assert res.status_code == 403


def test_rate_limit(monkeypatch):
    monkeypatch.setenv('CI_ENV', 'true')
    monkeypatch.setenv('CI_CLEANUP_TOKEN', 'secret-ci')
    headers = {'X-CI-Token': 'secret-ci', 'X-Forwarded-For': '1.2.3.4'}
    # 5 allowed
    for _ in range(5):
        r = client.delete('/admin/cleanup/leads', headers=headers)
        assert r.status_code == 204
    # 6th should be limited
    r6 = client.delete('/admin/cleanup/leads', headers=headers)
    assert r6.status_code == 429
    assert r6.json().get('detail') == 'Rate limit exceeded'


def test_cors_origin():
    # With default config, localhost:3000 is allowed
    res_allowed = client.options(
        '/health',
        headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
        },
    )
    assert res_allowed.status_code in (200, 204)
    assert res_allowed.headers.get('access-control-allow-origin') == 'http://localhost:3000'

    res_blocked = client.options(
        '/health',
        headers={
            'Origin': 'http://blocked.test',
            'Access-Control-Request-Method': 'GET',
        },
    )
    assert res_blocked.status_code in (200, 204, 400)
    assert res_blocked.headers.get('access-control-allow-origin') is None


def test_logging_contains_route_and_status(monkeypatch, caplog):
    monkeypatch.setenv('CI_ENV', 'false')
    monkeypatch.setenv('CI_CLEANUP_TOKEN', 'secret-ci')
    with caplog.at_level('INFO'):
        client.delete(
            '/admin/cleanup/all', headers={'X-CI-Token': 'secret-ci', 'X-Forwarded-For': '9.9.9.9'}
        )
    # Find our cleanup log record
    record = next((r for r in caplog.records if r.msg == 'cleanup_request'), None)
    assert record is not None
    # Route and auth result are embedded as attributes on the record
    assert getattr(record, 'route', None) == '/admin/cleanup/all'
    assert getattr(record, 'auth', None) in (
        'ci_env_false',
        'invalid_token',
        'success',
        'rate_limited',
    )
