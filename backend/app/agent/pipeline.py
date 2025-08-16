from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.core.config import get_settings
from app.core.event_bus import SystemEventBus


async def start_event_consumer() -> None:
    settings = get_settings()
    if not settings.SYSTEM_EVENT_CONSUMER_ENABLED:
        return
    bus = SystemEventBus()

    async def _on_operator_event(evt: Dict[str, Any]) -> None:
        from app.db import SessionLocal
        from app.models import OperatorEvent, OperatorRun

        db = SessionLocal()
        try:
            et = (evt or {}).get("type")
            data = (evt or {}).get("data") or {}
            corr = str(data.get("correlation_id") or "")
            if not corr:
                return
            run = db.query(OperatorRun).filter(OperatorRun.correlation_id == corr).first()
            if not run:
                run = OperatorRun(
                    correlation_id=corr,
                    description=str(data.get("description") or ""),
                    url=str(data.get("url") or None) if data.get("url") else None,
                    status="planned" if et == "operator.task.planned" else "running",
                )
                db.add(run)
                db.flush()
            # Update status transitions
            if et == "operator.task.started":
                run.status = "running"
            elif et == "operator.task.completed":
                run.status = str(data.get("status") or "completed")
            elif et == "operator.task.failed":
                run.status = "failed"
            # Persist event
            db.add(OperatorEvent(run_id=run.id, event_type=et or "unknown", payload=__import__("json").dumps(evt)))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    await bus.subscribe("operator.task.started", _on_operator_event)
    await bus.subscribe("operator.task.completed", _on_operator_event)
    await bus.consume(settings.EVENT_BUS_CONSUMER_GROUP, settings.EVENT_BUS_CONSUMER_NAME)

import json
import uuid

import boto3
from app.core.config import get_settings
from app.models import AgentRun, Artifact
from botocore.client import Config as BotoConfig
from sqlalchemy.orm import Session


def run_agent_pipeline(
    db: Session,
    owner_id: int,
    lead_id: int | None,
    context: str,
    run_id: int | None = None,
) -> AgentRun:
    run_obj: AgentRun | None
    if run_id is None:
        run_obj = AgentRun(owner_id=owner_id, lead_id=lead_id, status="running")
        db.add(run_obj)
        db.commit()
        db.refresh(run_obj)
    else:
        run_obj = db.get(AgentRun, run_id)
        if run_obj is None:
            run_obj = AgentRun(id=run_id, owner_id=owner_id, lead_id=lead_id, status="running")
            db.add(run_obj)
        else:
            run_obj.status = "running"
        db.commit()
        db.refresh(run_obj)

    # LangGraph-like steps (simplified deterministic pipeline)
    summary = research_agent(context)
    next_action = "Next Action: Send a follow-up email to the lead."
    draft = write_agent(summary)
    reviewed = review_agent(draft)

    # Persist artifacts (DB + optional S3)
    settings = get_settings()
    s3 = None
    if (
        settings.s3_endpoint_url
        and settings.s3_access_key
        and settings.s3_secret_key
        and settings.s3_bucket
    ):
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=BotoConfig(signature_version="s3v4"),
        )
        # Ensure bucket exists
        try:
            s3.head_bucket(Bucket=settings.s3_bucket)
        except Exception:
            s3.create_bucket(Bucket=settings.s3_bucket)

    artifacts_to_persist = [
        ("summary", summary),
        ("next_action", next_action),
        ("email_draft", draft),
        ("review", reviewed),
    ]
    # At this point run_obj exists
    run_id_val = run_obj.id
    for kind, content in artifacts_to_persist:
        if s3:
            key = f"runs/{run_id_val}/{kind}-{uuid.uuid4().hex}.json"
            data = json.dumps({"kind": kind, "content": content}).encode()
            s3.put_object(
                Bucket=settings.s3_bucket, Key=key, Body=data, ContentType="application/json"
            )
            db.add(
                Artifact(
                    run_id=run_id_val,
                    kind=kind,
                    content=f"Stored in S3 at s3://{settings.s3_bucket}/{key}",
                    file_path=f"s3://{settings.s3_bucket}/{key}",
                    status="completed",
                )
            )
        else:
            db.add(Artifact(run_id=run_id_val, kind=kind, content=content, status="completed"))

    assert run_obj is not None
    run_obj.status = "completed"
    db.commit()
    db.refresh(run_obj)
    return run_obj


def research_agent(context: str) -> str:
    ctx = context.strip()
    return f"Summary: {ctx}" if ctx else "Summary: (no context)"


def write_agent(summary: str) -> str:
    return (
        "Subject: Quick follow-up\n\n"
        "Hi there,\n\n"
        f"{summary}\n\n"
        "Let me know a good time to connect this week.\n\nBest,\nTeam"
    )


def review_agent(draft: str) -> str:
    # Simple review pass adds a footer and marks as reviewed
    return draft + "\n\n-- Reviewed: Ready to send."
