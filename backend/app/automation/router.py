# ruff: noqa: I001
import uuid

from fastapi import APIRouter, HTTPException

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag
from app.automation.schemas import AutomationEnqueued, AutomationStatus, AutomationSubmit
from app.automation.state import get_status, list_recent, record_run_meta, set_status

router = APIRouter(prefix='/automation', tags=['automation'])


@router.post('/submit', response_model=AutomationEnqueued)
async def submit(req: AutomationSubmit):
    # Check if intent exists in registry
    from app.automation.registry import _DAGS, _SKILLS

    if req.intent not in _DAGS and req.intent not in _SKILLS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown intent '{req.intent}'. Available: DAGs: {list(_DAGS.keys())}, Skills: {list(_SKILLS.keys())}",
        )

    key, cached = await claim_or_get(req.intent, req.payload, req.idempotency_key)
    if cached:
        return AutomationEnqueued(**cached)

    run_id = str(uuid.uuid4())
    await set_status(run_id, 'queued', {'intent': req.intent})
    await record_run_meta(run_id, req.intent, req.payload)

    # Get steps - if it's a DAG, use the DAG steps; if it's a skill, wrap it in a list
    steps = _DAGS.get(req.intent, [req.intent])

    # Set status to running before execution
    await set_status(run_id, 'running', {'intent': req.intent, 'steps': steps})

    try:
        # Always run inline to guarantee progress in tests/CI environments without broker
        result = await run_dag(run_id, steps, dict(req.payload))

        # Set status to succeeded with result
        await set_status(
            run_id, 'succeeded', {'intent': req.intent, 'result': result, 'executed': steps}
        )

        resp = {'run_id': run_id, 'status': 'succeeded', 'result': result}

    except Exception as e:
        # Set status to failed with error
        await set_status(
            run_id, 'failed', {'intent': req.intent, 'error': str(e), 'executed': steps}
        )
        resp = {'run_id': run_id, 'status': 'failed', 'error': str(e)}

    await store_result(key, resp)
    return AutomationEnqueued(**resp)


@router.get('/runs/{run_id}', response_model=AutomationStatus)
async def status(run_id: str):
    st = await get_status(run_id)
    return AutomationStatus(run_id=run_id, status=st['status'], detail=st.get('detail'))


@router.get('/recent')
async def recent(limit: int = 20):
    items = await list_recent(limit=limit)
    return {'items': items}


@router.get('/runs', response_model=list[dict])
async def list_runs(
    intent: str = None,
    status: str = None,
    from_ts: str = None,
    to_ts: str = None,
    limit: int = 25,
    cursor: str = None,
):
    """List automation runs with filtering and pagination."""
    try:
        # Get recent runs
        runs_data = await list_recent(limit)

        # Apply filters
        filtered_runs = []
        for run in runs_data:
            # Filter by intent
            if intent and run.get('detail', {}).get('intent') != intent:
                continue

            # Filter by status
            if status and run.get('status') != status:
                continue

            filtered_runs.append(run)

        return filtered_runs

    except Exception as e:
        print(f'Error in list_runs: {e}')
        return []
