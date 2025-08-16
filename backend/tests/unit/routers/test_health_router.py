import pytest


@pytest.mark.unit
def test_health_live(client):
    r = client.get('/health/live')
    assert r.status_code == 200
    data = r.json()
    assert data.get('status') in {'ok', 'alive'}


@pytest.mark.unit
def test_health_ready(client):
    r = client.get('/health/ready')
    assert r.status_code == 200
    data = r.json()
    assert 'db' in data and 'redis' in data and 'status' in data
    assert data['db'] in {'ok', 'fail'}
    assert data['redis'] in {'ok', 'fail'}
    assert data['status'] in {'ready', 'not_ready'}


