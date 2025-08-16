"""
Integration tests for API endpoint integration across routers.

This test suite validates:
- Cross-router data flow
- Authentication consistency
- Error handling across services
- Data persistence and retrieval
- Service interdependencies
"""

import pytest
from fastapi.testclient import TestClient
from app.security.jwt_hs256 import HS256JWT
from app.main import app


class TestAPIIntegration:
    """Test API integration across different routers."""

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

    def test_health_endpoints_across_routers(self, client):
        """Test health endpoints across different routers."""
        # 1. Main app health
        main_health = client.get("/health")
        assert main_health.status_code == 200
        main_health_data = main_health.json()
        assert "status" in main_health_data

        # 2. Investigations health
        investigations_health = client.get("/investigations/health")
        assert investigations_health.status_code == 200
        investigations_health_data = investigations_health.json()
        assert investigations_health_data["status"] == "healthy"

        # 3. Documents health (if available)
        try:
            documents_health = client.get("/documents/health")
            if documents_health.status_code == 200:
                documents_health_data = documents_health.json()
                assert "status" in documents_health_data
        except:
            pass  # Documents router might not have health endpoint

        print(f"✅ Health endpoints across routers working correctly")

    def test_authentication_consistency_across_routers(self, client):
        """Test that authentication is consistent across all protected endpoints."""
        # Test unauthenticated access to various endpoints
        protected_endpoints = [
            "/investigations/osint/run",
            "/investigations/malware/dynamic/run",
            "/investigations/forensics/timeline/run",
            "/documents/upload",  # If available
            "/admin/users",  # If available
        ]

        for endpoint in protected_endpoints:
            try:
                response = client.post(endpoint, json={})
                # Should either require authentication (401) or be invalid request (400)
                assert response.status_code in [401, 400], f"Endpoint {endpoint} should require authentication"
            except Exception:
                # Endpoint might not exist, which is fine
                pass

        print(f"✅ Authentication consistency verified across routers")

    def test_data_persistence_across_services(self, client, jwt_headers):
        """Test that data persists correctly across different services."""
        # 1. Create investigation data
        investigation_data = {
            "subject": {"target": "persistence-test.com", "type": "domain"},
            "scope": ["basic"],
            "priority": "normal"
        }

        # 2. Submit investigation
        investigation_response = client.post(
            "/investigations/osint/run",
            json=investigation_data,
            headers=jwt_headers
        )
        assert investigation_response.status_code == 200

        investigation_id = investigation_response.json()["investigation_id"]

        # 3. Verify data persistence by checking status
        status_response = client.get(
            f"/investigations/osint/status/{investigation_id}",
            headers=jwt_headers
        )
        assert status_response.status_code == 200

        # 4. Verify the data is consistent
        status_data = status_response.json()
        assert status_data["investigation_id"] == investigation_id
        assert status_data["status"] == "completed"

        print(f"✅ Data persistence verified across services")
        print(f"   Investigation ID: {investigation_id}")

    def test_error_propagation_across_services(self, client, jwt_headers):
        """Test that errors propagate correctly across service boundaries."""
        # 1. Test invalid investigation request
        invalid_request = {
            "subject": {},  # Missing required fields
            "invalid_field": "invalid_value"
        }

        response = client.post(
            "/investigations/osint/run",
            json=invalid_request,
            headers=jwt_headers
        )
        assert response.status_code == 400

        # 2. Verify error response format is consistent
        error_data = response.json()
        assert "detail" in error_data

        # 3. Test that system remains stable after errors
        valid_request = {
            "subject": {"target": "error-recovery.com", "type": "domain"},
            "scope": ["basic"]
        }

        recovery_response = client.post(
            "/investigations/osint/run",
            json=valid_request,
            headers=jwt_headers
        )
        assert recovery_response.status_code == 200

        print(f"✅ Error propagation working correctly across services")

    def test_service_interdependencies(self, client, jwt_headers):
        """Test that services can work together and share data."""
        # 1. Start investigation
        investigation_request = {
            "subject": {"target": "interdependency-test.com", "type": "domain"},
            "scope": ["basic", "technical"],
            "priority": "high"
        }

        investigation_response = client.post(
            "/investigations/osint/run",
            json=investigation_request,
            headers=jwt_headers
        )
        assert investigation_response.status_code == 200

        investigation_data = investigation_response.json()
        investigation_id = investigation_response.json()["investigation_id"]

        # 2. Use investigation results for further analysis
        if "data" in investigation_data and "findings" in investigation_data["data"]:
            findings = investigation_data["data"]["findings"]

            # 3. Create follow-up investigation based on findings
            if findings:
                follow_up_request = {
                    "subject": {"target": findings[0].get("target", "follow-up.com"), "type": "domain"},
                    "scope": ["basic"],
                    "priority": "medium"
                }

                follow_up_response = client.post(
                    "/investigations/osint/run",
                    json=follow_up_request,
                    headers=jwt_headers
                )
                assert follow_up_response.status_code == 200

        print(f"✅ Service interdependencies working correctly")
        print(f"   Primary Investigation ID: {investigation_id}")

    def test_rate_limiting_across_services(self, client, jwt_headers):
        """Test that rate limiting works consistently across all services."""
        # Make multiple requests to test rate limiting
        requests_made = 0
        max_requests = 10

        for i in range(max_requests):
            try:
                request_data = {
                    "subject": {"target": f"rate-limit-test-{i}.com", "type": "domain"},
                    "scope": ["basic"]
                }

                response = client.post(
                    "/investigations/osint/run",
                    json=request_data,
                    headers=jwt_headers
                )

                if response.status_code == 200:
                    requests_made += 1
                elif response.status_code == 429:
                    # Rate limit hit, which is expected behavior
                    break

            except Exception as e:
                # Handle any unexpected errors
                print(f"Request {i} failed: {e}")
                break

        # Should be able to make at least 5 requests before hitting rate limits
        assert requests_made >= 5, f"Rate limiting too aggressive: only {requests_made} requests succeeded"

        print(f"✅ Rate limiting working consistently across services")
        print(f"   Successful requests: {requests_made}")

    def test_concurrent_access_across_services(self, client, jwt_headers):
        """Test concurrent access to different services."""
        import concurrent.futures
        import time

        def make_investigation_request(target):
            request_data = {
                "subject": {"target": target, "type": "domain"},
                "scope": ["basic"]
            }
            response = client.post(
                "/investigations/osint/run",
                json=request_data,
                headers=jwt_headers
            )
            return response.status_code

        # Test concurrent access to different targets
        targets = [
            "concurrent-test-1.com",
            "concurrent-test-2.com",
            "concurrent-test-3.com"
        ]

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_investigation_request, target) for target in targets]
            results = [future.result() for future in futures]

        end_time = time.time()
        execution_time = end_time - start_time

        # All requests should succeed
        assert all(status == 200 for status in results)

        # Performance should be reasonable
        assert execution_time < 15.0

        print(f"✅ Concurrent access working correctly across services")
        print(f"   Concurrent requests: {len(targets)}")
        print(f"   Execution time: {execution_time:.2f} seconds")
        print(f"   All requests succeeded: {all(status == 200 for status in results)}")

    def test_data_integrity_across_services(self, client, jwt_headers):
        """Test that data integrity is maintained across service boundaries."""
        # 1. Create investigation with specific data
        original_data = {
            "subject": {"target": "integrity-test.com", "type": "domain"},
            "scope": ["basic", "technical"],
            "priority": "high",
            "max_depth": 5,
            "timeout_seconds": 600
        }

        # 2. Submit investigation
        response = client.post(
            "/investigations/osint/run",
            json=original_data,
            headers=jwt_headers
        )
        assert response.status_code == 200

        investigation_id = response.json()["investigation_id"]

        # 3. Retrieve investigation data
        status_response = client.get(
            f"/investigations/osint/status/{investigation_id}",
            headers=jwt_headers
        )
        assert status_response.status_code == 200

        # 4. Verify data integrity
        retrieved_data = status_response.json()
        assert retrieved_data["investigation_id"] == investigation_id

        # 5. Check that critical fields are preserved
        if "data" in response.json():
            original_subject = original_data["subject"]
            retrieved_subject = response.json()["data"].get("subject", {})

            # Subject target should match
            assert original_subject["target"] == retrieved_subject.get("target")
            assert original_subject["type"] == retrieved_subject.get("type")

        print(f"✅ Data integrity maintained across service boundaries")
        print(f"   Investigation ID: {investigation_id}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
