from __future__ import annotations

import types
import pytest


def _ns(**k):
    return types.SimpleNamespace(**k)


@pytest.mark.asyncio
async def test_notion_query_db_pagination(monkeypatch):
    from app.integrations.notion import Notion
    import app.integrations.notion as mod

    s = _ns(NOTION_TOKEN="t")
    n = Notion(s)

    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("bad")

        def json(self):
            return self._payload

    class _Client:
        def __init__(self):
            self._calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001
            self._calls += 1
            if self._calls == 1:
                return _Resp(200, {"results": [{"id": "p1"}], "has_more": True, "next_cursor": "c2"})
            return _Resp(200, {"results": [{"id": "p2"}], "has_more": False})

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=30.0: _Client())

    rows = await n._query_db("db1")
    assert [r["id"] for r in rows] == ["p1", "p2"]


@pytest.mark.asyncio
async def test_notion_pull_vault_index_maps_fields(monkeypatch):
    from app.integrations.notion import Notion

    s = _ns(NOTION_TOKEN="t", NOTION_DB_VAULT="dbv")
    n = Notion(s)

    async def _fake_query(db_id: str):  # noqa: ARG001
        return [
            {
                "properties": {
                    "Key": {"title": [{"plain_text": "API_KEY"}]},
                    "Provider": {"select": {"name": "aws"}},
                    "Ref/Path": {"rich_text": [{"plain_text": "/secrets/api"}]},
                }
            }
        ]

    monkeypatch.setattr(n, "_query_db", _fake_query)
    out = await n.pull_vault_index()
    assert out == {"API_KEY": {"provider": "aws", "ref": "/secrets/api"}}


@pytest.mark.asyncio
async def test_notion_create_run_page_and_append_text(monkeypatch):
    from app.integrations.notion import Notion
    import app.integrations.notion as mod

    s = _ns(NOTION_TOKEN="t", NOTION_DB_RUNS="runs")
    n = Notion(s)

    class _Resp:
        def __init__(self, code: int, payload: dict | None = None):
            self.status_code = code
            self._payload = payload or {"id": "page123"}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("bad")

        def json(self):
            return self._payload

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001
            return _Resp(200)

        async def patch(self, url, headers=None, json=None):  # noqa: ANN001
            return _Resp(200, {"ok": True})

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=20.0: _Client())

    pid = await n.create_run_page("r1", "intent", "queued")
    assert pid == "page123"
    await n.append_page_text(pid, "hello")


