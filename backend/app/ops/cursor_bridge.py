"""Cursor bridge endpoints for prompts/secrets/run logs."""

# ruff: noqa: I001
from typing import Any
import ast
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException

from app.core.config import Settings
from app.integrations.notion import Notion
from app.integrations.secrets import resolve_secret

router = APIRouter(prefix="/cursor", tags=["cursor"])


async def _get_map(r, key: str) -> dict[str, Any]:
    raw = await r.get(key)
    return ast.literal_eval(raw) if raw else {}


@router.post("/sync")
async def sync():
    s = Settings()
    n = Notion(s)
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    prompts = await n.pull_prompts()
    vault = await n.pull_vault_index()
    await r.set("notion:prompts", repr(prompts), ex=s.NOTION_SYNC_INTERVAL_S * 2)
    await r.set("notion:vault", repr(vault), ex=s.NOTION_SYNC_INTERVAL_S * 2)
    return {"prompts": len(prompts), "vault_keys": len(vault)}


@router.get("/prompt/{key}")
async def get_prompt(key: str):
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    m = await _get_map(r, "notion:prompts")
    if key not in m:
        raise HTTPException(404, "Prompt not found")
    return {"key": key, "content": m[key]}


@router.get("/secret/{key}")
async def get_secret(key: str):
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    idx = await _get_map(r, "notion:vault")
    val = resolve_secret(key, idx, s)
    if val is None:
        raise HTTPException(404, "Secret not resolved")
    return {"key": key, "value": val}


@router.post("/run-log")
async def run_log(payload: dict):
    s = Settings()
    if not (s.NOTION_TOKEN and s.NOTION_DB_RUNS):
        return {"status": "skipped"}
    n = Notion(s)
    page = await n.create_run_page(
        payload.get("run_id", ""), payload.get("intent", ""), payload.get("status", "queued")
    )
    if payload.get("summary"):
        await n.append_page_text(page, payload["summary"])
    if payload.get("detail"):
        await n.append_page_text(page, json.dumps(payload["detail"])[:1800])
    return {"status": "ok", "page_id": page}
