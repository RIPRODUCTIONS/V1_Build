from typing import Any


async def noop(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, '_noop': True}
