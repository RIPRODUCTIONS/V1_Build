from typing import Annotated

import jwt
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db import get_db
from app.models import User
from app.security.jwt_hs256 import HS256JWT
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_subject(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if isinstance(subject, str) and subject:
            return subject
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> int:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if isinstance(subject, str) and subject.isdigit():
            return int(subject)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None


def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_subject_hs256(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """HS256 Bearer dependency for gating selected /life/* routes only.

    Errors:
      - 401 not_authenticated: missing/empty header
      - 401 invalid_token: signature/format/issuer/audience invalid
      - 401 token_expired: exp in past
      - 401 token_not_active: nbf/iat in future
      - 403 invalid_token: decoded but no subject
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")

    settings = get_settings()
    verifier = HS256JWT(
        secret=settings.jwt_secret,
        issuer=None,
        audience=None,
        ttl_seconds=settings.access_token_expire_minutes * 60,
        leeway_seconds=0,
    )
    token = credentials.credentials
    try:
        claims = verifier.verify(token)
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired") from err
    except jwt.ImmatureSignatureError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_not_active") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from err

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_token")
    return subject
