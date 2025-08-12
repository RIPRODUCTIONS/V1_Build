# ruff: noqa: I001
import asyncio

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_submit_and_status_happy_path():
    r = client.post(
        '/automation/submit',
        json={
            'intent': 'lead.intake',
            'payload': {'lead': {'name': 'Alice'}},
            'idempotency_key': 'demo-1',
        },
    )
    assert r.status_code == 200
    run_id = r.json()['run_id']

    st = None
    for _ in range(20):
        st = client.get(f'/automation/runs/{run_id}').json()
        if st['status'] in ('succeeded', 'failed'):
            break
        # small sleep to yield control; TestClient is sync so time.sleep would also be fine
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
    assert st is not None
    assert st['status'] in ('succeeded', 'failed')
