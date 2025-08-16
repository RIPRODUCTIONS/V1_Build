from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_default_db_path = (Path(__file__).resolve().parent.parent / "ai_framework.db").as_posix()
DB_URL = os.environ.get("DB_URL", f"sqlite:///{_default_db_path}")

# Engine configuration with safe defaults and Postgres pooling when applicable
_is_sqlite = DB_URL.startswith("sqlite")
_engine_kwargs: dict[str, object] = {"echo": False, "future": True}
if _is_sqlite:
	# SQLite thread-check off for async-ish usage patterns; noop for file DB if unused
	_engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
	# Assume a server SQL DB (e.g., Postgres). Enable pool and pre-ping.
	_engine_kwargs["pool_pre_ping"] = True
	try:
		_engine_kwargs["pool_size"] = int(os.environ.get("DB_POOL_SIZE", "5"))
		_engine_kwargs["max_overflow"] = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
	except Exception:
		pass

_engine = create_engine(DB_URL, **_engine_kwargs)
_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
	pass


class TenantRecord(Base):
	__tablename__ = "tenants"

	id = Column(String(64), primary_key=True, index=True)
	name = Column(String(128), nullable=False)
	created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	limits = Column(JSON, nullable=True)  # e.g., {"rpm": 120, "burst": 240}


class TaskRecord(Base):
	__tablename__ = "tasks"

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")
	task_id = Column(String(128), index=True, nullable=False)
	agent_id = Column(String(128), index=True, nullable=True)
	task_type = Column(String(128), index=True, nullable=True)
	description = Column(Text, nullable=True)
	status = Column(String(32), index=True, nullable=False, default="pending")
	created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	started_at = Column(DateTime(timezone=True), nullable=True)
	completed_at = Column(DateTime(timezone=True), nullable=True)
	result_json = Column(JSON, nullable=True)
	error = Column(Text, nullable=True)
	# SLA / ownership
	priority = Column(String(16), nullable=True)
	owner = Column(String(128), nullable=True)
	deadline_at = Column(DateTime(timezone=True), nullable=True)
	status_reason = Column(Text, nullable=True)


class AgentMetricRecord(Base):
	__tablename__ = "agent_metrics"

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")
	timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	agent_id = Column(String(128), index=True, nullable=False)
	name = Column(String(128), nullable=False)
	department = Column(String(64), index=True, nullable=False)
	status = Column(String(32), index=True, nullable=False)
	total_tasks_processed = Column(Integer, nullable=False, default=0)
	success_rate = Column(Float, nullable=False, default=0.0)
	avg_task_duration = Column(Float, nullable=False, default=0.0)


class DepartmentMetricRecord(Base):
	__tablename__ = "department_metrics"

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")
	timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	department = Column(String(64), index=True, nullable=False)
	agent_count = Column(Integer, nullable=False, default=0)
	active_agents = Column(Integer, nullable=False, default=0)
	efficiency = Column(Float, nullable=False, default=0.0)
	total_tasks = Column(Integer, nullable=False, default=0)
	completed_tasks = Column(Integer, nullable=False, default=0)


class WebhookEventRecord(Base):
	__tablename__ = "webhook_events"

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")
	source = Column(String(64), index=True, nullable=False)
	received_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	payload = Column(JSON, nullable=False)


