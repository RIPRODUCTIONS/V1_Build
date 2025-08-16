from __future__ import annotations

from prometheus_client import REGISTRY


def test_reliability_metrics_imports():
    """Test that reliability metrics modules can be imported without errors."""
    from app.reliability import circuit_breaker as cb
    from app.reliability import metrics as rel_metrics
    from app.reliability import rate_limiter as rl

    assert hasattr(rel_metrics, 'SimpleTimingMetrics')
    assert hasattr(cb, 'SimpleCircuitBreaker')
    assert hasattr(rl, 'SlidingWindowRateLimiter')


def test_reliability_metrics_collection():
    """Test that reliability metrics can be collected from registry."""
    # Get current registry state
    before_keys = set(REGISTRY._names_to_collectors.keys())

    # Import and use reliability metrics
    from app.reliability.metrics import SimpleTimingMetrics

    # Create a simple timing metric
    timing = SimpleTimingMetrics()

    # Check that metrics are registered
    after_keys = set(REGISTRY._names_to_collectors.keys())
    new_metrics = after_keys - before_keys

    # Should have added some metrics
    assert len(new_metrics) > 0


def test_reliability_circuit_breaker_metrics():
    """Test circuit breaker metrics registration and usage."""
    from app.reliability.circuit_breaker import SimpleCircuitBreaker

    # Create circuit breaker
    cb = SimpleCircuitBreaker(fail_threshold=2, reset_timeout=0.1)

    # Record some operations
    cb.record_success()
    cb.record_failure()
    cb.record_failure()  # Should open circuit

    # Verify state
    assert cb.is_open is True
    assert cb.fail_count == 2


def test_reliability_rate_limiter_metrics():
    """Test rate limiter metrics and behavior."""
    from app.reliability.rate_limiter import SlidingWindowRateLimiter

    # Create rate limiter
    rl = SlidingWindowRateLimiter(requests_per_minute=5)

    # Test rate limiting
    assert rl.is_allowed() is True
    assert rl.is_allowed() is True
    assert rl.is_allowed() is True
    assert rl.is_allowed() is True
    assert rl.is_allowed() is True

    # Should be rate limited after 5 requests
    assert rl.is_allowed() is False


def test_reliability_metrics_middleware_integration():
    """Test that reliability metrics work as middleware."""
    from app.reliability.circuit_breaker import SimpleCircuitBreaker
    from app.reliability.metrics import SimpleTimingMetrics
    from app.reliability.rate_limiter import SlidingWindowRateLimiter
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    # Create app with reliability middleware
    app = FastAPI()
    app.add_middleware(SimpleTimingMetrics)
    app.add_middleware(SimpleCircuitBreaker, fail_threshold=5, reset_timeout=1.0)
    app.add_middleware(SlidingWindowRateLimiter, requests_per_minute=10)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    # Test client
    client = TestClient(app)

    # Make request
    response = client.get("/test")
    assert response.status_code == 200

    # Verify metrics were recorded
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "http_request_duration_seconds" in metrics_response.text


def test_reliability_metrics_persistence():
    """Test that reliability metrics persist across requests."""
    from app.reliability.metrics import SimpleTimingMetrics
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    app = FastAPI()
    app.add_middleware(SimpleTimingMetrics)

    @app.get("/test1")
    async def test1():
        return {"status": "ok"}

    @app.get("/test2")
    async def test2():
        return {"status": "ok"}

    client = TestClient(app)

    # Make multiple requests
    client.get("/test1")
    client.get("/test2")
    client.get("/test1")

    # Check metrics
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    # Should have metrics for both endpoints
    assert "test1" in metrics_response.text
    assert "test2" in metrics_response.text


def test_reliability_circuit_breaker_state_transitions():
    """Test circuit breaker state transitions and metrics."""
    import time

    from app.reliability.circuit_breaker import SimpleCircuitBreaker

    # Create circuit breaker with short timeout
    cb = SimpleCircuitBreaker(fail_threshold=2, reset_timeout=0.1)

    # Initial state should be closed
    assert cb.is_open is False
    assert cb.fail_count == 0

    # Record failures until circuit opens
    cb.record_failure()
    assert cb.is_open is False
    assert cb.fail_count == 1

    cb.record_failure()
    assert cb.is_open is True
    assert cb.fail_count == 2

    # Wait for reset timeout
    time.sleep(0.15)

    # Circuit should be half-open
    assert cb.is_open is False

    # Record success to close circuit
    cb.record_success()
    assert cb.is_open is False
    assert cb.fail_count == 0


def test_reliability_rate_limiter_window_sliding():
    """Test rate limiter sliding window behavior."""
    import time

    from app.reliability.rate_limiter import SlidingWindowRateLimiter

    # Create rate limiter with 2 requests per minute
    rl = SlidingWindowRateLimiter(requests_per_minute=2)

    # First two requests should be allowed
    assert rl.is_allowed() is True
    assert rl.is_allowed() is True

    # Third request should be blocked
    assert rl.is_allowed() is False

    # Wait for window to slide (simulate time passing)
    time.sleep(0.1)  # Small delay

    # Should still be blocked (window hasn't slid enough)
    assert rl.is_allowed() is False


def test_reliability_metrics_thread_safety():
    """Test that reliability metrics are thread-safe."""
    import threading
    import time

    from app.reliability.metrics import SimpleTimingMetrics

    # Create timing metrics
    timing = SimpleTimingMetrics()

    # Shared counter
    request_count = 0

    def make_request():
        nonlocal request_count
        # Simulate request processing
        time.sleep(0.001)
        request_count += 1

    # Create multiple threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify all requests were processed
    assert request_count == 5


def test_reliability_metrics_error_handling():
    """Test that reliability metrics handle errors gracefully."""
    from app.reliability.metrics import SimpleTimingMetrics
    from fastapi import FastAPI, HTTPException
    from starlette.testclient import TestClient

    app = FastAPI()
    app.add_middleware(SimpleTimingMetrics)

    @app.get("/error")
    async def error_endpoint():
        raise HTTPException(status_code=500, detail="Internal error")

    client = TestClient(app)

    # Make request that will error
    response = client.get("/error")
    assert response.status_code == 500

    # Metrics should still be recorded even for errors
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "http_request_duration_seconds" in metrics_response.text
