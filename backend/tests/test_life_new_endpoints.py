from app.main import app
from app.security.jwt_hs256 import HS256JWT
from starlette.testclient import TestClient

client = TestClient(app)

# Create a test JWT token
def _get_test_jwt():
    jwt_handler = HS256JWT(secret="change-me")
    return jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)

def _post(path: str):
    headers = {"Authorization": f"Bearer {_get_test_jwt()}"}
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