class DLQTaskRecord(Base):
	__tablename__ = "dlq_tasks"

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")
	task_id = Column(String(128), index=True, nullable=True)
	agent_id = Column(String(128), index=True, nullable=True)
	error = Column(Text, nullable=True)
	payload = Column(JSON, nullable=True)
	attempts = Column(Integer, nullable=False, default=0)
	created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AuditLogRecord(Base):
	__tablename__ = "audit_log"

	id = Column(Integer, primary_key=True, index=True)
	timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	user_id = Column(String(128), nullable=True)
	action = Column(String(128), nullable=False)
	details = Column(JSON, nullable=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")


class FindingRecord(Base):
	__tablename__ = "security_findings"

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(String(64), index=True, nullable=True, default="default")
	created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
	source = Column(String(64), index=True, nullable=False)  # e.g., nmap, zap
	target = Column(String(256), index=True, nullable=False)
	host = Column(String(128), index=True, nullable=True)
	port = Column(Integer, nullable=True)
	severity = Column(String(16), index=True, nullable=True)  # info/low/medium/high/critical
	title = Column(String(256), nullable=False)
	description = Column(Text, nullable=True)
	data = Column(JSON, nullable=True)


def init_db() -> None:
	Base.metadata.create_all(bind=_engine)
	# Lightweight migrations only for SQLite; use Alembic for Postgres
	if not _is_sqlite:
		return
	try:
		with _engine.connect() as conn:
			# tasks
			res = conn.exec_driver_sql("PRAGMA table_info(tasks);")
			cols = {row[1] for row in res.fetchall()}
			alters = []
			for col, ddl in (
				("priority", "ALTER TABLE tasks ADD COLUMN priority VARCHAR(16) NULL;"),
				("owner", "ALTER TABLE tasks ADD COLUMN owner VARCHAR(128) NULL;"),
				("deadline_at", "ALTER TABLE tasks ADD COLUMN deadline_at DATETIME NULL;"),
				("status_reason", "ALTER TABLE tasks ADD COLUMN status_reason TEXT NULL;"),
				("tenant_id", "ALTER TABLE tasks ADD COLUMN tenant_id VARCHAR(64) NULL;")
			):
				if col not in cols:
					alters.append(ddl)
			for stmt in alters:
				with suppress(Exception):
					conn.exec_driver_sql(stmt)
			# agent_metrics
			res = conn.exec_driver_sql("PRAGMA table_info(agent_metrics);")
			cols = {row[1] for row in res.fetchall()}
			if "tenant_id" not in cols:
				with suppress(Exception):
					conn.exec_driver_sql("ALTER TABLE agent_metrics ADD COLUMN tenant_id VARCHAR(64) NULL;")
			# department_metrics
			res = conn.exec_driver_sql("PRAGMA table_info(department_metrics);")
			cols = {row[1] for row in res.fetchall()}
			if "tenant_id" not in cols:
				with suppress(Exception):
					conn.exec_driver_sql("ALTER TABLE department_metrics ADD COLUMN tenant_id VARCHAR(64) NULL;")
			# webhook_events table ensure tenant_id exists
			Base.metadata.create_all(bind=_engine)
			res = conn.exec_driver_sql("PRAGMA table_info(webhook_events);")
			cols = {row[1] for row in res.fetchall()}
			if "tenant_id" not in cols:
				with suppress(Exception):
					conn.exec_driver_sql("ALTER TABLE webhook_events ADD COLUMN tenant_id VARCHAR(64) NULL;")
			# dlq_tasks tenant_id
			res = conn.exec_driver_sql("PRAGMA table_info(dlq_tasks);")
			cols = {row[1] for row in res.fetchall()}
			if "tenant_id" not in cols:
				with suppress(Exception):
					conn.exec_driver_sql("ALTER TABLE dlq_tasks ADD COLUMN tenant_id VARCHAR(64) NULL;")
			# audit_log table
			res = conn.exec_driver_sql("PRAGMA table_info(audit_log);")
			cols = {row[1] for row in res.fetchall()}
			if "id" not in cols:
				with suppress(Exception):
					Base.metadata.create_all(bind=_engine)
			# security_findings table
			res = conn.exec_driver_sql("PRAGMA table_info(security_findings);")
			cols = {row[1] for row in res.fetchall()}
			if "id" not in cols:
				with suppress(Exception):
					Base.metadata.create_all(bind=_engine)
	except Exception:
		pass


class _SessionManager:
	def __init__(self) -> None:
		self._session: Session | None = None

	def __enter__(self) -> Session:
		self._session = _SessionLocal()
		return self._session

	def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-redef]
		assert self._session is not None
		try:
			if exc_type is None:
				self._session.commit()
			else:
				self._session.rollback()
		finally:
			self._session.close()


def get_session() -> _SessionManager:
	return _SessionManager()


@dataclass
class TaskData:
	"""Task data for upsert operations."""
	task_id: str
	agent_id: str | None = None
	task_type: str | None = None
	description: str | None = None
	status: str = "pending"
	created_at: datetime | None = None
	started_at: datetime | None = None
	completed_at: datetime | None = None
	result: dict[str, Any] | None = None
	error: str | None = None
	priority: str | None = None
	owner: str | None = None
	deadline_at: datetime | None = None
	status_reason: str | None = None
	tenant_id: str | None = "default"

