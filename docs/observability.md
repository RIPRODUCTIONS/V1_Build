# Observability

Trace issues from UI → API → Celery → S3/DB using OTEL traces and Sentry events. Include
X-Request-ID in logs; correlate by run_id for agent flows.

- API: Prometheus at /metrics, OTEL spans, Sentry events (PII disabled)
- Workers: log run_id, correlation_id, and errors with context
- Storage: artifacts paths (s3://bucket/key) recorded in DB
