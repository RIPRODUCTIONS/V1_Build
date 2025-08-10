from __future__ import annotations

import argparse
import os
import sys

from .planner import plan_queries
from .search import FakeSearchAdapter


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--real", action="store_true", help="use real adapter (not implemented)")
    args = ap.parse_args(argv)

    if not os.getenv("RESEARCH_ENABLED"):  # disabled by default
        print("research disabled; set RESEARCH_ENABLED=1 to enable")
        return 0
    if not args.query:
        print("missing query", file=sys.stderr)
        return 2
    plan = plan_queries(args.query)
    adapter = FakeSearchAdapter()
    hits = adapter.search(plan.queries[0], limit=3)
    print(f"# Research results for: {args.query}")
    for h in hits:
        print(f"- {h.title} — {h.url}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
