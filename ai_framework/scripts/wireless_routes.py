
# Add these routes to your FastAPI server (server.py)

from agents.wireless_security_agent import WirelessSecurityAgent
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import time

wireless_router = APIRouter(prefix="/api/wireless", tags=["wireless"])

@wireless_router.post("/start-monitoring")
async def start_wireless_monitoring(interface: str = "wlan0", duration: int = 3600):
    """Start wireless network monitoring"""
    try:
        # Get wireless agent from orchestrator
        wireless_agent = None
        for agent in agent_orchestrator.agents.values():
            if isinstance(agent, WirelessSecurityAgent):
                wireless_agent = agent
                break
        
        if not wireless_agent:
            return JSONResponse(
                status_code=404,
                content={"error": "Wireless security agent not found"}
            )
        
        # Create monitoring task
        task = Task(
            task_id=f"wireless_monitor_{int(time.time())}",
            task_type="start_monitoring",
            description="Start wireless network monitoring",
            requirements={"interface": interface, "duration": duration}
        )
        
        result = await wireless_agent.execute_task(task)
        return JSONResponse(content=result.__dict__)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@wireless_router.get("/scan")
async def scan_networks():
    """Scan for nearby wireless networks"""
    try:
        wireless_agent = None
        for agent in agent_orchestrator.agents.values():
            if isinstance(agent, WirelessSecurityAgent):
                wireless_agent = agent
                break
        
        if not wireless_agent:
            return JSONResponse(
                status_code=404,
                content={"error": "Wireless security agent not found"}
            )
        
        task = Task(
            task_id=f"wireless_scan_{int(time.time())}",
            task_type="scan_networks",
            description="Scan wireless networks"
        )
        
        result = await wireless_agent.execute_task(task)
        return JSONResponse(content=result.__dict__)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@wireless_router.get("/threats")
async def detect_threats():
    """Detect wireless security threats"""
    try:
        wireless_agent = None
        for agent in agent_orchestrator.agents.values():
            if isinstance(agent, WirelessSecurityAgent):
                wireless_agent = agent
                break
        
        if not wireless_agent:
            return JSONResponse(
                status_code=404,
                content={"error": "Wireless security agent not found"}
            )
        
        task = Task(
            task_id=f"threat_detection_{int(time.time())}",
            task_type="detect_threats",
            description="Detect wireless threats"
        )
        
        result = await wireless_agent.execute_task(task)
        return JSONResponse(content=result.__dict__)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@wireless_router.get("/report/{report_type}")
async def generate_report(report_type: str):
    """Generate wireless security report"""
    try:
        wireless_agent = None
        for agent in agent_orchestrator.agents.values():
            if isinstance(agent, WirelessSecurityAgent):
                wireless_agent = agent
                break
        
        if not wireless_agent:
            return JSONResponse(
                status_code=404,
                content={"error": "Wireless security agent not found"}
            )
        
        task = Task(
            task_id=f"wireless_report_{int(time.time())}",
            task_type="generate_report",
            description=f"Generate {report_type} report",
            requirements={"report_type": report_type}
        )
        
        result = await wireless_agent.execute_task(task)
        return JSONResponse(content=result.__dict__)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@wireless_router.post("/baseline")
async def establish_baseline():
    """Establish wireless network baseline"""
    try:
        wireless_agent = None
        for agent in agent_orchestrator.agents.values():
            if isinstance(agent, WirelessSecurityAgent):
                wireless_agent = agent
                break
        
        if not wireless_agent:
            return JSONResponse(
                status_code=404,
                content={"error": "Wireless security agent not found"}
            )
        
        task = Task(
            task_id=f"wireless_baseline_{int(time.time())}",
            task_type="baseline_network",
            description="Establish network baseline"
        )
        
        result = await wireless_agent.execute_task(task)
        return JSONResponse(content=result.__dict__)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Add the wireless router to your main app
app.include_router(wireless_router)
