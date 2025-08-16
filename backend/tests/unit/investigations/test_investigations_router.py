from fastapi.testclient import TestClient
from app.security.jwt_hs256 import HS256JWT

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _get_jwt_headers():
    """Generate JWT headers for testing."""
    jwt_handler = HS256JWT(secret="change-me")
    jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
    return {"Authorization": f"Bearer {jwt_token}"}


def test_investigations_health_endpoint():
    """Test the health endpoint that exists in our new API."""
    c = _client()
    r = c.get("/investigations/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "endpoints" in data


def test_investigations_capabilities_endpoint():
    """Test the capabilities endpoint that exists in our new API."""
    c = _client()
    r = c.get("/investigations/capabilities")
    assert r.status_code == 200
    data = r.json()
    assert "capabilities" in data
    assert "osint" in data["capabilities"]
    assert "malware" in data["capabilities"]
    assert "forensics" in data["capabilities"]


def test_investigations_status_endpoint():
    """Test the status endpoint that exists in our new API."""
    c = _client()
    r = c.get("/investigations/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "operational"
    assert "tools" in data

