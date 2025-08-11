from __future__ import annotations

from datetime import UTC, datetime

from prefect import flow, task


@task
def beat() -> str:
    msg = f"heartbeat @ {datetime.now(UTC).isoformat()}"
    print(msg)
    return msg


@flow
def heartbeat_flow() -> str:
    return beat()


if __name__ == "__main__":
    heartbeat_flow()
