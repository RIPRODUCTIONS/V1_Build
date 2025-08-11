from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def _post(path: str):
    r = client.post(path, json={})
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
