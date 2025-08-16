from datetime import datetime

from agents.base import Task, TaskPriority


def seed_creative_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"design_batch_{now}",
            task_type="branding",
            description="Create design assets",
            priority=TaskPriority.NORMAL,
            requirements={"assets": 12},
            metadata={}
        ),
        Task(
            task_id=f"copy_batch_{now}",
            task_type="ad_copy",
            description="Generate ad copy",
            priority=TaskPriority.NORMAL,
            requirements={"ads": 8},
            metadata={}
        ),
    ]






