from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Request
from pydantic import BaseModel

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag
from app.automation.state import set_status
from app.dependencies.auth import require_scope_hs256, require_subject_hs256
from app.services.queue.redis_bus import get_bus

router = APIRouter(
    prefix='/life',
    tags=['life-automation'],
)


class SimpleReq(BaseModel):
    payload: dict[str, Any] | None = None
    idempotency_key: str | None = None

    model_config = {
        'json_schema_extra': {
            'examples': [{'payload': {'example': True}, 'idempotency_key': 'idem-abc'}]
        }
    }


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str

    model_config = {
        'json_schema_extra': {
            'examples': [
                {'run_id': 'run_01HXYZ', 'status': 'queued'},
                {'run_id': 'run_01HABC', 'status': 'succeeded'},
            ]
        }
    }


async def _inline(
    intent: str, payload: dict[str, Any] | None, idem_key: str | None
) -> EnqueuedResponse:
    p = payload or {}
    key, cached = await claim_or_get(intent, p, idem_key)
    if cached:
        return EnqueuedResponse(**cached)
    run_id = str(uuid.uuid4())
    await set_status(
        run_id, 'queued', {'intent': intent, 'correlation_id': p.get('correlation_id')}
    )
    # Emit domain event
    try:
        bus = get_bus()
        event = {
            'event_type': 'automation.run.requested',
            'version': 'v1',
            'intent': intent,
            'payload': p,
            'idempotency_key': idem_key,
            'correlation_id': p.get('correlation_id'),
        }
        bus.emit(event['event_type'], event)
    except Exception:
        pass
    # Directly enqueue orchestration; steps are resolved by orchestrator from registered DAGs
    await run_dag(run_id, [], dict(p))
    resp = {'run_id': run_id, 'status': 'queued'}
    await store_result(key, resp)
    return EnqueuedResponse(**resp)


_auth_responses = {
    401: {
        'description': 'Unauthorized',
        'content': {
            'application/json': {
                'examples': {
                    'not_authenticated': {'value': {'detail': 'not_authenticated'}},
                    'invalid_token': {'value': {'detail': 'invalid_token'}},
                    'token_expired': {'value': {'detail': 'token_expired'}},
                    'token_not_active': {'value': {'detail': 'token_not_active'}},
                }
            }
        },
    },
    403: {
        'description': 'Forbidden',
        'content': {
            'application/json': {
                'examples': {'invalid_token_no_subject': {'value': {'detail': 'invalid_token'}}}
            }
        },
    },
}


@router.post('/health/wellness', response_model=EnqueuedResponse, responses=_auth_responses)
async def wellness(
    _: SimpleReq, subject: str = Depends(require_subject_hs256), request: Request = None
) -> EnqueuedResponse:
    """Trigger daily wellness automation. Requires bearerAuth (JWT)."""
    _ = subject
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('health.wellness_daily', {'correlation_id': corr} if corr else {}, None)


@router.post('/nutrition/plan', response_model=EnqueuedResponse, responses=_auth_responses)
async def nutrition(
    _: SimpleReq, subject: str = Depends(require_subject_hs256), request: Request = None
) -> EnqueuedResponse:
    """Plan nutrition tasks. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('nutrition.plan', {'correlation_id': corr} if corr else {}, None)


@router.post('/home/evening', response_model=EnqueuedResponse, responses=_auth_responses)
async def home(
    _: SimpleReq, subject: str = Depends(require_subject_hs256), request: Request = None
) -> EnqueuedResponse:
    """Run evening home scene. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('home.evening_scene', {'correlation_id': corr} if corr else {}, None)


@router.post('/transport/commute', response_model=EnqueuedResponse, responses=_auth_responses)
async def transport(
    _: SimpleReq, subject: str = Depends(require_subject_hs256), request: Request = None
) -> EnqueuedResponse:
    """Commute helper. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('transport.commute', {'correlation_id': corr} if corr else {}, None)


@router.post('/learning/upskill', response_model=EnqueuedResponse, responses=_auth_responses)
async def learning(
    _: SimpleReq, subject: str = Depends(require_subject_hs256), request: Request = None
) -> EnqueuedResponse:
    """Upskill plan. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('learning.upskill', {'correlation_id': corr} if corr else {}, None)


