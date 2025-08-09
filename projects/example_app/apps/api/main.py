from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
