from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Any, Optional
from contextlib import contextmanager

from app.models import AgentRun


class RunStateLogger:
    """Structured logging for automation run states with correlation IDs."""

    def __init__(self, logger_name: str = "run_state"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        # Ensure we have a handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_run_event(
        self,
        run_id: str,
        event_type: str,
        status: str,
        correlation_id: Optional[str] = None,
        intent: Optional[str] = None,
        department: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        level: str = "info",
    ) -> None:
        """Log a run state event with structured data."""

        log_data = {
            "run_id": run_id,
            "event_type": event_type,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_id": correlation_id,
            "intent": intent,
            "department": department,
            "metadata": metadata or {},
        }

        log_message = f"RUN_STATE: {json.dumps(log_data)}"

        if level == "debug":
            self.logger.debug(log_message)
        elif level == "warn":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)

    def log_run_started(
        self,
        run_id: str,
        intent: str,
        correlation_id: Optional[str] = None,
        department: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log when a run starts."""
        self.log_run_event(
            run_id=run_id,
            event_type="run.started",
            status="started",
            correlation_id=correlation_id,
            intent=intent,
            department=department,
            metadata=metadata,
        )

    def log_run_completed(
        self,
        run_id: str,
        intent: str,
        correlation_id: Optional[str] = None,
        department: Optional[str] = None,
        result: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log when a run completes successfully."""
        metadata = {"result": result} if result else {}
        self.log_run_event(
            run_id=run_id,
            event_type="run.completed",
            status="completed",
            correlation_id=correlation_id,
            intent=intent,
            department=department,
            metadata=metadata,
        )

    def log_run_failed(
        self,
        run_id: str,
        intent: str,
        error: str,
        correlation_id: Optional[str] = None,
        department: Optional[str] = None,
        error_details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log when a run fails."""
        metadata = {"error": error, "error_details": error_details or {}}
        self.log_run_event(
            run_id=run_id,
            event_type="run.failed",
            status="failed",
            correlation_id=correlation_id,
            intent=intent,
            department=department,
            metadata=metadata,
            level="error",
        )

    def log_run_status_update(
        self,
        run_id: str,
        status: str,
        correlation_id: Optional[str] = None,
        intent: Optional[str] = None,
        department: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a run status update."""
        self.log_run_event(
            run_id=run_id,
            event_type="run.status_updated",
            status=status,
            correlation_id=correlation_id,
            intent=intent,
            department=department,
            metadata=metadata,
        )

    @contextmanager
    def run_context(
        self,
        run_id: str,
        intent: str,
        correlation_id: Optional[str] = None,
        department: Optional[str] = None,
    ):
        """Context manager for logging run lifecycle."""
        try:
            self.log_run_started(
                run_id=run_id, intent=intent, correlation_id=correlation_id, department=department
            )
            yield
            self.log_run_completed(
                run_id=run_id, intent=intent, correlation_id=correlation_id, department=department
            )
        except Exception as e:
            self.log_run_failed(
                run_id=run_id,
                intent=intent,
                error=str(e),
                correlation_id=correlation_id,
                department=department,
            )
            raise


# Global instance
run_logger = RunStateLogger()
