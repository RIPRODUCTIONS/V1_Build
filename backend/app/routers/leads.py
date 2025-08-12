from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import get_current_user
from app.models import Lead, User
from app.schemas import IdResponse, LeadCreate, LeadOut, LeadUpdate

router = APIRouter(prefix='/leads', tags=['leads'])


@router.post('/', response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    lead = Lead(
        owner_id=current_user.id, name=payload.name, email=payload.email, notes=payload.notes
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return IdResponse(id=lead.id)


@router.get('/', response_model=list[LeadOut])
@router.get('', response_model=list[LeadOut])
def list_leads(  # noqa: PLR0913 - FastAPI dependency signature
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, description='Filter by name/email contains'),
    sort: str | None = Query(
        default=None, description="Sort by 'name' or 'created_at' (prefix '-' for desc)"
    ),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Lead).where(Lead.owner_id == current_user.id)
    if q:
        like = f'%{q}%'
        stmt = stmt.where(or_(Lead.name.ilike(like), Lead.email.ilike(like)))
    if sort:
        # Accept multiple sort syntaxes:
        # - Canonical: "name", "-name", "created_at", "-created_at"
        # - UI-friendly: "name_asc", "name_desc", "created_asc", "created_desc"
        desc = False
        field = sort
        if '_' in sort:
            base, direction = sort.split('_', 1)
            field = 'created_at' if base == 'created' else base
            desc = direction.lower() == 'desc'
        else:
            desc = sort.startswith('-')
            field = sort.lstrip('-')

        if field not in {'name', 'created_at'}:
            raise HTTPException(status_code=400, detail='invalid sort field')
        col = getattr(Lead, field)
        stmt = stmt.order_by(col.desc() if desc else col.asc())
    stmt = stmt.limit(limit).offset(offset)
    rows = db.scalars(stmt).all()
    return rows


@router.get('/{lead_id}', response_model=LeadOut)
def get_lead(
    lead_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    lead = db.get(Lead, lead_id)
    if not lead or lead.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail='lead not found')
    return lead


@router.put('/{lead_id}', response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    lead = db.get(Lead, lead_id)
    if not lead or lead.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail='lead not found')
    if payload.name is not None:
        lead.name = payload.name
    if payload.email is not None:
        lead.email = payload.email
    if payload.notes is not None:
        lead.notes = payload.notes
    db.commit()
    db.refresh(lead)
    return lead


@router.delete('/{lead_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    lead = db.get(Lead, lead_id)
    if not lead or lead.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail='lead not found')
    db.delete(lead)
    db.commit()
