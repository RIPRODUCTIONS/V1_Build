"""
FastAPI Application for Autonomous Task Solver System
Production-ready API with authentication, rate limiting, and comprehensive endpoints
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

import jwt
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..autonomous_orchestrator import AutonomousOrchestrator
from ..classification.task_classifier import TaskCategory
from ..discovery.task_detector import DetectedTask, TaskPriority, TaskSource
from ..monitoring.system_monitor import AlertLevel, AlertStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100

# Pydantic models
class TaskCreate(BaseModel):
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    source: TaskSource = Field(..., description="Task source")
    priority: TaskPriority = Field(..., description="Task priority")
    category: TaskCategory | None = Field(None, description="Task category")
    metadata: dict[str, Any] | None = Field(default_factory=dict, description="Additional metadata")

class TaskResponse(BaseModel):
    task_id: str
    title: str
    description: str
    source: str
    priority: str
    category: str | None
    status: str
    created_at: datetime
    metadata: dict[str, Any]

class SystemStatusResponse(BaseModel):
    status: str
    uptime: float
    active_tasks: int
    queue_length: int
    components: dict[str, str]
    health_score: float
    last_heartbeat: datetime

class PerformanceMetricsResponse(BaseModel):
    metric_type: str
    value: float
    task_category: str
    model_used: str
    timestamp: datetime
    trend: str
    confidence: float

class AlertResponse(BaseModel):
    alert_id: str
    level: str
    title: str
    description: str
    status: str
    timestamp: datetime
    source: str

# Global state
orchestrator: AutonomousOrchestrator | None = None
rate_limit_store: dict[str, list[float]] = {}

# Security
security = HTTPBearer()

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def rate_limit(request: Request):
    """Rate limiting middleware"""
    client_ip = request.client.host
    current_time = time.time()

    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []

    # Clean old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )

    rate_limit_store[client_ip].append(current_time)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global orchestrator

    # Startup
    logger.info("🚀 Starting Autonomous Task Solver API...")

    # Initialize orchestrator
    config = {
        "system": {"name": "Autonomous Task Solver API", "environment": "production"},
        "database": {"path": "api_autonomous_system.db"}
    }

    try:
        orchestrator = AutonomousOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start()
        logger.info("✅ API startup completed")
    except Exception as e:
        logger.error(f"❌ API startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Autonomous Task Solver API...")
    if orchestrator:
        await orchestrator.shutdown()
    logger.info("✅ API shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="Autonomous Task Solver System API",
    description="Production-ready API for autonomous task management and execution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        status = await orchestrator.get_system_status()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_status": status.status,
            "uptime": status.uptime,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="System unhealthy")

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get system metrics in Prometheus format"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        # Get performance metrics
        performance_tracker = orchestrator.performance_tracker
        if performance_tracker:
            summary = await performance_tracker.get_performance_summary(hours=1)
        else:
            summary = {"error": "Performance tracker not available"}

        # Get system status
        status = await orchestrator.get_system_status()

        # Format as Prometheus metrics
        metrics = []
        metrics.append("# HELP autonomous_system_status System status")
        metrics.append("# TYPE autonomous_system_status gauge")
        metrics.append(f'autonomous_system_status{{status="{status.status}"}} 1')

        metrics.append("# HELP autonomous_system_uptime_seconds System uptime in seconds")
        metrics.append("# TYPE autonomous_system_uptime_seconds gauge")
        metrics.append(f"autonomous_system_uptime_seconds {status.uptime}")

        metrics.append("# HELP autonomous_system_active_tasks Number of active tasks")
        metrics.append("# TYPE autonomous_system_active_tasks gauge")
        metrics.append(f"autonomous_system_active_tasks {status.active_tasks}")

        metrics.append("# HELP autonomous_system_queue_length Task queue length")
        metrics.append("# TYPE autonomous_system_queue_length gauge")
        metrics.append(f"autonomous_system_queue_length {status.queue_length}")

        return StreamingResponse(
            iter(metrics),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

# Task management endpoints
@app.post("/tasks", response_model=TaskResponse, tags=["Tasks"])
async def create_task(
    task: TaskCreate,
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Create a new task"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        # Create task
        detected_task = DetectedTask(
            task_id=f"api_task_{int(time.time())}",
            title=task.title,
            description=task.description,
            source=task.source,
            priority=task.priority,
            timestamp=datetime.now(),
            metadata=task.metadata
        )

        # Submit to orchestrator
        await orchestrator.submit_task(detected_task)

        return TaskResponse(
            task_id=detected_task.task_id,
            title=detected_task.title,
            description=detected_task.description,
            source=detected_task.source.value,
            priority=detected_task.priority.value,
            category=task.category.value if task.category else None,
            status="submitted",
            created_at=detected_task.timestamp,
            metadata=detected_task.metadata
        )

    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.get("/tasks", response_model=list[TaskResponse], tags=["Tasks"])
async def list_tasks(
    status: str | None = None,
    category: str | None = None,
    limit: int = 100,
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """List tasks with optional filtering"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        # This would integrate with the orchestrator's task storage
        # For now, return mock data
        return []

    except Exception as e:
        logger.error(f"Task listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: str,
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Get task by ID"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        # This would integrate with the orchestrator's task storage
        # For now, return mock data
        raise HTTPException(status_code=404, detail="Task not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")

# System status endpoints
@app.get("/status", response_model=SystemStatusResponse, tags=["System"])
async def get_system_status(
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Get comprehensive system status"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        status = await orchestrator.get_system_status()

        return SystemStatusResponse(
            status=status.status,
            uptime=status.uptime,
            active_tasks=status.active_tasks,
            queue_length=status.queue_length,
            components=status.components,
            health_score=getattr(status, 'health_score', 1.0),
            last_heartbeat=status.last_heartbeat
        )

    except Exception as e:
        logger.error(f"Status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {str(e)}")

@app.get("/components", tags=["System"])
async def get_components_status(
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Get status of individual components"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        status = await orchestrator.get_system_status()
        return status.components

    except Exception as e:
        logger.error(f"Component status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve component status: {str(e)}")

# Performance monitoring endpoints
@app.get("/performance", response_model=list[PerformanceMetricsResponse], tags=["Performance"])
async def get_performance_metrics(
    hours: int = 24,
    category: str | None = None,
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Get performance metrics"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        if not orchestrator.performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")

        summary = await orchestrator.performance_tracker.get_performance_summary(
            task_category=category,
            hours=hours
        )

        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])

        # Convert to response format
        metrics = []
        for metric_type, data in summary.get("metrics_by_type", {}).items():
            metrics.append(PerformanceMetricsResponse(
                metric_type=metric_type,
                value=data.get("average", 0.0),
                task_category=data.get("task_category", "unknown"),
                model_used=data.get("model_used", "unknown"),
                timestamp=datetime.now(),
                trend=data.get("trend", "stable"),
                confidence=data.get("confidence", 0.0)
            ))

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}")

