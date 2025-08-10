from collections.abc import Callable

_SKILLS: dict[str, Callable] = {}
_DAGS: dict[str, list[str]] = {}


def skill(name: str):
    def deco(fn: Callable):
        _SKILLS[name] = fn
        return fn

    return deco


def register_dag(intent: str, steps: list[str]) -> None:
    _DAGS[intent] = steps


def get_skill(name: str) -> Callable:
    return _SKILLS[name]


def get_dag(intent: str) -> list[str]:
    return _DAGS[intent]
