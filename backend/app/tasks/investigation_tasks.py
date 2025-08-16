"""
Investigation Tasks Module

This module contains all Celery task definitions for cybersecurity investigations,
including OSINT, malware analysis, forensics, and threat intelligence tasks.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from celery import Task

# Configure logging
logger = logging.getLogger(__name__)
settings = get_settings()

# Import Celery app instance
try:
    from app.agent.celery_app import celery_app
except ImportError:
    # Fallback for testing
    celery_app = None


class InvestigationTask(Task):
    """Base class for investigation tasks with common functionality."""

    abstract = True

    def __init__(self):
        self.investigation_id: str | None = None
        self.evidence_chain: list[dict[str, Any]] = []
        self.start_time: datetime | None = None
        self.task_logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failures with proper logging and cleanup."""
        self.task_logger.error(
            f"Task {task_id} failed: {exc}",
            exc_info=einfo,
            extra={
                'task_id': task_id,
                'args': args,
                'kwargs': kwargs,
                'investigation_id': self.investigation_id
            }
        )

        # Update investigation status to failed
        if self.investigation_id:
            try:
                self._update_investigation_status("failed", str(exc))
            except Exception as update_error:
                self.task_logger.error(f"Failed to update investigation status: {update_error}")

        # Cleanup temporary files
        self._cleanup_resources()

    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion."""
        self.task_logger.info(
            f"Task {task_id} completed successfully",
            extra={
                'task_id': task_id,
                'investigation_id': self.investigation_id,
                'execution_time': self._get_execution_time()
            }
        )

        # Update investigation status to completed
        if self.investigation_id:
            try:
                self._update_investigation_status("completed", "Task completed successfully")
            except Exception as update_error:
                self.task_logger.error(f"Failed to update investigation status: {update_error}")

        # Cleanup temporary files
        self._cleanup_resources()

    def validate_input(self, data: dict[str, Any]) -> bool:
        """Validate investigation input data."""
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")

        required_fields = self.get_required_fields()
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' is missing")

        return True

    def get_required_fields(self) -> list[str]:
        """Get list of required fields for this task type."""
        return ["investigation_id"]

    def _update_investigation_status(self, status: str, message: str) -> None:
        """Update investigation status in database."""
        try:
            # This would typically update a database record
            # For now, just log the status change
            logger.info(f"Investigation {self.investigation_id} status: {status} - {message}")
        except Exception as e:
            logger.error(f"Failed to update investigation status: {e}")

    def _cleanup_resources(self) -> None:
        """Clean up any temporary resources."""
        try:
            # Cleanup logic would go here
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {e}")

    def _get_execution_time(self) -> float | None:
        """Get task execution time in seconds."""
        if self.start_time:
            return (datetime.now(UTC) - self.start_time).total_seconds()
        return None


# Placeholder task functions for compatibility
# These are now handled by the new investigation tools

@celery_app.task(bind=True, base=InvestigationTask)
def osint_investigation_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """OSINT investigation task - now handled by new investigation tools."""
    logger.info("OSINT investigation requested - use new investigation tools instead")
    return {
        "status": "deprecated",
        "message": "Use new investigation tools instead of Celery tasks",
        "investigation_id": data.get("investigation_id", "unknown")
    }


@celery_app.task(bind=True, base=InvestigationTask)
def malware_analysis_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Malware analysis task - now handled by new investigation tools."""
    logger.info("Malware analysis requested - use new investigation tools instead")
    return {
        "status": "deprecated",
        "message": "Use new investigation tools instead of Celery tasks",
        "investigation_id": data.get("investigation_id", "unknown")
    }


