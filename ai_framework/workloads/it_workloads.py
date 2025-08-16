from datetime import datetime

from agents.base import Task, TaskPriority


def seed_it_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"patch_cycle_{now}",
            task_type="patch_management",
            description="Weekly patch management",
            priority=TaskPriority.NORMAL,
            requirements={},
            metadata={}
        ),
        Task(
            task_id=f"siem_scan_{now}",
            task_type="threat_detection",
            description="Run SIEM analysis",
            priority=TaskPriority.HIGH,
            requirements={"window_hours": 24},
            metadata={}
        ),
    ]






