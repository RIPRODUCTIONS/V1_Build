from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from app.db import Base


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String, nullable=False)  # e.g. calendar.event.created
    event_pattern = Column(String, nullable=True)
    conditions = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    execution_count = Column(Integer, default=0, nullable=False)
    last_executed = Column(DateTime, nullable=True)


class RuleExecution(Base):
    __tablename__ = "rule_executions"

    id = Column(String, primary_key=True)
    rule_id = Column(String, ForeignKey("automation_rules.id"), index=True, nullable=False)
    event_id = Column(String, nullable=True)
    status = Column(String, nullable=False)  # success|failed|skipped
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)  # email, slack, sms
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
    extra = Column("metadata", JSON, nullable=True)


