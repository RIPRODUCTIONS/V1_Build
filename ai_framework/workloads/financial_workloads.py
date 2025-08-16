from datetime import datetime

from agents.base import Task, TaskPriority


def seed_financial_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    tasks: list[Task] = []

    tasks.append(Task(
        task_id=f"fin_close_{now}",
        task_type="financial_close",
        description="Monthly close processing",
        priority=TaskPriority.NORMAL,
        requirements={"period": "current_month"},
        metadata={}
    ))

    tasks.append(Task(
        task_id=f"budget_review_{now}",
        task_type="budget_review",
        description="Quarterly budget review",
        priority=TaskPriority.NORMAL,
        requirements={"period": "current_quarter"},
        metadata={}
    ))

    tasks.append(Task(
        task_id=f"fraud_scan_{now}",
        task_type="fraud_detection",
        description="Run transaction anomaly detection",
        priority=TaskPriority.HIGH,
        requirements={"hours": 24},
        metadata={}
    ))

    return tasks






