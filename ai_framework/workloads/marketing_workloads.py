from datetime import datetime

from agents.base import Task, TaskPriority


def seed_marketing_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"campaign_launch_{now}",
            task_type="campaign_planning",
            description="Plan and launch new campaign",
            priority=TaskPriority.HIGH,
            requirements={"budget": 50000},
            metadata={}
        ),
        Task(
            task_id=f"seo_audit_{now}",
            task_type="content_optimization",
            description="Run SEO audit and optimization",
            priority=TaskPriority.NORMAL,
            requirements={},
            metadata={}
        ),
    ]






