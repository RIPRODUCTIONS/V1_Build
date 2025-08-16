from __future__ import annotations

import types
import pytest


def _settings(monkeypatch, token: str | None, db_prompts: str | None = None):
    from app.core import config as cfg

    class S(cfg.Settings):  # type: ignore[misc]
        NOTION_TOKEN: str | None
        NOTION_DB_PROMPTS: str | None

    S.NOTION_TOKEN = token
    S.NOTION_DB_PROMPTS = db_prompts
    monkeypatch.setattr(cfg, "Settings", S)
    return S()


def test_notion_requires_token(monkeypatch):
    from app.integrations.notion import Notion

    s = types.SimpleNamespace(NOTION_TOKEN=None)
    with pytest.raises(RuntimeError):
        Notion(s)


@pytest.mark.asyncio
async def test_notion_pull_prompts_empty_without_db(monkeypatch):
    from app.integrations.notion import Notion

    s = types.SimpleNamespace(NOTION_TOKEN="t", NOTION_DB_PROMPTS=None)
    n = Notion(s)
    out = await n.pull_prompts()
    assert out == {}

