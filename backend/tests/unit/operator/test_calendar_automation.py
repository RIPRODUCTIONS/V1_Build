import types
import pytest

from app.operator.templates.calendar_automation import PersonalCalendarAutomation


@pytest.mark.asyncio
async def test_calendar_automation_success(monkeypatch):
    import app.operator.templates.calendar_automation as ca

    class _Cal:
        async def get_credentials(self, user_id: str):
            return object()
        async def _list_events(self, user_id, creds, start, end):
            return [
                {"summary": "A", "start": {"dateTime": "2024-01-01T00:00:00+00:00"}},
                {"summary": "B", "start": {"date": "2024-01-02"}},
            ]

    monkeypatch.setattr(ca, "GoogleCalendarIntegration", _Cal)

    auto = PersonalCalendarAutomation()
    res = await auto.execute({"user_id": "1"})
    assert res["success"] is True
    assert res["events_analyzed"] == 2
    assert "daily_briefing" in res and "schedule_analysis" in res


@pytest.mark.asyncio
async def test_calendar_automation_missing_creds(monkeypatch):
    import app.operator.templates.calendar_automation as ca

    class _Cal:
        async def get_credentials(self, user_id: str):
            return None

    monkeypatch.setattr(ca, "GoogleCalendarIntegration", _Cal)
    auto = PersonalCalendarAutomation()
    res = await auto.execute({})
    assert res["success"] is False and res["detail"]["status"] == "missing_creds"


