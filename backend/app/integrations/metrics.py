from __future__ import annotations

from prometheus_client import Counter, Histogram

integration_sync_duration = Histogram(
    "integration_sync_duration_seconds",
    "Time spent syncing integrations",
    labelnames=("integration", "user_id"),
)

integration_errors = Counter(
    "integration_errors_total",
    "Integration errors",
    labelnames=("integration", "error_type"),
)

credential_refresh = Counter(
    "credential_refresh_total",
    "OAuth token refreshes",
    labelnames=("integration", "result"),
)


