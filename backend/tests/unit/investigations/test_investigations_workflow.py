from __future__ import annotations

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


def test_osint_investigation_workflow():
    """Test the complete OSINT investigation workflow with our new API."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    # Start OSINT investigation
    payload = {"subject": {"name": "John Example"}}
    r = c.post("/investigations/osint/run", json=payload, headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert "investigation_id" in body
    assert "data" in body

    investigation_id = body["investigation_id"]

    # Check investigation status
    r = c.get(f"/investigations/osint/status/{investigation_id}", headers=jwt_headers)
    assert r.status_code == 200
    status_body = r.json()
    assert "status" in status_body


def test_malware_investigation_workflow():
    """Test the complete malware investigation workflow with our new API."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    # Start malware investigation
    payload = {"sample": "test.exe"}
    r = c.post("/investigations/malware/dynamic/run", json=payload, headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert "investigation_id" in body
    assert "data" in body

    investigation_id = body["investigation_id"]

    # Check investigation status
    r = c.get(f"/investigations/malware/status/{investigation_id}", headers=jwt_headers)
    assert r.status_code == 200
    status_body = r.json()
    assert "status" in status_body


def test_forensics_investigation_workflow():
    """Test the complete forensics investigation workflow with our new API."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    # Start forensics investigation
    payload = {"source": "evidence.dd"}
    r = c.post("/investigations/forensics/timeline/run", json=payload, headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert "investigation_id" in body
    assert "data" in body

    investigation_id = body["investigation_id"]

    # Check investigation status
    r = c.get(f"/investigations/forensics/timeline/status/{investigation_id}", headers=jwt_headers)
    assert r.status_code == 200
    status_body = r.json()
    assert "status" in status_body


def test_evidence_chain_of_custody():
    """Test the evidence chain of custody endpoint."""
    c = _client()
    jwt_headers = _get_jwt_headers()

    r = c.get("/investigations/evidence/chain-of-custody", headers=jwt_headers)
    assert r.status_code == 200
    body = r.json()
    assert "entries" in body
    assert "total" in body


