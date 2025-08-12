from fastapi import Query

MAX_LIMIT = 100


def limit_param(limit: int = Query(25, ge=1, le=MAX_LIMIT)) -> int:  # noqa: B008
    return limit


def offset_param(offset: int = Query(0, ge=0)) -> int:  # noqa: B008
    return offset


