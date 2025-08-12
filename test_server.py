#!/usr/bin/env python3
"""
Minimal test server to isolate startup issues
"""
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Test server running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
