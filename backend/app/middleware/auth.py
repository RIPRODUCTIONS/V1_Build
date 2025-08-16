from __future__ import annotations

import logging
import os

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


async def validate_api_key(x_api_key: str | None = Header(None)) -> str:
    """Central API key validator for Builder automation endpoints.

    - When SECURE_MODE is true, INTERNAL_API_KEY must be set and header must match.
    - When SECURE_MODE is false, allow requests, but if INTERNAL_API_KEY is set,
      require match to encourage secure-by-default local usage.
    """
    secure_mode = os.getenv("SECURE_MODE", "false").lower() == "true"
    expected = os.getenv("INTERNAL_API_KEY")

    if secure_mode:
        if not expected:
            logger.error("SECURE_MODE enabled but INTERNAL_API_KEY is not set")
            raise HTTPException(status_code=500, detail="server not configured: api key missing")
        if not x_api_key:
            logger.warning("Missing X-API-Key header in secure mode")
            raise HTTPException(status_code=401, detail="X-API-Key header required")
        if x_api_key != expected:
            logger.warning("Invalid X-API-Key provided in secure mode")
            raise HTTPException(status_code=401, detail="invalid api key")
        return x_api_key

    # Not in secure mode
    if expected:
        if not x_api_key or x_api_key != expected:
            logger.warning("Request blocked: INTERNAL_API_KEY is set; header missing or invalid")
            raise HTTPException(status_code=401, detail="invalid or missing api key")
    elif not x_api_key:
        logger.debug("Allowing request without X-API-Key (non-secure mode, no expected key)")
        return ""
    return x_api_key or ""



