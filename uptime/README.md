# Uptime checks

Set up external uptime probes for:

- GET `/health/live` (liveness)
- GET `/health/ready` (readiness)

Suggested tools: Pingdom, UptimeRobot, healthchecks.io.

Thresholds:

- Alert if 2 consecutive failures or >1% failures over 10 minutes.
- Alert if median latency increases by 2x baseline for 5 minutes.

Record SLOs and outage notes in your ops runbook.
