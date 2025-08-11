from __future__ import annotations

from prometheus_client import Counter, Histogram

SEARCH_REQUESTS = Counter("research_search_requests_total", "Total search requests", ["adapter"])
SEARCH_ERRORS = Counter("research_search_errors_total", "Search errors", ["adapter"])
CACHE_HITS = Counter("research_cache_hits_total", "Cache hits", ["adapter"])
CACHE_MISSES = Counter("research_cache_misses_total", "Cache misses", ["adapter"])
RATE_LIMITED = Counter("research_rate_limited_total", "Requests rate-limited", ["adapter"])

SEARCH_LATENCY = Histogram("research_search_latency_seconds", "Search latency", ["adapter"])
