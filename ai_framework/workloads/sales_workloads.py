from datetime import datetime

from agents.base import Task, TaskPriority


def seed_sales_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"lead_intake_{now}",
            task_type="lead_assignment",
            description="Distribute incoming leads",
            priority=TaskPriority.NORMAL,
            requirements={"count": 100},
            metadata={}
        ),
        Task(
            task_id=f"quota_check_{now}",
            task_type="quota_tracking",
            description="Weekly quota tracking",
            priority=TaskPriority.LOW,
            requirements={},
            metadata={}
        ),
    ]






