from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote_plus

from celery import shared_task

from app.tasks.web_automation_tasks import execute_web_automation_task
from app.ai.system_brain import propose_new_templates


@shared_task(name="coverage.expand")
def expand_coverage(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrate simple coverage expansion:

    - For each topic, queue a generic web search and monitoring task
    - Ask SystemBrain to propose templates based on recent runs (best effort)
    """
    topics: List[str] = list(task_data.get("topics") or [])
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
    queued: List[str] = []
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
    proposals: List[Dict[str, Any]] = []
    try:
        observed: Dict[str, Any] = {"platform_counts": {}}
        proposals = propose_new_templates(observed)
    except Exception:
        proposals = []
    return {"status": "ok", "queued": queued, "proposals": proposals}


