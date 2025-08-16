from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import psutil

from core.db import TaskRecord, get_session


class MetricsCollector:
    def __init__(self) -> None:
        # Constants to replace magic numbers
        self.CACHE_TTL_SECONDS = 30
        self.CPU_INTERVAL = 0.2
        self.METRICS_HISTORY_HOURS = 1
        self.BYTES_TO_GB = 1024 ** 3

        self.start_time = time.time()
        self._metrics_cache: dict[str, Any] = {}
        self._last_update = 0.0

    async def collect_system_metrics(self) -> dict[str, Any]:
        now = time.time()
        if now - self._last_update < self.CACHE_TTL_SECONDS and self._metrics_cache:
            return self._metrics_cache

        # System
        cpu_percent = psutil.cpu_percent(interval=self.CPU_INTERVAL)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # DB task stats
        with get_session() as session:
            total = session.query(TaskRecord).count()
            pending = session.query(TaskRecord).filter(TaskRecord.status == "pending").count()
            running = session.query(TaskRecord).filter(TaskRecord.status == "running").count()
            completed = session.query(TaskRecord).filter(TaskRecord.status == "completed").count()
            failed = session.query(TaskRecord).filter(TaskRecord.status == "failed").count()
            one_hour_ago = datetime.now(UTC) - timedelta(hours=self.METRICS_HISTORY_HOURS)
            recent_completed = (
                session.query(TaskRecord)
                .filter(TaskRecord.completed_at.isnot(None))
                .filter(TaskRecord.completed_at >= one_hour_ago)
                .filter(TaskRecord.status == "completed")
                .count()
            )
            recent_failed = (
                session.query(TaskRecord)
                .filter(TaskRecord.completed_at.isnot(None))
                .filter(TaskRecord.completed_at >= one_hour_ago)
                .filter(TaskRecord.status == "failed")
                .count()
            )

        success_rate = 100.0
        denom = recent_completed + recent_failed
        if denom > 0:
            success_rate = (recent_completed / denom) * 100.0

        metrics = {
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime_seconds": now - self.start_time,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_used_gb": round(mem.used / self.BYTES_TO_GB, 3),
                "memory_available_gb": round(mem.available / self.BYTES_TO_GB, 3),
                "memory_percent": mem.percent,
                "disk_used_gb": round(disk.used / self.BYTES_TO_GB, 3),
                "disk_free_gb": round(disk.free / self.BYTES_TO_GB, 3),
                "disk_percent": round((disk.used / disk.total) * 100.0, 2),
            },
            "tasks": {
                "total": total,
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "success_rate_1h": round(success_rate, 2),
            },
        }

        self._metrics_cache = metrics
        self._last_update = now
        return metrics



