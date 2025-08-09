from __future__ import annotations

from collections.abc import Callable

JobFunc = Callable[[], int]
_registry: dict[str, JobFunc] = {}


def register(name: str):
    def decorator(func: JobFunc) -> JobFunc:
        _registry[name] = func
        return func

    return decorator


def list_jobs() -> list[str]:
    return sorted(_registry.keys())


def get_job(name: str) -> JobFunc | None:
    return _registry.get(name)
