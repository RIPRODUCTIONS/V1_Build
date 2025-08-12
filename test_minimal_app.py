#!/usr/bin/env python3
"""
Minimal test app to isolate startup issues
"""
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Minimal Test", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Minimal app running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
