from __future__ import annotations

from temporalio import workflow

from .activities import heartbeat_activity


@workflow.defn
class HelloWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        result = await workflow.execute_activity(
            heartbeat_activity,
            name,
            start_to_close_timeout=workflow.timedelta(seconds=10),
        )
        return f"hello,{result}"