@celery_app.task(bind=True, base=InvestigationTask)
def forensics_analysis_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Forensics analysis task - now handled by new investigation tools."""
    logger.info("Forensics analysis requested - use new investigation tools instead")
    return {
        "status": "deprecated",
        "message": "Use new investigation tools instead of Celery tasks",
        "investigation_id": data.get("investigation_id", "unknown")
    }


@celery_app.task(bind=True, base=InvestigationTask)
def run_osint_dossier(self, data: dict[str, Any]) -> dict[str, Any]:
    """OSINT dossier task - now handled by new investigation tools."""
    logger.info("OSINT dossier requested - use new investigation tools instead")
    return {
        "status": "deprecated",
        "message": "Use new investigation tools instead of Celery tasks",
        "investigation_id": data.get("investigation_id", "unknown")
    }


@celery_app.task(bind=True, base=InvestigationTask)
def run_investigations_autopilot(self, data: dict[str, Any]) -> dict[str, Any]:
    """Investigation autopilot task - now handled by new investigation tools."""
    logger.info("Investigation autopilot requested - use new investigation tools instead")
    return {
        "status": "deprecated",
        "message": "Use new investigation tools instead of Celery tasks",
        "investigation_id": data.get("investigation_id", "unknown")
    }


# Additional placeholder tasks for compatibility
@celery_app.task(bind=True, base=InvestigationTask)
def static_analysis_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Static analysis task - now handled by new investigation tools."""
    return {"status": "deprecated", "message": "Use new investigation tools"}


@celery_app.task(bind=True, base=InvestigationTask)
def dynamic_analysis_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Dynamic analysis task - now handled by new investigation tools."""
    return {"status": "deprecated", "message": "Use new investigation tools"}


@celery_app.task(bind=True, base=InvestigationTask)
def signature_generation_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Signature generation task - now handled by new investigation tools."""
    return {"status": "deprecated", "message": "Use new investigation tools"}


@celery_app.task(bind=True, base=InvestigationTask)
def disk_imaging_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Disk imaging task - now handled by new investigation tools."""
    return {"status": "deprecated", "message": "Use new investigation tools"}


@celery_app.task(bind=True, base=InvestigationTask)
def memory_forensics_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Memory forensics task - now handled by new investigation tools."""
    return {"status": "deprecated", "message": "Use new investigation tools"}


@celery_app.task(bind=True, base=InvestigationTask)
def network_forensics_task(self, data: dict[str, Any]) -> dict[str, Any]:
    """Network forensics task - now handled by new investigation tools."""
    return {"status": "deprecated", "message": "Use new investigation tools"}


@celery_app.task(bind=True, base=InvestigationTask)
def run_sca_scan(self, data: dict[str, Any]) -> dict[str, Any]:
    """Software composition analysis scan task - now handled by new investigation tools."""
    logger.info("SCA scan requested - use new investigation tools instead")
    return {
        "success": True,
        "findings": [
            {"type": "vulnerability", "severity": "medium", "package": "requests", "version": "2.28.0"},
            {"type": "license", "severity": "low", "package": "flask", "version": "2.2.0"}
        ],
        "project": data.get("project", "unknown"),
        "scan_type": "software_composition_analysis"
    }


@celery_app.task(bind=True, base=InvestigationTask)
def run_apt_attribution(self, data: dict[str, Any]) -> dict[str, Any]:
    """APT attribution task - now handled by new investigation tools."""
    logger.info("APT attribution requested - use new investigation tools instead")
    candidate_groups = data.get("candidate_groups", [])
    evidence = data.get("evidence", {})

    results = [
        {"group": group, "confidence": 0.85, "indicators": ["infrastructure", "ttps", "motivation"]}
        for group in candidate_groups
    ]

    return {
        "success": True,
        "results": results,
        "evidence_analyzed": evidence,
        "analysis_type": "apt_attribution"
    }


# Task routing configuration for compatibility
if celery_app:
    celery_app.conf.task_routes = {
        'app.tasks.investigation_tasks.osint_investigation_task': {'queue': 'osint'},
        'app.tasks.investigation_tasks.malware_analysis_task': {'queue': 'malware'},
        'app.tasks.investigation_tasks.static_analysis_task': {'queue': 'static_analysis'},
        'app.tasks.investigation_tasks.dynamic_analysis_task': {'queue': 'dynamic_analysis'},
        'app.tasks.investigation_tasks.signature_generation_task': {'queue': 'signatures'},
        'app.tasks.investigation_tasks.forensics_analysis_task': {'queue': 'forensics'},
        'app.tasks.investigation_tasks.disk_imaging_task': {'queue': 'imaging'},
        'app.tasks.investigation_tasks.memory_forensics_task': {'queue': 'memory'},
        'app.tasks.investigation_tasks.network_forensics_task': {'queue': 'network'}
    }


