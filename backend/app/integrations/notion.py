"""Notion control-plane client."""

# ruff: noqa: I001
import httpx
from typing import Any

from app.core.config import Settings

NOTION_API = "https://api.notion.com/v1"
VER = "2022-06-28"


class Notion:
    def __init__(self, s: Settings):
        if not s.NOTION_TOKEN:
            raise RuntimeError("NOTION_TOKEN missing")
        self.s = s
        self.h = {
            "Authorization": f"Bearer {s.NOTION_TOKEN}",
            "Notion-Version": VER,
            "Content-Type": "application/json",
        }

    async def _query_db(self, db_id: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor = None
        async with httpx.AsyncClient(timeout=30.0) as c:
            while True:
                body = {"start_cursor": cursor} if cursor else {}
                r = await c.post(f"{NOTION_API}/databases/{db_id}/query", headers=self.h, json=body)
                r.raise_for_status()
                data = r.json()
                out += data.get("results", [])
                if not data.get("has_more"):
                    break
                cursor = data.get("next_cursor")
        return out

    async def pull_prompts(self) -> dict[str, str]:
        if not self.s.NOTION_DB_PROMPTS:
            return {}
        rows = await self._query_db(self.s.NOTION_DB_PROMPTS)
        out: dict[str, str] = {}
        for row in rows:
            p = row["properties"]
            key = "".join(t["plain_text"] for t in p["Key"]["title"])
            rt = p.get("Content", {}).get("rich_text", [])
            out[key] = "".join(t.get("plain_text", "") for t in rt)
        return out

    async def pull_vault_index(self) -> dict[str, dict[str, str]]:
        if not self.s.NOTION_DB_VAULT:
            return {}
        rows = await self._query_db(self.s.NOTION_DB_VAULT)
        out: dict[str, dict[str, str]] = {}
        for row in rows:
            p = row["properties"]
            key = "".join(t["plain_text"] for t in p["Key"]["title"])
            prov = p.get("Provider", {}).get("select", {}).get("name", "env")
            ref = "".join(
                t.get("plain_text", "") for t in p.get("Ref/Path", {}).get("rich_text", [])
            )
            out[key] = {"provider": prov, "ref": ref}
        return out

    async def create_run_page(self, run_id: str, intent: str, status: str) -> str:
        if not self.s.NOTION_DB_RUNS:
            return ""
        async with httpx.AsyncClient(timeout=20.0) as c:
            body = {
                "parent": {"database_id": self.s.NOTION_DB_RUNS},
                "properties": {
                    "Run ID": {"title": [{"text": {"content": run_id}}]},
                    "Intent": {"rich_text": [{"text": {"content": intent}}]},
                    "Status": {"status": {"name": status}},
                },
            }
            r = await c.post(f"{NOTION_API}/pages", headers=self.h, json=body)
            r.raise_for_status()
            return r.json()["id"]

    async def append_page_text(self, page_id: str, text: str) -> None:
        if not page_id:
            return
        async with httpx.AsyncClient(timeout=20.0) as c:
            body = {
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
                    }
                ]
            }
            r = await c.patch(f"{NOTION_API}/blocks/{page_id}/children", headers=self.h, json=body)
            r.raise_for_status()
