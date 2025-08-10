def test_planner_basic():
    from tools.web_research import plan_queries

    rp = plan_queries("FastAPI background tasks failing on uvicorn reload")
    assert len(rp.queries) >= 3


def test_ledger_markdown():
    from tools.web_research.citations import CitationLedger

    cl = CitationLedger()
    cl.add("Doc", "https://example.com", 0.0, ["key"])
    assert "[CIT-1]" in cl.as_markdown()
