"""
Investigation router for cybersecurity analysis endpoints.

This router provides enterprise-grade investigation capabilities including:
- OSINT (Open Source Intelligence) gathering
- Malware analysis and dynamic testing
- Forensics timeline analysis
- Chain of custody management
- Evidence preservation and integrity
"""

import logging
from typing import Any

from app.investigations.forensics_tools import run_timeline_analysis
from app.investigations.malware_tools import run_malware_analysis
from app.investigations.osint_tools import run_osint_investigation
from app.security.deps import verify_jwt_token
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigations", tags=["investigations"])


# Request/Response Models
class OSINTRequest(BaseModel):
    """OSINT investigation request."""
    subject: dict[str, Any] = Field(..., description="Investigation subject")
    scope: list[str] = Field(default=["basic"], description="Investigation scope")
    priority: str = Field(default="normal", description="Investigation priority")
    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum investigation depth")
    timeout_seconds: int = Field(default=300, ge=60, le=3600, description="Timeout in seconds")


class MalwareRequest(BaseModel):
    """Malware analysis request."""
    sample: str = Field(..., description="Malware sample filename")
    analysis_type: list[str] = Field(default=["dynamic"], description="Analysis types")
    timeout_seconds: int = Field(default=600, ge=60, le=3600, description="Analysis timeout")
    sandbox_config: dict[str, Any] = Field(default_factory=dict, description="Sandbox configuration")
    priority: str = Field(default="normal", description="Analysis priority")


class TimelineRequest(BaseModel):
    """Forensics timeline analysis request."""
    source: str = Field(..., description="Forensics source")
    start_time: str | None = Field(None, description="Analysis start time (ISO format)")
    end_time: str | None = Field(None, description="Analysis end time (ISO format)")
    event_types: list[str] = Field(default=["all"], description="Event types to analyze")
    correlation_rules: dict[str, Any] = Field(default_factory=dict, description="Correlation rules")
    max_events: int = Field(default=10000, ge=100, le=100000, description="Maximum events to process")


class InvestigationResponse(BaseModel):
    """Generic investigation response."""
    status: str = Field(..., description="Investigation status")
    investigation_id: str = Field(..., description="Unique investigation identifier")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Investigation data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Response metadata")