@app.get("/performance/recommendations", tags=["Performance"])
async def get_optimization_recommendations(
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Get optimization recommendations"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        if not orchestrator.performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")

        recommendations = await orchestrator.performance_tracker.get_optimization_recommendations()
        return recommendations

    except Exception as e:
        logger.error(f"Recommendations retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")

# Alerting endpoints
@app.get("/alerts", response_model=list[AlertResponse], tags=["Alerts"])
async def get_alerts(
    level: str | None = None,
    status: str | None = None,
    limit: int = 100,
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Get system alerts"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        if not orchestrator.system_monitor:
            raise HTTPException(status_code=503, detail="System monitor not available")

        alerts = await orchestrator.system_monitor.get_alerts(
            level=AlertLevel(level) if level else None,
            status=AlertStatus(status) if status else None,
            limit=limit
        )

        # Convert to response format
        alert_responses = []
        for alert in alerts:
            alert_responses.append(AlertResponse(
                alert_id=alert["alert_id"],
                level=alert["level"],
                title=alert["title"],
                description=alert["description"],
                status=alert["status"],
                timestamp=datetime.fromisoformat(alert["timestamp"]),
                source=alert["source"]
            ))

        return alert_responses

    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")

@app.post("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    token: dict = Depends(verify_token),
    request: Request = Depends(rate_limit)
):
    """Acknowledge an alert"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")

        if not orchestrator.system_monitor:
            raise HTTPException(status_code=503, detail="System monitor not available")

        success = await orchestrator.system_monitor.acknowledge_alert(alert_id, acknowledged_by)

        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": "Alert acknowledged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert acknowledgement failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time system updates"""
    await websocket.accept()

    try:
        while True:
            # Send system status updates every 5 seconds
            if orchestrator:
                try:
                    status = await orchestrator.get_system_status()
                    await websocket.send_json({
                        "type": "system_status",
                        "data": {
                            "status": status.status,
                            "uptime": status.uptime,
                            "active_tasks": status.active_tasks,
                            "queue_length": status.queue_length,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                except Exception as e:
                    logger.error(f"WebSocket status update failed: {e}")

            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system information"""
    return {
        "name": "Autonomous Task Solver System API",
        "version": "1.0.0",
        "description": "Production-ready API for autonomous task management",
        "docs": "/docs",
        "health": "/health",
        "status": "/status"
    }

if __name__ == "__main__":
    import os
    if os.environ.get("RUN_AUTONOMOUS_API") == "1":
        uvicorn.run(
            "fastapi_app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    else:
        print("autonomous_system/api/fastapi_app.py entrypoint disabled. Set RUN_AUTONOMOUS_API=1 to run.")
