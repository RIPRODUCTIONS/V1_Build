from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_departments_list():
    r = client.get('/departments/')
    assert r.status_code == 200
    items = r.json().get('items')
    assert isinstance(items, list) and 'life' in items and 'finance' in items


def test_tasks_catalog():
    r = client.get('/departments/tasks/catalog')
    assert r.status_code == 200
    data = r.json()
    assert 'departments' in data
