from datetime import datetime

from agents.base import Task, TaskPriority


def seed_operations_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"inventory_check_{now}",
            task_type="inventory_optimization",
            description="Run weekly inventory optimization",
            priority=TaskPriority.NORMAL,
            requirements={},
            metadata={}
        ),
        Task(
            task_id=f"route_plan_{now}",
            task_type="route_optimization",
            description="Daily route optimization",
            priority=TaskPriority.NORMAL,
            requirements={"routes": 120},
            metadata={}
        ),
    ]






