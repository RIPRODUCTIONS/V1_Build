"""
Integration tests for complete investigation workflows.
"""

import pytest
from fastapi.testclient import TestClient
from app.security.jwt_hs256 import HS256JWT
from app.main import app


class TestInvestigationWorkflow:
    """Test complete investigation workflows end-to-end."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def jwt_headers(self):
        """Generate JWT headers for authenticated requests."""
        jwt_handler = HS256JWT(secret="change-me")
        jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
        return {"Authorization": f"Bearer {jwt_token}"}
    
    def test_complete_osint_investigation_workflow(self, client, jwt_headers):
        """Test complete OSINT investigation workflow."""
        # 1. Check system health
        health_response = client.get("/investigations/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert "OSINT gathering and analysis" in health_data["capabilities"]
        
        # 2. Check system status
        status_response = client.get("/investigations/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "operational"
        assert "osint" in status_data["tools"]
        
        # 3. Start OSINT investigation with correct field structure
        osint_request = {
            "subject": {
                "domain": "example.com",
                "name": "Example Domain"
            },
            "scope": ["basic", "social", "technical"],
            "priority": "high",
            "max_depth": 3,
            "timeout_seconds": 300
        }
        
        osint_response = client.post(
            "/investigations/osint/run",
            json=osint_request,
            headers=jwt_headers
        )
        assert osint_response.status_code == 200
        osint_data = osint_response.json()
        assert osint_data["status"] == "success"
        assert "investigation_id" in osint_data
        assert osint_data["message"] == "OSINT investigation completed successfully"
        
        print(f"✅ OSINT investigation workflow completed successfully")
        print(f"   Investigation ID: {osint_data.get('investigation_id', 'N/A')}")
