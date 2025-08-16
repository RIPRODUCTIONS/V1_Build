import pytest


@pytest.mark.unit
def test_init_tracing_smoke():
    from app.ops.otel import init_tracing

    # Should not raise and should be idempotent
    init_tracing("builder-test")
    init_tracing("builder-test")