def upsert_task(task_data: TaskData) -> None:
	with get_session() as session_ctx:
		session: Session = session_ctx
		rec: TaskRecord | None = session.query(TaskRecord).filter(TaskRecord.task_id == task_data.task_id).one_or_none()
		if rec is None:
			rec = TaskRecord(
				tenant_id=task_data.tenant_id,
				task_id=task_data.task_id,
				agent_id=task_data.agent_id,
				task_type=task_data.task_type,
				description=task_data.description,
				status=task_data.status,
				created_at=task_data.created_at or datetime.now(UTC),
				started_at=task_data.started_at,
				completed_at=task_data.completed_at,
				result_json=task_data.result,
				error=task_data.error,
				priority=task_data.priority,
				owner=task_data.owner,
				deadline_at=task_data.deadline_at,
				status_reason=task_data.status_reason,
			)
			session.add(rec)
		else:
			# Assign updates (cast to Any for SQLAlchemy ORM attributes)
			rec_any: Any = rec
			rec_any.tenant_id = task_data.tenant_id or rec_any.tenant_id
			rec_any.agent_id = task_data.agent_id or rec_any.agent_id
			rec_any.task_type = task_data.task_type or rec_any.task_type
			rec_any.description = task_data.description or rec_any.description
			rec_any.status = task_data.status
			rec_any.started_at = task_data.started_at or rec_any.started_at
			rec_any.completed_at = task_data.completed_at or rec_any.completed_at
			if task_data.result is not None:
				rec_any.result_json = task_data.result
			if task_data.error is not None:
				rec_any.error = task_data.error
			rec_any.priority = task_data.priority or rec_any.priority
			rec_any.owner = task_data.owner or rec_any.owner
			rec_any.deadline_at = task_data.deadline_at or rec_any.deadline_at
			rec_any.status_reason = task_data.status_reason or rec_any.status_reason


def log_task_start(*, task_data: dict[str, Any]) -> None:
	"""Record a task start using the TaskData dataclass expected by upsert_task."""
	# Extract required fields with defaults
	task_id = task_data.get("task_id")
	agent_id = task_data.get("agent_id")
	task_type = task_data.get("task_type")
	description = task_data.get("description")
	started_at = task_data.get("started_at")
	priority = task_data.get("priority")
	owner = task_data.get("owner")
	deadline_at = task_data.get("deadline_at")
	tenant_id = task_data.get("tenant_id", "default")

	data = TaskData(
		tenant_id=tenant_id,
		task_id=task_id,
		agent_id=agent_id,
		task_type=task_type,
		description=description,
		status="running",
		started_at=started_at,
		priority=priority,
		owner=owner,
		deadline_at=deadline_at,
	)
	upsert_task(data)


def log_task_complete(*, task_data: dict[str, Any]) -> None:
	"""Record a task completion using TaskData to satisfy type checking."""
	# Extract required fields with defaults
	task_id = task_data.get("task_id")
	agent_id = task_data.get("agent_id")
	completed_at = task_data.get("completed_at")
	result = task_data.get("result")
	error = task_data.get("error")
	tenant_id = task_data.get("tenant_id", "default")

	data = TaskData(
		tenant_id=tenant_id,
		task_id=task_id,
		agent_id=agent_id,
		status="failed" if error else "completed",
		completed_at=completed_at,
		result=result,
		error=error,
	)
	upsert_task(data)


def save_agent_metric(*, metric_data: dict[str, Any]) -> None:
	"""Save agent metrics using a dictionary to reduce parameter count."""
	with get_session() as session_ctx:
		session: Session = session_ctx
		rec = AgentMetricRecord(
			tenant_id=metric_data.get("tenant_id", "default"),
			timestamp=metric_data.get("timestamp") or datetime.now(UTC),
			agent_id=metric_data.get("agent_id"),
			name=metric_data.get("name"),
			department=metric_data.get("department"),
			status=metric_data.get("status"),
			total_tasks_processed=metric_data.get("total_tasks_processed"),
			success_rate=metric_data.get("success_rate"),
			avg_task_duration=metric_data.get("avg_task_duration"),
		)
		session.add(rec)


