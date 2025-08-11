from __future__ import annotations

from datetime import datetime
from prefect import flow, task


@task
def beat() -> str:
    msg = f"heartbeat @ {datetime.utcnow().isoformat()}Z"
    print(msg)
    return msg


@flow
def heartbeat_flow() -> str:
    return beat()


if __name__ == "__main__":
    heartbeat_flow()


