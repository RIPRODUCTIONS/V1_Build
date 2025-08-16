"""
Pytest configuration for integration tests.

This file provides shared fixtures and configuration for all integration tests.
"""

import pytest
import os
import sys
from fastapi.testclient import TestClient
from app.main import app
from app.security.jwt_hs256 import HS256JWT


@pytest.fixture(scope="session")
def app_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="session")
def jwt_handler():
    """Create a JWT handler for testing."""
    return HS256JWT(secret="change-me")


@pytest.fixture
def jwt_headers(jwt_handler):
    """Generate JWT headers for authenticated requests."""
    jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
    return {"Authorization": f"Bearer {jwt_token}"}


@pytest.fixture
def admin_jwt_headers(jwt_handler):
    """Generate JWT headers for admin user."""
    jwt_token = jwt_handler.mint(subject="admin-user-456", ttl_override_seconds=3600)
    return {"Authorization": f"Bearer {jwt_token}"}


@pytest.fixture
def test_investigation_data():
    """Sample investigation data for testing."""
    return {
        "subject": {"target": "test-target.com", "type": "domain"},
        "scope": ["basic", "technical"],
        "priority": "medium",
        "max_depth": 3,
        "timeout_seconds": 300
    }


@pytest.fixture
def test_malware_data():
    """Sample malware analysis data for testing."""
    return {
        "sample": "test_sample.exe",
        "analysis_type": ["dynamic", "static"],
        "timeout_seconds": 600,
        "sandbox_config": {"os": "windows", "timeout": 300},
        "priority": "high"
    }


@pytest.fixture
def test_timeline_data():
    """Sample forensics timeline data for testing."""
    return {
        "source": "test_evidence.dd",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-02T00:00:00Z",
        "event_types": ["file_access", "network"],
        "correlation_rules": {"suspicious_ips": ["192.168.1.100"]},
        "max_events": 1000
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["RATE_LIMIT_ENABLED"] = "true"

    yield

    # Cleanup after test
    pass


@pytest.fixture(scope="session")
def test_database():
    """Setup test database if needed."""
    # For now, we'll use the in-memory/mock implementations
    # In the future, this could set up a test database
    yield None


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Add markers for integration tests
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "workflow: mark test as workflow test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for integration tests."""
    for item in items:
        # Mark all tests in integration directory as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark workflow tests
        if "workflow" in item.name:
            item.add_marker(pytest.mark.workflow)

        # Mark performance tests as slow
        if "performance" in item.name or "concurrent" in item.name:
            item.add_marker(pytest.mark.slow)
