from datetime import datetime

from agents.base import Task, TaskPriority


def seed_legal_workloads() -> list[Task]:
    now = datetime.utcnow().isoformat()
    return [
        Task(
            task_id=f"contract_review_{now}",
            task_type="contract_drafting",
            description="Review and draft contracts",
            priority=TaskPriority.NORMAL,
            requirements={"contracts": 10},
            metadata={}
        ),
        Task(
            task_id=f"compliance_audit_{now}",
            task_type="policy_management",
            description="Run policy compliance audit",
            priority=TaskPriority.NORMAL,
            requirements={},
            metadata={}
        ),
    ]






