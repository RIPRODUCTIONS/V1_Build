from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def test_login_and_me():
    # default creds from settings
    res = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    res2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert res2.json()["username"] == "admin"


def test_login_wrong_password():
    res = client.post(
        "/auth/token",
        data={"username": "admin", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 400
