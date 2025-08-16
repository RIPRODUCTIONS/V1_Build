#!/usr/bin/env python3
"""Universal base class for AI Framework components."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any


class BaseComponent:
    """Universal base class with common attributes and helpers."""

    def __init__(self, name: str = "BaseComponent") -> None:
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.name = name
        self.status = "initialized"
        self.metrics: dict[str, Any] = {}
        self.config: dict[str, Any] = {}
        self.errors: list[str] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def report_error(self, error: str) -> dict[str, Any]:
        """Universal error reporting."""
        self.logger.error(f"Error in {self.name}: {error}")
        self.errors.append(error)
        return {"error": error, "timestamp": datetime.now().isoformat(), "component": self.name}

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "error_count": len(self.errors),
        }

    def update_metrics(self, metrics: dict[str, Any]) -> None:
        self.metrics.update(metrics)
        self.last_updated = datetime.now()

    def reset(self) -> None:
        self.status = "reset"
        self.errors.clear()
        self.metrics.clear()
        self.last_updated = datetime.now()




