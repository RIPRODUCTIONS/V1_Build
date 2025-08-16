from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _stub_prometheus_counters_for_google(monkeypatch):
    # Avoid duplicate Prometheus metric registration across tests for Google integrations
    try:
        import app.integrations.google_workspace as gw

        class _FakeCounter:
            def labels(self, *a, **k):  # noqa: ANN001
                return self

            def inc(self, *a, **k):  # noqa: ANN001
                return None

        monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())
    except Exception:
        pass


