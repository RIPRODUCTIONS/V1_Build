from __future__ import annotations

from typing import Any, Dict

import pytest
from starlette.testclient import TestClient
from app.security.jwt_hs256 import HS256JWT

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _get_jwt_headers():
    """Generate JWT headers for testing."""
    jwt_handler = HS256JWT(secret="change-me")
    jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
    return {"Authorization": f"Bearer {jwt_token}"}


def test_investigation_status_endpoints():
    """Test the investigation status endpoints that exist in our new API."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    # Test OSINT status endpoint
    r = c.get("/investigations/osint/status/test-id", headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert "investigation_id" in body
    assert "status" in body

    # Test malware status endpoint
    r = c.get("/investigations/malware/status/test-id", headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert "analysis_id" in body
    assert "status" in body

    # Test forensics status endpoint
    r = c.get("/investigations/forensics/timeline/status/test-id", headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert "analysis_id" in body
    assert "status" in body


def test_evidence_endpoints():
    """Test the evidence endpoints that exist in our new API."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    # Test chain of custody endpoint
    r = c.get("/investigations/evidence/chain-of-custody", headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert "entries" in body
    assert "total" in body

    # Test evidence details endpoint
    r = c.get("/investigations/evidence/test-evidence-id", headers=jwt_headers)
    # This should return 404 for non-existent evidence, which is expected
    assert r.status_code in [200, 404]


def test_investigation_workflow_integration():
    """Test the complete investigation workflow integration."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    # Start an OSINT investigation
    payload = {"subject": {"name": "Test Subject"}}
    r = c.post("/investigations/osint/run", json=payload, headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    investigation_id = body["investigation_id"]

    # Check the status
    r = c.get(f"/investigations/osint/status/{investigation_id}", headers=jwt_headers)
    assert r.status_code == 200
    status_body = r.json()
    assert "status" in status_body

    # Verify the investigation data is consistent
    assert status_body["investigation_id"] == investigation_id


