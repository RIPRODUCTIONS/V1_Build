# Performance baseline (k6)

- Baseline summary: perf/baselines/smoke-summary.json
- Interpret p95/p99 latency and error rate; compare in PRs.
- Update baseline when material performance work lands; include justification.

## Targets
- API p95 latency: ≤ 300ms
- API error rate: < 1% (5m)
- 429 budget: ≤ 0.1% of requests (rolling 1h)
