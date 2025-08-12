import sys
import traceback
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix='/debug', tags=['debug'])


@router.get('/threads')
def threads() -> dict[str, Any]:
    """Get live thread stack traces for debugging startup hangs."""
    frames = sys._current_frames()
    dump = {}
    for tid, frame in frames.items():
        dump[str(tid)] = ''.join(traceback.format_stack(frame))
    return {'thread_count': len(frames), 'stacks': dump}


@router.get('/health')
def debug_health() -> dict[str, str]:
    """Debug health endpoint that always responds."""
    return {'status': 'debug_ok', 'message': 'Debug router is working'}


@router.get('/info')
def debug_info() -> dict[str, Any]:
    """Get basic system info for debugging."""
    import os
    import platform

    return {
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'cwd': os.getcwd(),
        'env': {
            'SKIP_DB_INIT': os.getenv('SKIP_DB_INIT'),
            'ALLOW_START_WITHOUT_REDIS': os.getenv('ALLOW_START_WITHOUT_REDIS'),
            'CELERY_EAGER': os.getenv('CELERY_EAGER'),
        },
    }
