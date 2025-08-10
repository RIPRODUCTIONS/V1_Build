# ruff: noqa: I001
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import Settings
from app.prototype_builder.tasks import enqueue_build

router = APIRouter(prefix="/prototype", tags=["prototype"])


class BuildRequest(BaseModel):
    name: str
    prompt: str
    repo_dir: str | None = None


class BuildResponse(BaseModel):
    status: str
    run_id: str


def get_settings() -> Settings:
    return Settings()


@router.post("/run", response_model=BuildResponse)
async def run_build(req: BuildRequest):
    settings = get_settings()
    if not settings.PROTOTYPE_BUILDER_ENABLED:
        raise HTTPException(status_code=403, detail="Prototype builder disabled")
    run_id = await enqueue_build(req.name, req.prompt, repo_dir=req.repo_dir)
    return BuildResponse(status="queued", run_id=str(run_id))
