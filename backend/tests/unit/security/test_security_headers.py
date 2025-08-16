def test_security_headers_present(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    # Middleware attaches these
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"



