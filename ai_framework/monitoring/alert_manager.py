from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from core.db import TaskRecord, get_session


class AlertManager:
    def __init__(self) -> None:
        # Constants to replace magic numbers
        self.MIN_TASKS_FOR_ALERT = 10
        self.ALERT_COOLDOWN_HOURS = 1
        self.MONITORING_INTERVAL = 60  # seconds

        self.alert_thresholds = {
            "high_failure_rate": 20.0,  # percent
        }
        self._cooldown: dict[str, datetime] = {}
        self.last_check_time: datetime | None = None

    async def start_monitoring(self) -> None:
        while True:
            try:
                self.last_check_time = datetime.now(UTC)
                await self._check_failure_rate()
            except Exception:
                pass
            await asyncio.sleep(self.MONITORING_INTERVAL)

    async def _check_failure_rate(self) -> None:
        with get_session() as session:
            one_hour_ago = datetime.now(UTC) - timedelta(hours=self.ALERT_COOLDOWN_HOURS)
            total_recent = (
                session.query(TaskRecord)
                .filter(TaskRecord.created_at >= one_hour_ago)
                .count()
            )
            failed_recent = (
                session.query(TaskRecord)
                .filter(TaskRecord.created_at >= one_hour_ago)
                .filter(TaskRecord.status == "failed")
                .count()
            )
        if total_recent < self.MIN_TASKS_FOR_ALERT:
            return
        rate = (failed_recent / total_recent) * 100.0
        if rate > self.alert_thresholds["high_failure_rate"]:
            key = f"failrate_{datetime.now(UTC).strftime('%Y%m%d%H')}"
            if key not in self._cooldown:
                self._cooldown[key] = datetime.now(UTC)
                print(f"\n\u26a0\ufe0f ALERT: High failure rate {rate:.1f}% ({failed_recent}/{total_recent})\n")


