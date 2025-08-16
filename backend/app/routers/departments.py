"""
Departments Router

This module provides endpoints for managing organizational departments.
"""

from __future__ import annotations

from app.middleware.auth import validate_api_key
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/departments", tags=["departments"], dependencies=[Depends(validate_api_key)])


class Department(BaseModel):
    id: str
    name: str
    description: str
    manager_id: str | None = None
    budget: float | None = None
    active: bool = True


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Department name")
    description: str = Field(..., min_length=1, description="Department description")
    manager_id: str | None = Field(None, description="Manager ID")
    budget: float | None = Field(None, ge=0, description="Department budget")


class DepartmentList(BaseModel):
    departments: list[Department]
    total: int
    page: int
    per_page: int


@router.get("/", response_model=list[Department])
async def list_departments(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    active: bool | None = Query(None, description="Filter by active status")
) -> list[Department]:
    """List all departments with optional filtering."""
    # Mock response for testing
    departments = [
        Department(
            id="dept-001",
            name="Engineering",
            description="Software engineering department",
            manager_id="mgr-001",
            budget=1000000.0,
            active=True
        ),
        Department(
            id="dept-002",
            name="Marketing",
            description="Marketing and communications",
            manager_id="mgr-002",
            budget=500000.0,
            active=True
        ),
        Department(
            id="dept-003",
            name="Finance",
            description="Financial operations and accounting",
            manager_id="mgr-003",
            budget=750000.0,
            active=True
        )
    ]

    # Apply active filter if specified
    if active is not None:
        departments = [d for d in departments if d.active == active]

    return departments


@router.get("/{department_id}", response_model=Department)
async def get_department(department_id: str) -> Department:
    """Get a specific department by ID."""
    # Mock response for testing
    if department_id == "dept-001":
        return Department(
            id="dept-001",
            name="Engineering",
            description="Software engineering department",
            manager_id="mgr-001",
            budget=1000000.0,
            active=True
        )

    raise HTTPException(status_code=404, detail="Department not found")


@router.post("/", response_model=Department, status_code=201)
async def create_department(department: DepartmentCreate) -> Department:
    """Create a new department."""
    # Mock response for testing
    return Department(
        id="dept-new",
        name=department.name,
        description=department.description,
        manager_id=department.manager_id,
        budget=department.budget,
        active=True
    )


@router.put("/{department_id}", response_model=Department)
async def update_department(department_id: str, department: DepartmentCreate) -> Department:
    """Update an existing department."""
    # Mock response for testing
    return Department(
        id=department_id,
        name=department.name,
        description=department.description,
        manager_id=department.manager_id,
        budget=department.budget,
        active=True
    )


@router.delete("/{department_id}")
async def delete_department(department_id: str):
    """Delete a department."""
    # Mock response for testing
    return {"message": f"Department {department_id} deleted successfully"}
