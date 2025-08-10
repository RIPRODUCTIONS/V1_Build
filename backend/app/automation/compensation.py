from collections.abc import Callable

_COMP: dict[str, Callable[[dict], None]] = {}


def compensator(step: str):
    def deco(fn: Callable[[dict], None]):
        _COMP[step] = fn
        return fn

    return deco


def get_comp(step: str) -> Callable[[dict], None] | None:
    return _COMP.get(step)
