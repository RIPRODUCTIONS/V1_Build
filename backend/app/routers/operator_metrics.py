from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter
from prometheus_client import REGISTRY
from app.core.config import get_settings


router = APIRouter(prefix="/operator/metrics", tags=["operator:metrics"])


@router.get("/summary")
def metrics_summary() -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "tasks_started": 0,
        "tasks_completed": {},
        "actions": {},
        "action_errors": {},
    }
    try:
        p95_ms: float | None = None
        for metric in REGISTRY.collect():
            name = metric.name
            if name == "web_automation_tasks_started":
                # Counter without labels
                total = 0.0
                for s in metric.samples:
                    total += float(s.value or 0.0)
                summary["tasks_started"] = int(total)
            elif name == "web_automation_tasks_completed":
                # Counter with label status
                completed_buckets: Dict[str, int] = {}
                for s in metric.samples:
                    status: str = (s.labels.get("status") or "unknown") if s.labels else "unknown"
                    completed_buckets[status] = completed_buckets.get(status, 0) + int(s.value or 0)
                summary["tasks_completed"] = completed_buckets
            elif name == "web_automation_actions_total":
                # Counter with label action
                actions_buckets: Dict[str, int] = {}
                for s in metric.samples:
                    action_label = (s.labels.get("action") or "unknown") if s.labels else "unknown"
                    actions_buckets[action_label] = actions_buckets.get(action_label, 0) + int(s.value or 0)
                summary["actions"] = actions_buckets
            elif name == "web_automation_action_errors_total":
                error_buckets: Dict[str, int] = {}
                for s in metric.samples:
                    err_action_label = (s.labels.get("action") or "unknown") if s.labels else "unknown"
                    error_buckets[err_action_label] = error_buckets.get(err_action_label, 0) + int(s.value or 0)
                summary["action_errors"] = error_buckets
            elif name == "web_automation_task_duration_seconds":
                # Histogram without labels -> compute p95
                # Prometheus client exposes samples with _bucket, _sum, _count
                duration_buckets: List[Tuple[float, float]] = []  # (le, count)
                total_count = 0.0
                for s in metric.samples:
                    if s.name.endswith("_bucket"):
                        try:
                            le_str = s.labels.get("le") if s.labels else None
                            if le_str is None:
                                continue
                            le = float("inf") if le_str == "+Inf" else float(le_str)
                            duration_buckets.append((le, float(s.value or 0.0)))
                        except Exception:
                            continue
                    elif s.name.endswith("_count"):
                        total_count = float(s.value or 0.0)
                if total_count > 0 and duration_buckets:
                    duration_buckets.sort(key=lambda x: x[0])
                    threshold = total_count * 0.95
                    prev_count = 0.0
                    for le, count in duration_buckets:
                        if count >= threshold:
                            # Linear interpolate within this bucket relative to previous cumulative
                            bucket_count = count - prev_count
                            if bucket_count <= 0:
                                p95_ms = le * 1000.0
                            else:
                                overshoot = threshold - prev_count
                                ratio = max(0.0, min(1.0, overshoot / bucket_count))
                                p95_ms = le * 1000.0 * ratio
                            break
                        prev_count = count
        if p95_ms is not None:
            summary["p95_ms"] = round(p95_ms, 2)
    except Exception:
        # Best-effort summary
        pass
    # Include Grafana link hint if configured
    try:
        settings_obj = get_settings()
        if settings_obj.GRAFANA_BASE_URL and settings_obj.GRAFANA_DASHBOARD_UID:
            summary["grafana"] = {
                "base_url": settings_obj.GRAFANA_BASE_URL,
                "dashboard_uid": settings_obj.GRAFANA_DASHBOARD_UID,
                "dashboard_url": f"{settings_obj.GRAFANA_BASE_URL}/d/{settings_obj.GRAFANA_DASHBOARD_UID}",
            }
    except Exception:
        pass
    return summary


