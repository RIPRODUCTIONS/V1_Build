import types
import pytest

from app.operator.templates.email_automation import PersonalEmailAutomation


@pytest.mark.asyncio
async def test_email_automation_success(monkeypatch):
    # Stub GmailIntegration.list_messages to return three messages
    import app.operator.templates.email_automation as ema

    class _Gmail:
        async def list_messages(self, user_id: str, q: str | None = None, max_results: int = 10):
            return {"status": "ok", "messages": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}

    monkeypatch.setattr(ema, "GmailIntegration", _Gmail)

    auto = PersonalEmailAutomation()
    # Provide deterministic message IDs and no network
    res = await auto.execute({"user_id": "1", "max_results": 3, "query": "newer_than:1d"})
    assert res["success"] is True
    assert res["emails_processed"] == 3
    assert isinstance(res["categories"], dict)


@pytest.mark.asyncio
async def test_email_automation_missing_creds(monkeypatch):
    import app.operator.templates.email_automation as ema

    class _Gmail:
        async def list_messages(self, user_id: str, q: str | None = None, max_results: int = 10):
            return {"status": "missing_creds"}

    monkeypatch.setattr(ema, "GmailIntegration", _Gmail)

    auto = PersonalEmailAutomation()
    res = await auto.execute({})
    assert res["success"] is False
    assert res["detail"]["status"] == "missing_creds"


