from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def token():
    email = "list@example.com"
    password = "secret123"
    client.post("/users/register", json={"email": email, "password": password})
    r = client.post("/users/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_list_leads_and_tasks():
    t = token()
    headers = {"Authorization": f"Bearer {t}"}

    # create some
    client.post("/leads/", json={"name": "Acme"}, headers=headers)
    client.post("/tasks/", json={"title": "Call"}, headers=headers)

    r1 = client.get("/leads/", headers=headers)
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    r2 = client.get("/tasks/", headers=headers)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
