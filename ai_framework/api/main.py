"""
AI Framework FastAPI Backend

This is the main FastAPI application that provides:
- REST API endpoints for all AI agents
- WebSocket connections for real-time updates
- Dashboard data endpoints
- Agent management and control
"""

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from agents.base import Task, TaskPriority
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.agent_orchestrator import AgentOrchestrator
from core.master_dashboard import MasterDashboard
from core.model_router import TaskComplexity, TaskRequirements, TaskType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Framework Backend",
    description="Backend API for the AI Framework with 50+ specialized agents",
    version="1.0.0"
)

# Add CORS middleware
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8001,http://127.0.0.1:8001,http://localhost:8000,http://127.0.0.1:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend
try:
    app.mount("/frontend", StaticFiles(directory=str((__file__).rsplit("/", 2)[0] + "/frontend"), html=True), name="frontend")
except Exception:
    # Fallback: mount from known relative path when running from project root
    app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Global variables
# dashboard: MasterDashboard = None
# orchestrator: AgentOrchestrator = None
active_connections: list[WebSocket] = []

# AppState class to replace global variables
class AppState:
    def __init__(self):
        self.dashboard: MasterDashboard = None
        self.orchestrator: AgentOrchestrator = None

    def update_dashboard(self, new_dashboard: MasterDashboard):
        self.dashboard = new_dashboard

    def update_orchestrator(self, new_orchestrator: AgentOrchestrator):
        self.orchestrator = new_orchestrator

# Use instance instead of global
app_state = AppState()

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    # global dashboard, orchestrator

    logger.info("Starting AI Framework Backend...")

    # Initialize orchestrator
    orchestrator = AgentOrchestrator()

    # Initialize master dashboard
    dashboard = MasterDashboard(orchestrator)

    # Update app state instead of global variables
    app_state.update_orchestrator(orchestrator)
    app_state.update_dashboard(dashboard)

    logger.info(f"AI Framework initialized with {len(dashboard.agent_registry)} agents")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # global dashboard

    if app_state.dashboard:
        await app_state.dashboard.shutdown_all_agents()
        logger.info("AI Framework shutdown complete")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                # Remove failed connection
                self.active_connections.remove(connection)

manager = ConnectionManager()

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            if app_state.dashboard:
                overview = await app_state.dashboard.get_dashboard_overview()
                await websocket.send_text(json.dumps(overview))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Dashboard endpoints
@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    return await app_state.dashboard.get_dashboard_overview()

@app.get("/api/dashboard/departments")
async def get_departments():
    """Get all departments and their status."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    overview = await app_state.dashboard.get_dashboard_overview()
    return overview.get("departments", {})

@app.get("/api/dashboard/agents")
async def get_all_agents():
    """Get status of all agents."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    agents = {}
    for agent_id, agent in app_state.dashboard.agent_registry.items():
        agents[agent_id] = await agent.get_status_report()

    return agents

@app.get("/api/dashboard/agent/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get status of a specific agent."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    agent_status = await app_state.dashboard.get_agent_status(agent_id)
    if not agent_status:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent_status

@app.get("/api/dashboard/department/{department}")
async def get_department_status(department: str):
    """Get status of a specific department."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    dept_status = await app_state.dashboard.get_department_status(department)
    if not dept_status:
        raise HTTPException(status_code=404, detail="Department not found")

    return dept_status

# Agent control endpoints
@app.post("/api/agents/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """Restart a specific agent."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    # Find the agent
    if agent_id not in app_state.dashboard.agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = app_state.dashboard.agent_registry[agent_id]
    try:
        # Reinitialize the agent
        agent._initialize_agent()
        return {"status": "success", "message": f"Agent {agent_id} restarted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart agent: {str(e)}") from e

@app.post("/api/departments/{department}/restart")
async def restart_department(department: str):
    """Restart all agents in a department."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    result = await app_state.dashboard.restart_agents(department)
    return result

@app.post("/api/agents/restart-all")
async def restart_all_agents():
    """Restart all agents."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    result = await app_state.dashboard.restart_agents()
    return result

# Emergency protocol endpoints
@app.post("/api/emergency/{protocol}")
async def execute_emergency_protocol(protocol: str):
    """Execute emergency protocol."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    result = await app_state.dashboard.execute_emergency_protocol(protocol)
    return result

# System control endpoints
@app.post("/api/system/shutdown")
async def shutdown_system():
    """Shutdown all agents."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    result = await app_state.dashboard.shutdown_all_agents()
    return result

@app.get("/api/system/health")
async def get_system_health():
    """Get overall system health."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    return {
        "status": "healthy",
        "dashboard_status": app_state.dashboard.status.value,
        "system_health": app_state.dashboard.system_health.value,
        "total_agents": app_state.dashboard.metrics.total_agents,
        "active_agents": app_state.dashboard.metrics.active_agents,
        "timestamp": datetime.now(UTC).isoformat()
    }

# Agent task execution endpoints
@app.post("/api/agents/{agent_id}/execute")
async def execute_agent_task(agent_id: str, task_data: dict[str, Any]):
    """Execute a task on a specific agent."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    if agent_id not in app_state.dashboard.agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = app_state.dashboard.agent_registry[agent_id]

    # Create task object

    task = Task(
        task_id=task_data.get("task_id", f"task_{datetime.now().timestamp()}"),
        task_type=task_data.get("task_type", "general"),
        description=task_data.get("description", "Task execution"),
        priority=TaskPriority(task_data.get("priority", "normal")),
        requirements=TaskRequirements(
            task_type=TaskType.COORDINATOR,
            complexity=TaskComplexity.SIMPLE
        ),
        metadata=task_data.get("metadata", {})
    )

    try:
        result = await agent.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}") from e

# Analytics and metrics endpoints
@app.get("/api/analytics/performance")
async def get_performance_analytics():
    """Get performance analytics across all agents."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    # Collect performance data from all agents
    performance_data = {}
    for agent_id, agent in app_state.dashboard.agent_registry.items():
        if hasattr(agent, 'performance_metrics'):
            performance_data[agent_id] = {
                "name": agent.config.name,
                "department": agent.config.department.value,
                "status": agent.status.value,
                "metrics": agent.performance_metrics.__dict__
            }

    return {
        "total_agents": len(performance_data),
        "performance_summary": performance_data,
        "timestamp": datetime.now(UTC).isoformat()
    }

@app.get("/api/analytics/departments")
async def get_department_analytics():
    """Get department-level analytics."""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    overview = await app_state.dashboard.get_dashboard_overview()
    return overview.get("departments", {})

# Root endpoint
@app.get("/")
async def root():
    """Redirect to the frontend dashboard."""
    return RedirectResponse(url="/frontend/")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}

if __name__ == "__main__":
    import os

    import uvicorn
    # Only run directly if explicitly enabled (to avoid duplicate servers)
    if os.environ.get("RUN_API_MAIN") == "1":
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        print("ai_framework/api/main.py entrypoint is disabled by default. Set RUN_API_MAIN=1 to run.")
