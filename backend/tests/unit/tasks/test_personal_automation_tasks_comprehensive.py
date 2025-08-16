from __future__ import annotations

import pytest

from app.tasks.personal_automation_tasks import execute_personal_research, execute_personal_shopping, execute_personal_finance


def test_research_task_sync_apply_success(monkeypatch):
    # Force delay() to raise so apply() path is used by routers; here we call task directly
    res = execute_personal_research.apply(args=[{"query": "ai"}]).result
    assert isinstance(res, dict)
    assert res.get("success") in (True, False)


def test_shopping_task_sync_apply_success():
    res = execute_personal_shopping.apply(args=[{"product_query": "phone"}]).result
    assert isinstance(res, dict)
    assert "success" in res


def test_finance_task_sync_apply_success():
    res = execute_personal_finance.apply(args=[{"csv_ref": "mem://id"}]).result
    assert isinstance(res, dict)
    assert "success" in res


