"""
Tasks Catalog Router

This module provides endpoints for managing task catalogs and task definitions.
"""

from __future__ import annotations

from app.middleware.auth import validate_api_key
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tasks-catalog", tags=["tasks-catalog"], dependencies=[Depends(validate_api_key)])


class TaskDefinition(BaseModel):
    id: str
    name: str
    description: str
    category: str
    priority: str
    estimated_duration: int | None = None
    required_skills: list[str] = []
    dependencies: list[str] = []
    active: bool = True


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Task name")
    description: str = Field(..., min_length=1, description="Task description")
    category: str = Field(..., description="Task category")
    priority: str = Field(..., description="Task priority")
    estimated_duration: int | None = Field(None, ge=1, description="Estimated duration in minutes")
    required_skills: list[str] = Field(default_factory=list, description="Required skills")
    dependencies: list[str] = Field(default_factory=list, description="Task dependencies")


class TaskList(BaseModel):
    tasks: list[TaskDefinition]
    total: int
    page: int
    per_page: int


@router.get("/", response_model=list[TaskDefinition])
async def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: str | None = Query(None, description="Filter by category"),
    priority: str | None = Query(None, description="Filter by priority"),
    active: bool | None = Query(None, description="Filter by active status")
) -> list[TaskDefinition]:
    """List all tasks with optional filtering."""
    # Mock response for testing
    tasks = [
        TaskDefinition(
            id="task-001",
            name="Code Review",
            description="Review pull request for security vulnerabilities",
            category="Development",
            priority="High",
            estimated_duration=60,
            required_skills=["Python", "Security"],
            dependencies=[],
            active=True
        ),
        TaskDefinition(
            id="task-002",
            name="Security Audit",
            description="Perform security audit of production systems",
            category="Security",
            priority="Critical",
            estimated_duration=240,
            required_skills=["Security", "Networking"],
            dependencies=["task-001"],
            active=True
        ),
        TaskDefinition(
            id="task-003",
            name="Documentation Update",
            description="Update API documentation",
            category="Documentation",
            priority="Medium",
            estimated_duration=120,
            required_skills=["Technical Writing"],
            dependencies=[],
            active=True
        )
    ]

    # Apply filters
    if category:
        tasks = [t for t in tasks if t.category.lower() == category.lower()]
    if priority:
        tasks = [t for t in tasks if t.priority.lower() == priority.lower()]
    if active is not None:
        tasks = [t for t in tasks if t.active == active]

    return tasks


@router.get("/{task_id}", response_model=TaskDefinition)
async def get_task(task_id: str) -> TaskDefinition:
    """Get a specific task by ID."""
    # Mock response for testing
    if task_id == "task-001":
        return TaskDefinition(
            id="task-001",
            name="Code Review",
            description="Review pull request for security vulnerabilities",
            category="Development",
            priority="High",
            estimated_duration=60,
            required_skills=["Python", "Security"],
            dependencies=[],
            active=True
        )

    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/", response_model=TaskDefinition, status_code=201)
async def create_task(task: TaskCreate) -> TaskDefinition:
    """Create a new task."""
    # Mock response for testing
    return TaskDefinition(
        id="task-new",
        name=task.name,
        description=task.description,
        category=task.category,
        priority=task.priority,
        estimated_duration=task.estimated_duration,
        required_skills=task.required_skills,
        dependencies=task.dependencies,
        active=True
    )


@router.put("/{task_id}", response_model=TaskDefinition)
async def update_task(task_id: str, task: TaskCreate) -> TaskDefinition:
    """Update an existing task."""
    # Mock response for testing
    return TaskDefinition(
        id=task_id,
        name=task.name,
        description=task.description,
        category=task.category,
        priority=task.priority,
        estimated_duration=task.estimated_duration,
        required_skills=task.required_skills,
        dependencies=task.dependencies,
        active=True
    )


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    # Mock response for testing
    return {"message": f"Task {task_id} deleted successfully"}


@router.get("/categories", response_model=list[str])
async def list_categories() -> list[str]:
    """List all available task categories."""
    return ["Development", "Security", "Documentation", "Testing", "Deployment"]


@router.get("/priorities", response_model=list[str])
async def list_priorities() -> list[str]:
    """List all available task priorities."""
    return ["Critical", "High", "Medium", "Low"]
