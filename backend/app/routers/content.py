from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix='/content', tags=['content'])


class GenerateRequest(BaseModel):
    kind: Literal['text', 'image', 'audio', 'video'] = 'text'
    prompt: str


class GenerateResponse(BaseModel):
    status: str
    result: dict[str, Any]


@router.post('/generate', response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(status='ok', result={'kind': req.kind, 'id': 'placeholder'})
