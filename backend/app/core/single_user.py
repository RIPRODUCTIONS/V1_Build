from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User


def get_or_create_single_user(db: Optional[Session] = None) -> int:
    must_close = False
    if db is None:
        db = SessionLocal()
        must_close = True
    try:
        user = db.query(User).first()
        if user:
            return user.id
        # Create a default single user
        u = User(email="owner@local", password_hash="disabled")
        db.add(u)
        db.commit()
        return u.id
    finally:
        if must_close:
            db.close()


