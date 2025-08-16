from __future__ import annotations

from datetime import datetime

from app.db import Base
from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String, Text


class CalendarSyncToken(Base):
    __tablename__ = "calendar_sync_tokens"

    user_id = Column(String(255), primary_key=True)
    calendar_id = Column(String(255), primary_key=True)
    sync_token = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GmailWatchSubscription(Base):
    __tablename__ = "gmail_watch_subscriptions"

    user_id = Column(String(255), primary_key=True)
    watch_id = Column(String(255), nullable=True)
    history_id = Column(BigInteger, nullable=True)
    expiration = Column(DateTime, nullable=True)
    webhook_url = Column(Text, nullable=True)


class DLQItem(Base):
    __tablename__ = "dlq_items"

    id = Column(String(64), primary_key=True)
    queue_name = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    error_details = Column(JSON, nullable=False)
    failed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)


