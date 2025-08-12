from __future__ import annotations

import json
import uuid

import boto3
from botocore.client import Config as BotoConfig
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AgentRun, Artifact


def run_agent_pipeline(
    db: Session,
    owner_id: int,
    lead_id: int | None,
    context: str,
    run_id: int | None = None,
) -> AgentRun:
    if run_id is None:
        run = AgentRun(owner_id=owner_id, lead_id=lead_id, status='running')
        db.add(run)
        db.commit()
        db.refresh(run)
    else:
        run = db.get(AgentRun, run_id)
        if run is None:
            run = AgentRun(id=run_id, owner_id=owner_id, lead_id=lead_id, status='running')
            db.add(run)
        else:
            run.status = 'running'
        db.commit()
        db.refresh(run)

    # LangGraph-like steps (simplified deterministic pipeline)
    summary = research_agent(context)
    next_action = 'Next Action: Send a follow-up email to the lead.'
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
            's3',
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=BotoConfig(signature_version='s3v4'),
        )
        # Ensure bucket exists
        try:
            s3.head_bucket(Bucket=settings.s3_bucket)
        except Exception:
            s3.create_bucket(Bucket=settings.s3_bucket)

    artifacts_to_persist = [
        ('summary', summary),
        ('next_action', next_action),
        ('email_draft', draft),
        ('review', reviewed),
    ]
    for kind, content in artifacts_to_persist:
        if s3:
            key = f'runs/{run.id}/{kind}-{uuid.uuid4().hex}.json'
            data = json.dumps({'kind': kind, 'content': content}).encode()
            s3.put_object(
                Bucket=settings.s3_bucket, Key=key, Body=data, ContentType='application/json'
            )
            db.add(
                Artifact(
                    run_id=run.id,
                    kind=kind,
                    content=f'Stored in S3 at s3://{settings.s3_bucket}/{key}',
                    file_path=f's3://{settings.s3_bucket}/{key}',
                    status='completed',
                )
            )
        else:
            db.add(Artifact(run_id=run.id, kind=kind, content=content, status='completed'))

    run.status = 'completed'
    db.commit()
    db.refresh(run)
    return run


def research_agent(context: str) -> str:
    ctx = context.strip()
    return f'Summary: {ctx}' if ctx else 'Summary: (no context)'


def write_agent(summary: str) -> str:
    return (
        'Subject: Quick follow-up\n\n'
        'Hi there,\n\n'
        f'{summary}\n\n'
        'Let me know a good time to connect this week.\n\nBest,\nTeam'
    )


def review_agent(draft: str) -> str:
    # Simple review pass adds a footer and marks as reviewed
    return draft + '\n\n-- Reviewed: Ready to send.'
