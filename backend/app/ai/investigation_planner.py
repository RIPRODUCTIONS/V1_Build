from __future__ import annotations

from typing import Any


def plan_osint(subject: dict[str, Any]) -> list[dict[str, Any]]:
    """Heuristic OSINT planner (stub ready for LLM prompt integration).

    Returns a list of steps with 'platform' and 'query' fields.
    """
    name = (subject or {}).get("name") or ""
    location = (subject or {}).get("location") or ""
    terms = [name]
    if location:
        terms.append(location)
    base_query = " ".join(t for t in terms if t).strip()
    if not base_query:
        base_query = "person of interest"
    steps: list[dict[str, Any]] = [
        {"platform": "linkedin", "query": base_query},
        {"platform": "twitter", "query": base_query},
        {"platform": "facebook", "query": base_query},
        {"platform": "instagram", "query": base_query},
        {"platform": "reddit", "query": base_query},
        {"platform": "web", "query": f"{base_query} resume OR CV OR profile"},
    ]
    return steps


