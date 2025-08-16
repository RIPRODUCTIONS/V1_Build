from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from app.ai.system_brain import propose_new_templates
from app.tasks.web_automation_tasks import execute_web_automation_task
from celery import shared_task


@shared_task(name="coverage.expand")
def expand_coverage(task_data: dict[str, Any]) -> dict[str, Any]:
    """Orchestrate simple coverage expansion:

    - For each topic, queue a generic web search and monitoring task
    - Ask SystemBrain to propose templates based on recent runs (best effort)
    """
    topics: list[str] = list(task_data.get("topics") or [])
    if not topics:
        topics = [
            "osint techniques",
            "financial fraud detection",
            "malware analysis sandbox",
            "cyber threat intel APT",
            "vehicle ALPR legal",
            "blockchain forensics chainalysis",
            "face recognition accuracy standards",
        ]
    queued: list[str] = []
    for t in topics[:20]:
        url = f"https://www.google.com/search?q={quote_plus(t)}"
        payload = {"description": "coverage_seed", "url": url}
        try:
            job = execute_web_automation_task.delay(payload)
            queued.append(job.id)
        except Exception:
            # Fallback to synchronous execution if broker is unavailable
            try:
                _ = execute_web_automation_task(payload)
                queued.append("sync")
            except Exception as _exc:  # pragma: no cover - best effort
                queued.append(f"error:{type(_exc).__name__}")
    # Best-effort: ask the simple heuristic proposer using recent activity context
    proposals: list[dict[str, Any]] = []
    try:
        observed: dict[str, Any] = {"platform_counts": {}}
        proposals = propose_new_templates(observed)
    except Exception:
        proposals = []
    return {"status": "ok", "queued": queued, "proposals": proposals}