@router.post(
    '/finance/investments',
    response_model=EnqueuedResponse,
    openapi_extra={
        'requestBody': {
            'content': {
                'application/json': {
                    'examples': {
                        'happy_path': {
                            'summary': 'Trigger investments analysis',
                            'value': {'payload': {'accounts': ['broker:abc'], 'rebalance': True}},
                        },
                        'validation_error': {
                            'summary': 'Missing required fields',
                            'value': {'payload': {}},
                        },
                    }
                }
            }
        }
    },
)
async def finance_investments(
    _: Annotated[
        SimpleReq,
        Body(
            examples={
                'happy_path': {
                    'summary': 'Trigger investments analysis',
                    'value': {'payload': {'accounts': ['broker:abc'], 'rebalance': True}},
                },
                'validation_error': {
                    'summary': 'Missing payload shape',
                    'value': {'payload': {}},
                },
            }
        ),
    ],
    subject: str = Depends(require_scope_hs256('life.finance')),
    request: Request = None,
) -> EnqueuedResponse:
    _ = subject  # subject is currently unused; provided for future auditing/attribution
    """Analyze investments. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline(
        'finance.investments_daily', {'correlation_id': corr} if corr else {}, None
    )


@router.post(
    '/finance/bills',
    response_model=EnqueuedResponse,
    openapi_extra={
        'requestBody': {
            'content': {
                'application/json': {
                    'examples': {
                        'happy_path': {
                            'summary': 'Detect and schedule bills',
                            'value': {'payload': {'accounts': ['chk:123']}},
                        },
                        'validation_error': {
                            'summary': 'Empty accounts',
                            'value': {'payload': {'accounts': []}},
                        },
                    }
                }
            }
        }
    },
)
async def finance_bills(
    _: Annotated[
        SimpleReq,
        Body(
            examples={
                'happy_path': {
                    'summary': 'Trigger bills detection/scheduling',
                    'value': {'payload': {'accounts': ['chk:123']}},
                },
                'validation_error': {
                    'summary': 'Empty accounts',
                    'value': {'payload': {'accounts': []}},
                },
            }
        ),
    ],
    subject: str = Depends(require_scope_hs256('life.finance')),
    request: Request = None,
) -> EnqueuedResponse:
    _ = subject
    """Detect and schedule bills. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('finance.bills_monthly', {'correlation_id': corr} if corr else {}, None)


@router.post(
    '/security/sweep',
    response_model=EnqueuedResponse,
    openapi_extra={
        'requestBody': {
            'content': {
                'application/json': {
                    'examples': {
                        'happy_path': {
                            'summary': 'Run weekly security sweep',
                            'value': {'payload': {'scope': 'device'}},
                        },
                        'bad_scope': {
                            'summary': 'Unsupported scope',
                            'value': {'payload': {'scope': 'unknown'}},
                        },
                    }
                }
            }
        }
    },
)
async def security_sweep(
    _: Annotated[
        SimpleReq,
        Body(
            examples={
                'happy_path': {
                    'summary': 'Run weekly security sweep',
                    'value': {'payload': {'scope': 'device'}},
                },
                'bad_scope': {
                    'summary': 'Unsupported scope',
                    'value': {'payload': {'scope': 'unknown'}},
                },
            }
        ),
    ],
    subject: str = Depends(require_subject_hs256),
    request: Request = None,
) -> EnqueuedResponse:
    _ = subject
    """Run weekly security sweep. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('security.weekly_sweep', {'correlation_id': corr} if corr else {}, None)


@router.post(
    '/travel/plan',
    response_model=EnqueuedResponse,
    openapi_extra={
        'requestBody': {
            'content': {
                'application/json': {
                    'examples': {
                        'happy_path': {
                            'summary': 'Plan travel',
                            'value': {
                                'payload': {'from': 'SFO', 'to': 'JFK', 'date': '2025-09-01'}
                            },
                        },
                        'validation_error': {
                            'summary': "Missing 'to'",
                            'value': {'payload': {'from': 'SFO'}},
                        },
                    }
                }
            }
        }
    },
)
async def travel_plan(
    _: Annotated[
        SimpleReq,
        Body(
            examples={
                'happy_path': {
                    'summary': 'Plan travel',
                    'value': {'payload': {'from': 'SFO', 'to': 'JFK', 'date': '2025-09-01'}},
                },
                'validation_error': {
                    'summary': "Missing 'to'",
                    'value': {'payload': {'from': 'SFO'}},
                },
            }
        ),
    ],
    subject: str = Depends(require_subject_hs256),
    request: Request = None,
) -> EnqueuedResponse:
    _ = subject
    """Plan travel. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('travel.plan', {'correlation_id': corr} if corr else {}, None)


@router.post(
    '/calendar/organize',
    response_model=EnqueuedResponse,
    openapi_extra={
        'requestBody': {
            'content': {
                'application/json': {
                    'examples': {
                        'happy_path': {
                            'summary': 'Organize day',
                            'value': {'payload': {'window_days': 3}},
                        }
                    }
                }
            }
        }
    },
)
async def calendar_organize(
    _: Annotated[
        SimpleReq,
        Body(
            examples={
                'happy_path': {
                    'summary': 'Organize day',
                    'value': {'payload': {'window_days': 3}},
                }
            }
        ),
    ],
    subject: str = Depends(require_subject_hs256),
    request: Request = None,
) -> EnqueuedResponse:
    _ = subject
    """Organize calendar. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('calendar.organize_day', {'correlation_id': corr} if corr else {}, None)


@router.post(
    '/shopping/optimize',
    response_model=EnqueuedResponse,
    openapi_extra={
        'requestBody': {
            'content': {
                'application/json': {
                    'examples': {
                        'happy_path': {
                            'summary': 'Optimize shopping',
                            'value': {'payload': {'list': ['milk', 'eggs']}},
                        }
                    }
                }
            }
        }
    },
)
async def shopping_optimize(
    _: Annotated[
        SimpleReq,
        Body(
            examples={
                'happy_path': {
                    'summary': 'Optimize shopping',
                    'value': {'payload': {'list': ['milk', 'eggs']}},
                }
            }
        ),
    ],
    subject: str = Depends(require_subject_hs256),
    request: Request = None,
) -> EnqueuedResponse:
    _ = subject
    """Optimize shopping. Requires bearerAuth (JWT)."""
    corr = getattr(request.state, 'correlation_id', None) if request is not None else None
    return await _inline('shopping.optimize', {'correlation_id': corr} if corr else {}, None)
