from __future__ import annotations

import types
import pytest


def _ns(**k):
    return types.SimpleNamespace(**k)


@pytest.mark.asyncio
async def test_notion_page_create_400_bad_request(monkeypatch):
    from app.integrations.notion import Notion
    import app.integrations.notion as mod

    s = _ns(NOTION_TOKEN="t", NOTION_DB_RUNS="runs")
    n = Notion(s)

    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return self._payload

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001
            return _Resp(400, {"error": "Invalid parent page ID"})

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=20.0: _Client())

    with pytest.raises(RuntimeError, match="HTTP 400"):
        await n.create_run_page("r1", "intent", "queued")


@pytest.mark.asyncio
async def test_notion_page_create_401_unauthorized(monkeypatch):
    from app.integrations.notion import Notion
    import app.integrations.notion as mod

    s = _ns(NOTION_TOKEN="t", NOTION_DB_RUNS="runs")
    n = Notion(s)

    class _Resp:
        def __init__(self, code: int):
            self.status_code = code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return {"error": "Unauthorized"}

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001
            return _Resp(401)

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=20.0: _Client())

    with pytest.raises(RuntimeError, match="HTTP 401"):
        await n.create_run_page("r1", "intent", "queued")


@pytest.mark.asyncio
async def test_notion_page_append_400_invalid_blocks(monkeypatch):
    from app.integrations.notion import Notion
    import app.integrations.notion as mod

    s = _ns(NOTION_TOKEN="t")
    n = Notion(s)

    class _Resp:
        def __init__(self, code: int):
            self.status_code = code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return {"error": "Invalid block content"}

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def patch(self, url, headers=None, json=None):  # noqa: ANN001
            return _Resp(400)

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=20.0: _Client())

    with pytest.raises(RuntimeError, match="HTTP 400"):
        await n.append_page_text("page123", "invalid content")


@pytest.mark.asyncio
async def test_notion_database_query_timeout(monkeypatch):
    from app.integrations.notion import Notion
    import app.integrations.notion as mod

    s = _ns(NOTION_TOKEN="t", NOTION_DB_PROMPTS="db1")
    n = Notion(s)

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001
            raise RuntimeError("Request timed out")

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=30.0: _Client())

    with pytest.raises(RuntimeError, match="Request timed out"):
        await n.pull_prompts()
