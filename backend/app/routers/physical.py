from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/physical", tags=["physical"])


class TriggerRequest(BaseModel):
    action: str
    params: dict[str, Any] = {}


class TriggerResponse(BaseModel):
    status: str
    accepted: bool


@router.post("/trigger", response_model=TriggerResponse)
async def trigger(req: TriggerRequest) -> TriggerResponse:
    return TriggerResponse(status="ok", accepted=True)
