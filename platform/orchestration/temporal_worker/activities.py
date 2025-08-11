from __future__ import annotations

from temporalio import activity


@activity.defn
async def heartbeat_activity(name: str) -> str:
    activity.heartbeat({"seen": name})
    return name



