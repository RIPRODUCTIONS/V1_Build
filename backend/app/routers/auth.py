from typing import Annotated

from app.core.config import get_settings
from app.core.security import create_access_token
from app.dependencies.auth import get_current_subject
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenResponse:
    settings = get_settings()
    if not (
        form_data.username == settings.admin_username
        and form_data.password == settings.admin_password
    ):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(subject=form_data.username)
    return TokenResponse(access_token=token)


@router.get("/me")
def me(user: Annotated[str, Depends(get_current_subject)]):
    return {"username": user}
