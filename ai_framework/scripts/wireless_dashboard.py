
"""
Wireless Security Dashboard Integration
Add wireless security monitoring to the main dashboard
"""

from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json

# Add to your dashboard routes

@app.get("/dashboard/wireless", response_class=HTMLResponse)
async def wireless_dashboard(request: Request):
    """Wireless security dashboard page"""
    
    # Get wireless agent status
    wireless_agent = None
    for agent in agent_orchestrator.agents.values():
        if isinstance(agent, WirelessSecurityAgent):
            wireless_agent = agent
            break
    
    context = {
        "request": request,
        "page_title": "Wireless Security",
        "agent_available": wireless_agent is not None,
        "monitoring_active": wireless_agent.monitoring_active if wireless_agent else False
    }
    
    if wireless_agent:
        try:
            status = await wireless_agent.get_status()
            context.update(status)
        except Exception as e:
            context["error"] = str(e)
    
    return templates.TemplateResponse("wireless/dashboard.html", context)

@app.get("/api/wireless/status")
async def wireless_status():
    """Get wireless security status"""
    
    wireless_agent = None
    for agent in agent_orchestrator.agents.values():
        if isinstance(agent, WirelessSecurityAgent):
            wireless_agent = agent
            break
    
    if not wireless_agent:
        return {"error": "Wireless agent not available"}
    
    return await wireless_agent.get_status()

@app.get("/api/wireless/dashboard-data")
async def wireless_dashboard_data():
    """Get data for wireless security dashboard"""
    
    wireless_agent = None
    for agent in agent_orchestrator.agents.values():
        if isinstance(agent, WirelessSecurityAgent):
            wireless_agent = agent
            break
    
    if not wireless_agent or not wireless_agent.kismet_adapter:
        return {"error": "Wireless monitoring not available"}
    
    try:
        devices = await wireless_agent.kismet_adapter.get_detected_devices()
        alerts = await wireless_agent.kismet_adapter.get_alerts()
        summary = await wireless_agent.kismet_adapter.get_network_summary()
        
        return {
            "devices": [asdict(device) for device in devices[-10:]],  # Last 10 devices
            "alerts": [asdict(alert) for alert in alerts[-10:]],      # Last 10 alerts
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}
