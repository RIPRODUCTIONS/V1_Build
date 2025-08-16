from __future__ import annotations

import time
import pytest

from app.reliability.circuit_breaker import CircuitBreaker


def test_circuit_breaker_closed_to_open_and_reset(monkeypatch):
    cb = CircuitBreaker(fail_threshold=2, reset_timeout=0.1)
    assert cb.is_open is False

    # Two failures reach threshold → opens
    cb.record_failure()
    assert cb.is_open is False
    cb.record_failure()
    assert cb.is_open is True

    # While open, not enough time elapsed → remains open
    assert cb.is_open is True

    # After timeout, becomes half-open/closed and counters reset
    time.sleep(0.12)
    assert cb.is_open is False
    assert cb.fail_count == 0

    # Success should keep it closed and reset counters
    cb.record_success()
    assert cb.is_open is False
    assert cb.fail_count == 0


def test_circuit_breaker_reopen_after_half_open():
    cb = CircuitBreaker(fail_threshold=1, reset_timeout=0.05)
    cb.record_failure()
    assert cb.is_open is True
    time.sleep(0.06)
    # Now half-open (internally closed) and counters reset
    assert cb.is_open is False
    # Immediate failure should reopen
    cb.record_failure()
    assert cb.is_open is True


