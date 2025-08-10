from fastapi import APIRouter
from prometheus_fastapi_instrumentator import Instrumentator

router = APIRouter()


def setup_metrics(app):  # noqa: ANN001 - FastAPI app
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
