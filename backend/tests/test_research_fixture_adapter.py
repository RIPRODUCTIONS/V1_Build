import json
from pathlib import Path

from tools.web_research.cache import TTLCache
from tools.web_research.limiter import TokenBucket
from tools.web_research.search import FixtureSearchAdapter


def test_fixture_adapter_offline(tmp_path: Path):
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (fixtures / "search_index.json").write_text(
        json.dumps(
            {
                "langchain token bucket": [
                    "https://example.com/post1.html",
                    "https://example.com/post2.html",
                ]
            }
        ),
        encoding="utf-8",
    )
    (fixtures / "example_com_post1_html.html").write_text(
        "<html><head><title>P1</title></head><body><nav>Nav</nav><p>Hello A</p></body></html>",
        encoding="utf-8",
    )
    (fixtures / "example_com_post2_html.html").write_text(
        "<html><head><title>P2</title></head><body><p>Hello B</p></body></html>",
        encoding="utf-8",
    )

    cache = TTLCache(max_items=10, ttl_s=60)
    limiter = TokenBucket(rate_per_s=100)
    adapter = FixtureSearchAdapter(str(fixtures), cache=cache, limiter=limiter, fetch=None)
    # Monkey-patch to use fixture fetch
    adapter.fetch = adapter._fixture_fetch
    results = adapter.search_and_extract("langchain token bucket", limit=3)
    assert len(results) == 2
    assert results[0].title in ("P1", "P2")
    assert results[0].canonical_url.startswith("https://")
