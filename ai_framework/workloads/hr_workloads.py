from datetime import datetime

from agents.base import Task, TaskPriority


def seed_hr_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"interview_cycle_{now}",
            task_type="candidate_screening",
            description="Screen new candidates",
            priority=TaskPriority.NORMAL,
            requirements={"candidates": 25},
            metadata={}
        ),
        Task(
            task_id=f"training_assign_{now}",
            task_type="training_needs",
            description="Assign training paths",
            priority=TaskPriority.LOW,
            requirements={},
            metadata={}
        ),
    ]






