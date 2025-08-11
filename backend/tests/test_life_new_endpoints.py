from app.core.config import get_settings
from app.main import app
from app.security.jwt_hs256 import HS256JWT
from starlette.testclient import TestClient

client = TestClient(app)


def _token() -> str:
    email = "life_tests@example.com"
    password = "secret123"
    client.post("/users/register", json={"email": email, "password": password})
    client.post("/users/login", json={"email": email, "password": password})
    # The default login token lacks scopes; produce a scoped token using HS256 helper.
    settings = get_settings()
    scoped = HS256JWT(secret=settings.jwt_secret).mint(
        subject=email, scopes=["life.finance"], ttl_override_seconds=300
    )
    return scoped


def _post(path: str):
    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
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
