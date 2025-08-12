from uuid import uuid4

from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def headers():
    email = 'filters@example.com'
    password = 'secret123'
    client.post('/users/register', json={'email': email, 'password': password})
    r = client.post('/users/login', json={'email': email, 'password': password})
    token = r.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_leads_filter_sort():
    h = headers()
    token = uuid4().hex[:8]
    client.post('/leads/', json={'name': f'Zeta{token}', 'email': 'z@a.com'}, headers=h)
    client.post('/leads/', json={'name': f'Alpha{token}', 'email': 'a@a.com'}, headers=h)
    r = client.get(f'/leads/?q={token}&sort=name', headers=h)
    assert r.status_code == 200
    data = r.json()
    assert [d['name'] for d in data] == [f'Alpha{token}', f'Zeta{token}']


def test_tasks_filter_sort():
    h = headers()
    token = uuid4().hex[:8]
    t1 = client.post('/tasks/', json={'title': f'Call{token}', 'lead_id': None}, headers=h).json()[
        'id'
    ]
    t2 = client.post('/tasks/', json={'title': f'Email{token}', 'lead_id': None}, headers=h).json()[
        'id'
    ]
    # Mark these tasks with a unique status to filter only them
    client.put(f'/tasks/{t1}', json={'status': f'tmp{token}'}, headers=h)
    client.put(f'/tasks/{t2}', json={'status': f'tmp{token}'}, headers=h)
    r = client.get(f'/tasks/?status_filter=tmp{token}&sort=title', headers=h)
    assert r.status_code == 200
    data = r.json()
    assert [d['title'] for d in data] == [f'Call{token}', f'Email{token}']
