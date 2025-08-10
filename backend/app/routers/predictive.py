from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/predictive", tags=["predictive"])


class ForecastRequest(BaseModel):
    domain: Literal["career", "finance", "relationship", "health"]
    input: dict[str, Any] = {}


class ForecastResponse(BaseModel):
    status: str
    forecast: dict[str, Any]


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(req: ForecastRequest) -> ForecastResponse:
    return ForecastResponse(status="ok", forecast={"domain": req.domain, "confidence": 0.0})
