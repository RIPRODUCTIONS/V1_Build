from __future__ import annotations

import argparse
import atexit
import os
import sys

from .cache import TTLCache
from .limiter import TokenBucket
from .planner import plan_queries
from .search import FakeSearchAdapter, FixtureSearchAdapter


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--offline", action="store_true", help="Use FixtureSearchAdapter")
    ap.add_argument(
        "--fixtures-path",
        default=os.getenv("RESEARCH_FIXTURES_DIR", "tools/web_research/fixtures"),
    )
    ap.add_argument("--stats", action="store_true", default=os.getenv("RESEARCH_STATS") == "1")
    args = ap.parse_args(argv)

    if not os.getenv("RESEARCH_ENABLED"):  # disabled by default
        print("research disabled; set RESEARCH_ENABLED=1 to enable")
        return 0
    if not args.query:
        print("missing query", file=sys.stderr)
        return 2

    cache = TTLCache(max_items=256, ttl_s=900)
    limiter = TokenBucket(rate_per_s=2.0, capacity=5)
    if args.offline:
        adapter = FixtureSearchAdapter(args.fixtures_path, cache=cache, limiter=limiter)
        # use fixture fetch
        adapter.fetch = adapter._fixture_fetch
    else:
        adapter = FakeSearchAdapter(cache=cache, limiter=limiter)

    if args.stats:

        def _dump_stats() -> None:
            print("\n== research stats ==")
            if cache:
                s = cache.stats()
                print(
                    f"cache: hits={s['hits']} misses={s['misses']} size={s['size']} max={s['max_items']} evictions={s['evictions']} ttl={s['ttl_s']}s"
                )
            if limiter:
                s2 = limiter.stats()
                print(
                    f"limiter: capacity={s2['capacity']} refill/s={s2['rate_per_s']} tokens={s2['tokens']:.2f} drops={s2['drops']}"
                )

        atexit.register(_dump_stats)

    plan = plan_queries(args.query)
    hits = adapter.search(plan.queries[0], limit=3)
    print(f"# Research results for: {args.query}")
    for h in hits:
        print(f"- {h.title} — {h.url}")
    # In-process invocation (tests): print stats immediately if requested
    if args.stats:
        # Directly print stats instead of introspecting atexit internals
        print("\n== research stats ==")
        s = cache.stats()
        print(
            f"cache: hits={s['hits']} misses={s['misses']} size={s['size']} max={s['max_items']} evictions={s['evictions']} ttl={s['ttl_s']}s"
        )
        s2 = limiter.stats()
        print(
            f"limiter: capacity={s2['capacity']} refill/s={s2['rate_per_s']} tokens={s2['tokens']:.2f} drops={s2['drops']}"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