# Health and Status Endpoints
@router.get("/health")
async def investigations_health():
    """Get investigations system health status."""
    try:
        return {
            "status": "healthy",
            "service": "investigations",
            "endpoints": {
                "osint": "/investigations/osint/run",
                "malware": "/investigations/malware/dynamic/run",
                "timeline": "/investigations/forensics/timeline/run"
            },
            "capabilities": [
                "OSINT gathering and analysis",
                "Malware dynamic and static analysis",
                "Forensics timeline analysis",
                "Evidence preservation and chain of custody"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed") from e


@router.get("/status")
async def investigations_status():
    """Get detailed investigations system status."""
    try:
        # Get status from each tool
        from app.investigations.forensics_tools import forensics_analyzer
        from app.investigations.malware_tools import malware_analyzer
        from app.investigations.osint_tools import osint_toolkit

        return {
            "status": "operational",
            "timestamp": "2024-01-01T00:00:00Z",
            "tools": {
                "osint": osint_toolkit.get_health_status(),
                "malware": malware_analyzer.get_health_status(),
                "forensics": forensics_analyzer.get_health_status()
            },
            "system_metrics": {
                "total_investigations": (
                    osint_toolkit.request_count +
                    malware_analyzer.analysis_count +
                    forensics_analyzer.analysis_count
                ),
                "active_analyses": (
                    len(osint_toolkit.request_timestamps) +
                    len(malware_analyzer.active_analyses) +
                    len(forensics_analyzer.active_analyses)
                )
            }
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed") from e


# OSINT Investigation Endpoints
@router.post("/osint/run", response_model=InvestigationResponse)
async def run_osint_investigation_endpoint(
    request: OSINTRequest = Body(...),  # noqa: B008
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """
    Run OSINT investigation.

    This endpoint initiates a comprehensive OSINT investigation with:
    - Input validation and sanitization
    - Rate limiting and API protection
    - Comprehensive error handling
    - Audit logging and chain of custody
    """
    try:
        logger.info(f"OSINT investigation requested by user: {claims.get('sub', 'unknown')}")

        # Run investigation
        result = await run_osint_investigation(request.model_dump())

        return InvestigationResponse(
            status="success",
            investigation_id=result.investigation_id,
            message="OSINT investigation completed successfully",
            data=result.model_dump(),
            metadata={
                "user": claims.get('sub', 'unknown'),
                "scope": request.scope,
                "priority": request.priority
            }
        )

    except ValueError as e:
        logger.warning(f"OSINT investigation validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"OSINT investigation runtime error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"OSINT investigation unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/osint/status/{investigation_id}")
async def get_osint_status(
    investigation_id: str,
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """Get OSINT investigation status."""
    try:
        # For now, return mock status
        # In a real implementation, this would query the actual investigation status
        return {
            "investigation_id": investigation_id,
            "status": "completed",
            "progress": 100,
            "message": "Investigation completed successfully"
        }
    except Exception as e:
        logger.error(f"OSINT status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed") from e


# Malware Analysis Endpoints
@router.post("/malware/dynamic/run", response_model=InvestigationResponse)
async def run_malware_analysis_endpoint(
    request: MalwareRequest = Body(...),  # noqa: B008
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """
    Run malware dynamic analysis.

    This endpoint initiates malware analysis with:
    - Secure sandboxed analysis
    - Dynamic and static analysis
    - Behavioral monitoring
    - Threat scoring and classification
    """
    try:
        logger.info(f"Malware analysis requested by user: {claims.get('sub', 'unknown')}")

        # Run analysis
        result = await run_malware_analysis(request.model_dump())

        return InvestigationResponse(
            status="success",
            investigation_id=result.analysis_id,
            message="Malware analysis completed successfully",
            data=result.model_dump(),
            metadata={
                "user": claims.get('sub', 'unknown'),
                "analysis_type": request.analysis_type,
                "priority": request.priority
            }
        )

    except ValueError as e:
        logger.warning(f"Malware analysis validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"Malware analysis runtime error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Malware analysis unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/malware/status/{analysis_id}")
async def get_malware_status(
    analysis_id: str,
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """Get malware analysis status."""
    try:
        # For now, return mock status
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "progress": 100,
            "message": "Analysis completed successfully"
        }
    except Exception as e:
        logger.error(f"Malware status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed") from e


# Forensics Timeline Endpoints
@router.post("/forensics/timeline/run", response_model=InvestigationResponse)
async def run_timeline_analysis_endpoint(
    request: TimelineRequest = Body(...),  # noqa: B008
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """
    Run forensics timeline analysis.

    This endpoint initiates timeline analysis with:
    - Evidence preservation and integrity
    - Chain of custody management
    - Timeline correlation and analysis
    - Event classification and tagging
    """
    try:
        logger.info(f"Timeline analysis requested by user: {claims.get('sub', 'unknown')}")

        # Run analysis
        result = await run_timeline_analysis(request.model_dump())

        return InvestigationResponse(
            status="success",
            investigation_id=result.analysis_id,
            message="Timeline analysis completed successfully",
            data=result.to_dict(),
            metadata={
                "user": claims.get('sub', 'unknown'),
                "source": request.source,
                "event_types": request.event_types
            }
        )

    except ValueError as e:
        logger.warning(f"Timeline analysis validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"Timeline analysis runtime error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Timeline analysis unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/forensics/timeline/status/{analysis_id}")
async def get_timeline_status(
    analysis_id: str,
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """Get timeline analysis status."""
    try:
        # For now, return mock status
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "progress": 100,
            "message": "Timeline analysis completed successfully"
        }
    except Exception as e:
        logger.error(f"Timeline status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed") from e


# Evidence and Chain of Custody Endpoints
@router.get("/evidence/chain-of-custody")
async def get_chain_of_custody(
    claims: dict = Depends(verify_jwt_token),  # noqa: B008
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return"),  # noqa: B008
    offset: int = Query(0, ge=0, description="Number of entries to skip")  # noqa: B008
):
    """Get chain of custody entries."""
    try:
        from app.investigations.forensics_tools import forensics_analyzer

        custody_entries = forensics_analyzer.get_chain_of_custody()

        # Apply pagination
        start = offset
        end = start + limit
        paginated_entries = custody_entries[start:end]

        return {
            "entries": paginated_entries,
            "total": len(custody_entries),
            "limit": limit,
            "offset": offset,
            "has_more": end < len(custody_entries)
        }

    except Exception as e:
        logger.error(f"Chain of custody retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chain of custody")


@router.get("/evidence/{evidence_id}")
async def get_evidence_details(
    evidence_id: str,
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
):
    """Get evidence details."""
    try:
        from app.investigations.forensics_tools import forensics_analyzer

        evidence = forensics_analyzer.evidence_store.get(evidence_id)

        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")

        return {
            "evidence_id": evidence_id,
            "details": evidence
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evidence retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve evidence")


# Utility Endpoints
@router.get("/capabilities")
async def get_investigation_capabilities():
    """Get available investigation capabilities."""
    return {
        "capabilities": {
            "osint": {
                "description": "Open Source Intelligence gathering and analysis",
                "features": [
                    "Subject investigation",
                    "Social media analysis",
                    "Technical analysis",
                    "Rate limiting and API protection"
                ],
                "endpoints": ["/investigations/osint/run", "/investigations/osint/status/{id}"]
            },
            "malware": {
                "description": "Malware analysis and threat detection",
                "features": [
                    "Dynamic analysis in sandbox",
                    "Static analysis",
                    "Behavioral monitoring",
                    "Threat scoring and classification"
                ],
                "endpoints": ["/investigations/malware/dynamic/run", "/investigations/malware/status/{id}"]
            },
            "forensics": {
                "description": "Forensics timeline analysis and evidence preservation",
                "features": [
                    "Timeline correlation",
                    "Evidence preservation",
                    "Chain of custody management",
                    "Event classification and tagging"
                ],
                "endpoints": ["/investigations/forensics/timeline/run", "/investigations/forensics/timeline/status/{id}"]
            }
        },
        "reliability_features": [
            "Comprehensive error handling and recovery",
            "Input validation and sanitization",
            "Rate limiting and API protection",
            "Audit logging and chain of custody",
            "Fallback mechanisms and resilience",
            "Data integrity verification"
        ]
    }


