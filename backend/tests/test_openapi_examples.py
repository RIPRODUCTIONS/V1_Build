from app.main import app
from starlette.testclient import TestClient


def test_openapi_examples_present_for_life_routes():
    c = TestClient(app)
    r = c.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec.get("paths", {})
    required = [
        "/life/finance/investments",
        "/life/finance/bills",
        "/life/security/sweep",
        "/life/travel/plan",
        "/life/calendar/organize",
        "/life/shopping/optimize",
    ]
    for p in required:
        assert p in paths
        post = paths[p].get("post")
        assert post is not None
        # requestBody examples exist
        rb = post.get("requestBody", {})
        content = rb.get("content", {}).get("application/json", {})
        examples = content.get("examples", {})
        assert examples or content.get("example")
        # response example(s) exist via schema examples or explicit examples
        responses = post.get("responses", {})
        ok = responses.get("200") or responses.get("202")
        assert ok is not None
