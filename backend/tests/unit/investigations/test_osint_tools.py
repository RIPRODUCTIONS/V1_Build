import pytest
from app.security.jwt_hs256 import HS256JWT


class TestOSINTDossier:
    def test_osint_dossier_basic(self, client):
        # Create a test JWT token
        jwt_handler = HS256JWT(secret="change-me")
        jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
        jwt_headers = {"Authorization": f"Bearer {jwt_token}"}

        res = client.post(
            "/investigations/osint/run",
            headers=jwt_headers,
            json={"subject": {"name": "Jane Doe"}},
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert "investigation_id" in data
        assert data.get("message") == "OSINT investigation completed successfully"


class TestMalwareAnalysis:
    def test_malware_dynamic_skeleton(self, client):
        # Create a test JWT token
        jwt_handler = HS256JWT(secret="change-me")
        jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
        jwt_headers = {"Authorization": f"Bearer {jwt_token}"}

        res = client.post(
            "/investigations/malware/dynamic/run",
            headers=jwt_headers,
            json={"sample": "test.exe"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert "investigation_id" in data
        assert data.get("message") == "Malware analysis completed successfully"


class TestForensicsTimeline:
    def test_forensics_timeline_skeleton(self, client):
        # Create a test JWT token
        jwt_handler = HS256JWT(secret="change-me")
        jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
        jwt_headers = {"Authorization": f"Bearer {jwt_token}"}

        res = client.post(
            "/investigations/forensics/timeline/run",
            headers=jwt_headers,
            json={"source": "image.dd"},
        )
        print(f"Response status: {res.status_code}")
        print(f"Response body: {res.text}")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert "investigation_id" in data
        assert data.get("message") == "Timeline analysis completed successfully"



