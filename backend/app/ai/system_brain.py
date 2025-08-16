from __future__ import annotations

from typing import Any


def plan_investigations(context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Very lightweight rule-based planner for investigation sequencing.

    Returns a list of steps like {"kind": "osint"} in the order to execute.
    """
    ctx = context or {}
    steps: list[dict[str, Any]] = []
    # Always start with OSINT for subject discovery
    steps.append({"kind": "osint"})
    # If we have any artifact sources, add forensics timeline
    if ctx.get("has_disk_image") or ctx.get("forensics_source"):
        steps.append({"kind": "forensics_timeline"})
    # If suspect binary present or URL sample, add malware dynamic
    if ctx.get("has_malware_sample"):
        steps.append({"kind": "malware_dynamic"})
    # Threat intel pass to attribute
    steps.append({"kind": "apt_attribution"})
    # Always include SCA to audit code repos when path provided
    if ctx.get("project_path"):
        steps.append({"kind": "sca"})
    # Ensure a baseline minimal path
    if not steps:
        steps = [{"kind": "osint"}, {"kind": "apt_attribution"}]
    return steps


def propose_new_templates(observed: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate basic proposals for new automation templates.

    Heuristic: if repeated investigations mention the same platform or action,
    propose a dedicated template.
    """
    proposals: list[dict[str, Any]] = []
    platforms = observed.get("platform_counts", {})
    MIN_PLATFORM_COUNT = 3
    for platform, count in platforms.items():
        if count >= MIN_PLATFORM_COUNT:
            proposals.append({
                "name": f"{platform.title()} Investigator",
                "template_id": f"investigate_{platform}",
                "category": "investigations",
                "description": f"Collect, enrich, and report on {platform} data for a subject.",
                "parameters": {"subject": {"name": ""}},
                "score": min(1.0, 0.2 + 0.1 * count),
            })
    return proposals


