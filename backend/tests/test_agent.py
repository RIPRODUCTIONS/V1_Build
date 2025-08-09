from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def login_token():
    email = "agent@example.com"
    password = "secret123"
    client.post("/users/register", json={"email": email, "password": password})
    r = client.post("/users/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_run_agent_and_fetch_artifacts():
    token = login_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/agent/run", json={"lead_id": None, "context": "Follow up about demo"}, headers=headers
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    r2 = client.get(f"/agent/artifacts/{run_id}", headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    kinds = {a["kind"] for a in data}
    assert {"summary", "next_action", "email_draft"}.issubset(kinds)
