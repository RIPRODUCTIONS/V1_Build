from __future__ import annotations

from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload(file: UploadFile):
    # Stub: accept file and discard for now
    content = await file.read()
    return {"filename": file.filename, "size": len(content)}




