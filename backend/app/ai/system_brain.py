from __future__ import annotations

from typing import Any, Dict, List


def plan_investigations(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Very lightweight rule-based planner for investigation sequencing.

    Returns a list of steps like {"kind": "osint"} in the order to execute.
    """
    ctx = context or {}
    steps: List[Dict[str, Any]] = []
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


