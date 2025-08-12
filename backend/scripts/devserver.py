#!/usr/bin/env python3
"""
Explicit dev server runner to bypass shell wrappers and isolate startup issues
"""

import os
import sys

import uvicorn


def main():
    # Fix Python path - add backend directory
    backend_dir = os.path.abspath('.')
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    print(f'📁 Added {backend_dir} to Python path')

    # Set environment variables for safe startup
    os.environ.setdefault('SKIP_DB_INIT', 'true')
    os.environ.setdefault('ALLOW_START_WITHOUT_REDIS', 'true')
    os.environ.setdefault('CELERY_EAGER', 'true')

    print('🚀 Starting dev server with explicit configuration...')
    print(f'SKIP_DB_INIT: {os.environ.get("SKIP_DB_INIT")}')
    print(f'ALLOW_START_WITHOUT_REDIS: {os.environ.get("ALLOW_START_WITHOUT_REDIS")}')
    print(f'CELERY_EAGER: {os.environ.get("CELERY_EAGER")}')

    uvicorn.run(
        'app.main:create_app',
        factory=True,
        host='127.0.0.1',
        port=8000,
        log_level='debug',
        lifespan='off',
        loop='asyncio',
        http='h11',
        workers=1,
    )


if __name__ == '__main__':
    main()
