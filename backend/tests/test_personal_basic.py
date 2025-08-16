def test_personal_research_smoke(client, auth_headers):
    res = client.post(
        "/personal/run/research_assistant",
        headers=auth_headers,
        json={"query": "AI automation trends", "max_results": 1},
    )
    assert res.status_code in (200, 202)
    data = res.json()
    assert "status" in data
    assert "task_id" in data



