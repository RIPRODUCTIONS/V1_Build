from __future__ import annotations

from typing import Annotated

import boto3
from app.agent.pipeline import run_agent_pipeline
from app.agent.tasks import run_pipeline_task
from app.core.config import get_settings
from app.db import get_db
from app.dependencies.auth import get_current_user
from app.models import AgentRun, Artifact, User
from app.schemas import AgentRunRequest, AgentRunResponse, ArtifactOut
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse)
def run_agent(
    payload: AgentRunRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    settings = get_settings()
    if settings.ci_env:
        # In CI/test mode, run synchronously to avoid external Redis dependency
        run = run_agent_pipeline(
            db, owner_id=current_user.id, lead_id=payload.lead_id, context=payload.context
        )
        return AgentRunResponse(run_id=run.id, status=run.status)
    else:
        # Create/initiate a run and queue background processing
        run = run_agent_pipeline(
            db,
            owner_id=current_user.id,
            lead_id=payload.lead_id,
            context=payload.context,
            run_id=None,
        )
        run_pipeline_task.delay(current_user.id, payload.lead_id, payload.context, run.id)
        return AgentRunResponse(run_id=run.id, status="queued")


@router.get("/artifacts/{run_id}", response_model=list[ArtifactOut])
def get_artifacts(
    run_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.scalars(select(Artifact).where(Artifact.run_id == run_id)).all()
    return [
        {
            "id": a.id,
            "kind": a.kind,
            "content": a.content,
            "file_path": a.file_path,
            "status": a.status,
        }
        for a in rows
    ]


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return a short-lived presigned URL for an artifact stored in S3/MinIO.
    Only the owner of the run may access.
    """

    art = db.get(Artifact, artifact_id)
    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    run = db.get(AgentRun, art.run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not art.file_path or not art.file_path.startswith("s3://"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artifact not in S3")

    # Parse s3://bucket/key
    try:
        _, rest = art.file_path.split("s3://", 1)
        bucket, key = rest.split("/", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid S3 path"
        ) from None

    settings = get_settings()
    if not (settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 not configured"
        )

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=300,
    )
    return {"url": url}
