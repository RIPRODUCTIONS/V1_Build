from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def _token() -> str:
    email = "life_tests@example.com"
    password = "secret123"
    client.post("/users/register", json={"email": email, "password": password})
    r = client.post("/users/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def _post(path: str):
    headers = {"Authorization": f"Bearer {_token()}"}
    r = client.post(path, json={}, headers=headers)
    assert r.status_code in (200, 202)
    data = r.json()
    assert "run_id" in data


def test_finance_and_security_endpoints():
    _post("/life/finance/investments")
    _post("/life/finance/bills")
    _post("/life/security/sweep")


def test_travel_calendar_shopping_endpoints():
    _post("/life/travel/plan")
    _post("/life/calendar/organize")
    _post("/life/shopping/optimize")
