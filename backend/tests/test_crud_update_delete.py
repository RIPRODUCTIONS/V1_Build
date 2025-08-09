from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def auth_headers():
    email = "crud@example.com"
    password = "secret123"
    client.post("/users/register", json={"email": email, "password": password})
    r = client.post("/users/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_lead_update_delete():
    headers = auth_headers()
    r = client.post("/leads/", json={"name": "Old", "email": "old@a.com"}, headers=headers)
    assert r.status_code == 201
    lead_id = r.json()["id"]

    r2 = client.put(f"/leads/{lead_id}", json={"name": "New"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["name"] == "New"

    r3 = client.delete(f"/leads/{lead_id}", headers=headers)
    assert r3.status_code == 204


def test_task_update_delete():
    headers = auth_headers()
    r = client.post("/tasks/", json={"title": "Old"}, headers=headers)
    assert r.status_code == 201
    task_id = r.json()["id"]

    r2 = client.put(f"/tasks/{task_id}", json={"title": "New", "status": "done"}, headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body["title"] == "New"
    assert body["status"] == "done"

    r3 = client.delete(f"/tasks/{task_id}", headers=headers)
    assert r3.status_code == 204