def save_department_metric(*, metric_data: dict[str, Any]) -> None:
	"""Save department metrics using a dictionary to reduce parameter count."""
	with get_session() as session_ctx:
		session: Session = session_ctx
		rec = DepartmentMetricRecord(
			tenant_id=metric_data.get("tenant_id", "default"),
			timestamp=metric_data.get("timestamp") or datetime.now(UTC),
			department=metric_data.get("department"),
			agent_count=metric_data.get("agent_count"),
			active_agents=metric_data.get("active_agents"),
			efficiency=metric_data.get("efficiency"),
			total_tasks=metric_data.get("total_tasks"),
			completed_tasks=metric_data.get("completed_tasks"),
		)
		session.add(rec)


def save_webhook_event(*, source: str, payload: dict[str, Any], tenant_id: str | None = "default") -> None:
	with get_session() as session_ctx:
		session: Session = session_ctx
		session.add(WebhookEventRecord(source=source, payload=payload, tenant_id=tenant_id))


def save_dlq_task(*, dlq_data: dict[str, Any]) -> None:
	"""Save DLQ task using a dictionary to reduce parameter count."""
	with get_session() as session_ctx:
		session: Session = session_ctx
		session.add(DLQTaskRecord(
			tenant_id=dlq_data.get("tenant_id", "default"),
			task_id=dlq_data.get("task_id"),
			agent_id=dlq_data.get("agent_id"),
			error=dlq_data.get("error"),
			payload=dlq_data.get("payload"),
			attempts=dlq_data.get("attempts")
		))


def delete_dlq_task(task_id: str | None, agent_id: str | None) -> None:
	with get_session() as session_ctx:
		session: Session = session_ctx
		q = session.query(DLQTaskRecord)
		if task_id:
			q = q.filter(DLQTaskRecord.task_id == task_id)
		if agent_id:
			q = q.filter(DLQTaskRecord.agent_id == agent_id)
		for r in q.all():
			session.delete(r)


def save_audit_log(*, user_id: str | None, action: str, details: dict[str, Any] | None = None, tenant_id: str | None = "default") -> None:
	with get_session() as session_ctx:
		session: Session = session_ctx
		session.add(AuditLogRecord(user_id=user_id, action=action, details=details or {}, tenant_id=tenant_id))


def save_finding(*, finding_data: dict[str, Any]) -> None:
	"""Save finding using a dictionary to reduce parameter count."""
	with get_session() as session_ctx:
		session: Session = session_ctx
		rec = FindingRecord(
			tenant_id=finding_data.get("tenant_id", "default"),
			source=finding_data.get("source"),
			target=finding_data.get("target"),
			host=finding_data.get("host"),
			port=finding_data.get("port"),
			severity=finding_data.get("severity"),
			title=finding_data.get("title"),
			description=finding_data.get("description"),
			data=finding_data.get("data") or {},
		)
		session.add(rec)


def list_findings(limit: int = 100) -> list[dict[str, Any]]:
	with get_session() as session_ctx:
		session: Session = session_ctx
		rows = (
			session.query(FindingRecord)
			.order_by(FindingRecord.created_at.desc())
			.limit(max(1, min(limit, 1000)))
			.all()
		)
		return [
			{
				"id": r.id,
				"source": r.source,
				"target": r.target,
				"host": r.host,
				"port": r.port,
				"severity": r.severity,
				"title": r.title,
				"description": r.description,
				"created_at": r.created_at.isoformat() if r.created_at else None,
				"data": r.data,
			}
			for r in rows
		]


def create_tenant(tenant_id: str, name: str, limits: dict[str, Any] | None = None) -> None:
	with get_session() as session_ctx:
		session: Session = session_ctx
		exists = session.query(TenantRecord).filter(TenantRecord.id == tenant_id).first()
		if exists:
			return
		session.add(TenantRecord(id=tenant_id, name=name, limits=limits or {"rpm": 120, "burst": 240}))


def list_tenants() -> list[dict[str, Any]]:
	with get_session() as session_ctx:
		session: Session = session_ctx
		rows = session.query(TenantRecord).order_by(TenantRecord.created_at.desc()).all()
		return [{"id": r.id, "name": r.name, "created_at": r.created_at.isoformat(), "limits": r.limits} for r in rows]


def set_tenant_limits(tenant_id: str, limits: Any) -> None:
	with get_session() as session_ctx:
		session: Session = session_ctx
		q = session.query(TenantRecord).filter(TenantRecord.id == tenant_id)
		if q.first():
			# Avoid static type issues by using ORM update
			q.update({"limits": limits})
