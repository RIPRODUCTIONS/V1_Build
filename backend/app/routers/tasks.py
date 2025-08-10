from __future__ import annotations

from typing import Annotated

from app.db import get_db
from app.dependencies.auth import get_current_user
from app.models import Task, User
from app.schemas import IdResponse, TaskCreate, TaskOut, TaskUpdate
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = Task(owner_id=current_user.id, title=payload.title, lead_id=payload.lead_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return IdResponse(id=task.id)


@router.get("/", response_model=list[TaskOut])
@router.get("", response_model=list[TaskOut])
def list_tasks(  # noqa: PLR0913 - FastAPI dependency signature
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, description="Filter by title contains"),
    status_filter: str | None = Query(default=None, description="Filter by status"),
    sort: str | None = Query(
        default=None, description="Sort by 'title', 'status', or 'created_at' (prefix '-' for desc)"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Task).where(Task.owner_id == current_user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Task.title.ilike(like))
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    if sort:
        # Accept multiple sort syntaxes:
        # - Canonical: "title", "-title", "status", "-status", "created_at", "-created_at"
        # - UI-friendly: "title_asc", "title_desc", "status_asc", ..., "created_asc", "created_desc"
        desc = False
        field = sort
        if "_" in sort:
            base, direction = sort.split("_", 1)
            field = "created_at" if base == "created" else base
            desc = direction.lower() == "desc"
        else:
            desc = sort.startswith("-")
            field = sort.lstrip("-")

        if field not in {"title", "status", "created_at"}:
            raise HTTPException(status_code=400, detail="invalid sort field")
        col = getattr(Task, field)
        stmt = stmt.order_by(col.desc() if desc else col.asc())
    stmt = stmt.limit(limit).offset(offset)
    rows = db.scalars(stmt).all()
    return rows


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="task not found")
    if payload.title is not None:
        task.title = payload.title
    if payload.status is not None:
        task.status = payload.status
    if payload.lead_id is not None:
        task.lead_id = payload.lead_id
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="task not found")
    db.delete(task)
    db.commit()
