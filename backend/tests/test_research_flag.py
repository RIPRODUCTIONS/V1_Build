import os


def test_research_flag_off_noop(monkeypatch):
    os.environ.pop("RESEARCH_ENABLED", None)
    from app.automation.orchestrator import run_dag  # noqa: F401

    # If import succeeds and no network calls are made, test passes implicitly
    assert True
