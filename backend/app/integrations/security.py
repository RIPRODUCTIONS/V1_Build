from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal


class StoredCredential(Base):
    __tablename__ = "stored_credentials"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), index=True, nullable=False)
    integration = Column(String(100), index=True, nullable=False)
    key = Column(String(100), nullable=False)
    blob = Column(LargeBinary, nullable=False)


@dataclass(slots=True)
class CredentialVault:
    secret_key: bytes

    @staticmethod
    def from_env() -> "CredentialVault":
        raw = os.getenv("INTEGRATION_VAULT_KEY")
        if not raw:
            # Generate ephemeral key in dev; in prod must be provided
            raw = base64.urlsafe_b64encode(os.urandom(32)).decode()
        return CredentialVault(secret_key=raw.encode())

    def _fernet(self) -> Fernet:
        return Fernet(self.secret_key)

    def put(self, user_id: str, integration: str, key: str, value: str, db: Optional[Session] = None) -> None:
        close = False
        if db is None:
            db = SessionLocal()
            close = True
        try:
            blob = self._fernet().encrypt(value.encode())
            # Upsert: replace existing credential for same (user, integration, key)
            existing = (
                db.query(StoredCredential)
                .filter(StoredCredential.user_id == user_id)
                .filter(StoredCredential.integration == integration)
                .filter(StoredCredential.key == key)
                .first()
            )
            if existing:
                existing.blob = blob
            else:
                rec = StoredCredential(user_id=user_id, integration=integration, key=key, blob=blob)
                db.add(rec)
            db.commit()
        finally:
            if close:
                db.close()

    def get(self, user_id: str, integration: str, key: str, db: Optional[Session] = None) -> Optional[str]:
        close = False
        if db is None:
            db = SessionLocal()
            close = True
        try:
            rec = (
                db.query(StoredCredential)
                .filter(StoredCredential.user_id == user_id)
                .filter(StoredCredential.integration == integration)
                .filter(StoredCredential.key == key)
                .first()
            )
            if not rec:
                return None
            return self._fernet().decrypt(rec.blob).decode()
        finally:
            if close:
                db.close()


