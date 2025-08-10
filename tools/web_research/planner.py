from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResearchPlan:
    queries: list[str]
    rationale: str
    max_results_per_query: int = 5


def plan_queries(blocker: str) -> ResearchPlan:
    # Simple heuristic planner; extend with LLM if available.
    seeds = [blocker]
    seeds += [f"{blocker} official docs", f"{blocker} troubleshooting", f"{blocker} best practices"]
    return ResearchPlan(queries=seeds, rationale=f"Queries derived from blocker: {blocker}")
