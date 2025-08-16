from datetime import datetime

from agents.base import Task, TaskPriority


def seed_personal_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"calendar_sync_{now}",
            task_type="calendar",
            description="Daily calendar sync and planning",
            priority=TaskPriority.LOW,
            requirements={},
            metadata={}
        ),
        Task(
            task_id=f"travel_plan_{now}",
            task_type="itineraries",
            description="Plan upcoming travel",
            priority=TaskPriority.NORMAL,
            requirements={"trips": 2},
            metadata={}
        ),
    ]






