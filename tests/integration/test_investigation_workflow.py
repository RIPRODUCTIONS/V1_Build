"""
Integration tests for complete investigation workflows.

This test suite validates end-to-end investigation processes including:
- OSINT investigation workflow
- Malware analysis workflow
- Forensics timeline analysis workflow
- Cross-component data flow
- Authentication and authorization
- Error handling and recovery
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

        # 3. Start OSINT investigation
        osint_request = {
            "subject": {"target": "example.com", "type": "domain"},
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

        # 4. Check OSINT investigation status
        investigation_id = osint_data["investigation_id"]
        status_response = client.get(
            f"/investigations/osint/status/{investigation_id}",
            headers=jwt_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["investigation_id"] == investigation_id
        assert status_data["status"] == "completed"

        # 5. Verify investigation data
        assert "data" in osint_data
        investigation_data = osint_data["data"]
        assert "subject" in investigation_data
        assert "findings" in investigation_data
        assert "risk_score" in investigation_data

        print(f"✅ OSINT investigation workflow completed successfully")
        print(f"   Investigation ID: {investigation_id}")
        print(f"   Risk Score: {investigation_data.get('risk_score', 'N/A')}")

    def test_complete_malware_analysis_workflow(self, client, jwt_headers):
        """Test complete malware analysis workflow."""
        # 1. Start malware analysis
        malware_request = {
            "sample": "test_malware.exe",
            "analysis_type": ["dynamic", "static", "behavioral"],
            "timeout_seconds": 600,
            "sandbox_config": {"os": "windows", "timeout": 300},
            "priority": "high"
        }

        malware_response = client.post(
            "/investigations/malware/dynamic/run",
            json=malware_request,
            headers=jwt_headers
        )
        assert malware_response.status_code == 200
        malware_data = malware_response.json()
        assert malware_data["status"] == "success"
        assert "investigation_id" in malware_data
        assert malware_data["message"] == "Malware analysis completed successfully"

        # 2. Check malware analysis status
        analysis_id = malware_data["investigation_id"]
        status_response = client.get(
            f"/investigations/malware/status/{analysis_id}",
            headers=jwt_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["analysis_id"] == analysis_id
        assert status_data["status"] == "completed"

        # 3. Verify analysis data
        assert "data" in malware_data
        analysis_data = malware_data["data"]
        assert "sample" in analysis_data
        assert "threat_score" in analysis_data
        assert "behavior_analysis" in analysis_data

        print(f"✅ Malware analysis workflow completed successfully")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Threat Score: {analysis_data.get('threat_score', 'N/A')}")

    def test_complete_forensics_timeline_workflow(self, client, jwt_headers):
        """Test complete forensics timeline analysis workflow."""
        # 1. Start forensics timeline analysis
        timeline_request = {
            "source": "evidence_image.dd",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z",
            "event_types": ["file_access", "network", "process"],
            "correlation_rules": {"suspicious_ips": ["192.168.1.100"]},
            "max_events": 5000
        }

        timeline_response = client.post(
            "/investigations/forensics/timeline/run",
            json=timeline_request,
            headers=jwt_headers
        )
        assert timeline_response.status_code == 200
        timeline_data = timeline_response.json()
        assert timeline_data["status"] == "success"
        assert "investigation_id" in timeline_data
        assert timeline_data["message"] == "Timeline analysis completed successfully"

        # 2. Check timeline analysis status
        analysis_id = timeline_data["investigation_id"]
        status_response = client.get(
            f"/investigations/forensics/timeline/status/{analysis_id}",
            headers=jwt_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["analysis_id"] == analysis_id
        assert status_data["status"] == "completed"

        # 3. Verify timeline data
        assert "data" in timeline_data
        timeline_analysis_data = timeline_data["data"]
        assert "source" in timeline_analysis_data
        assert "events" in timeline_analysis_data
        assert "summary" in timeline_analysis_data
        assert "integrity_hash" in timeline_analysis_data

        print(f"✅ Forensics timeline workflow completed successfully")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Events Count: {len(timeline_analysis_data.get('events', []))}")

    def test_cross_component_data_flow(self, client, jwt_headers):
        """Test data flow between different investigation components."""
        # 1. Start OSINT investigation
        osint_request = {
            "subject": {"target": "malicious-domain.com", "type": "domain"},
            "scope": ["basic", "threat_intel"],
            "priority": "high"
        }

        osint_response = client.post(
            "/investigations/osint/run",
            json=osint_request,
            headers=jwt_headers
        )
        assert osint_response.status_code == 200
        osint_data = osint_response.json()
        osint_id = osint_data["investigation_id"]

        # 2. Use OSINT findings to inform malware analysis
        osint_findings = osint_data["data"]["findings"]
        malware_request = {
            "sample": "suspicious_file.exe",
            "analysis_type": ["dynamic"],
            "sandbox_config": {
                "network_access": True,
                "suspicious_domains": [f["domain"] for f in osint_findings if "domain" in f]
            }
        }

        malware_response = client.post(
            "/investigations/malware/dynamic/run",
            json=malware_request,
            headers=jwt_headers
        )
        assert malware_response.status_code == 200
        malware_data = malware_response.json()
        malware_id = malware_data["investigation_id"]

        # 3. Use both findings for timeline analysis
        timeline_request = {
            "source": "compromised_system.dd",
            "correlation_rules": {
                "suspicious_domains": [f["domain"] for f in osint_findings if "domain" in f],
                "malware_indicators": malware_data["data"].get("indicators", [])
            }
        }

        timeline_response = client.post(
            "/investigations/forensics/timeline/run",
            json=timeline_request,
            headers=jwt_headers
        )
        assert timeline_response.status_code == 200

        print(f"✅ Cross-component data flow test completed successfully")
        print(f"   OSINT ID: {osint_id}")
        print(f"   Malware ID: {malware_id}")
        print(f"   Timeline ID: {timeline_response.json()['investigation_id']}")

    def test_authentication_and_authorization(self, client):
        """Test authentication and authorization across endpoints."""
        # 1. Test unauthenticated access
        health_response = client.get("/investigations/health")
        assert health_response.status_code == 200  # Health endpoint is public

        # 2. Test authenticated endpoints without token
        osint_response = client.post("/investigations/osint/run", json={"subject": {"target": "test.com"}})
        assert osint_response.status_code == 401  # Should require authentication

        # 3. Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        osint_response = client.post(
            "/investigations/osint/run",
            json={"subject": {"target": "test.com"}},
            headers=invalid_headers
        )
        assert osint_response.status_code == 401  # Should reject invalid token

        # 4. Test with valid token
        jwt_handler = HS256JWT(secret="change-me")
        valid_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
        valid_headers = {"Authorization": f"Bearer {valid_token}"}

        osint_response = client.post(
            "/investigations/osint/run",
            json={"subject": {"target": "test.com"}},
            headers=valid_headers
        )
        assert osint_response.status_code == 200  # Should work with valid token

        print(f"✅ Authentication and authorization tests completed successfully")

    def test_error_handling_and_recovery(self, client, jwt_headers):
        """Test error handling and recovery mechanisms."""
        # 1. Test invalid request data
        invalid_request = {
            "invalid_field": "invalid_value"
        }

        osint_response = client.post(
            "/investigations/osint/run",
            json=invalid_request,
            headers=jwt_headers
        )
        assert osint_response.status_code == 400  # Should return validation error

        # 2. Test missing required fields
        incomplete_request = {
            "subject": {}  # Missing required subject data
        }

        osint_response = client.post(
            "/investigations/osint/run",
            json=incomplete_request,
            headers=jwt_headers
        )
        assert osint_response.status_code == 400  # Should return validation error

        # 3. Test that system remains stable after errors
        # Make a valid request to ensure system still works
        valid_request = {
            "subject": {"target": "error-recovery.com", "type": "domain"},
            "scope": ["basic"]
        }

        recovery_response = client.post(
            "/investigations/osint/run",
            json=valid_request,
            headers=jwt_headers
        )
        assert recovery_response.status_code == 200  # System should recover

        print(f"✅ Error handling and recovery tests completed successfully")

    def test_system_performance_and_stability(self, client, jwt_headers):
        """Test system performance and stability under load."""
        # 1. Test concurrent requests
        import concurrent.futures
        import time

        def make_request():
            request_data = {
                "subject": {"target": f"test-{time.time()}.com", "type": "domain"},
                "scope": ["basic"]
            }
            response = client.post(
                "/investigations/osint/run",
                json=request_data,
                headers=jwt_headers
            )
            return response.status_code

        # Make 5 concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]

        end_time = time.time()
        execution_time = end_time - start_time

        # All requests should succeed
        assert all(status == 200 for status in results)

        # Performance should be reasonable (under 10 seconds for 5 requests)
        assert execution_time < 10.0

        print(f"✅ System performance and stability tests completed successfully")
        print(f"   Concurrent requests: 5")
        print(f"   Execution time: {execution_time:.2f} seconds")
        print(f"   All requests succeeded: {all(status == 200 for status in results)}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
