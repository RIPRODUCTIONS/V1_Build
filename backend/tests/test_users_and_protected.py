from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def register_and_login():
    email = "user@example.com"
    password = "secret123"
    r = client.post("/users/register", json={"email": email, "password": password})
    assert r.status_code in (201, 400)
    r2 = client.post("/users/login", json={"email": email, "password": password})
    assert r2.status_code == 200
    return r2.json()["access_token"]


def test_protected_lead_and_task_creation():
    token = register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/leads/", json={"name": "Acme Corp", "email": "a@b.com"}, headers=headers)
    assert r.status_code == 201
    lead_id = r.json()["id"]

    r2 = client.post("/tasks/", json={"title": "Follow up", "lead_id": lead_id}, headers=headers)
    assert r2.status_code == 201

    r3 = client.get("/users/me", headers=headers)
    assert r3.status_code == 200


def test_protected_requires_auth():
    r = client.post("/leads/", json={"name": "NoAuth"})
    assert r.status_code == 401
    r2 = client.post("/tasks/", json={"title": "NoAuth"})
    assert r2.status_code == 401
