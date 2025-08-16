# integrate_kismet.py
"""
Integration script to add Kismet wireless security capabilities
to the existing AI Framework
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the AI framework to the path
sys.path.append(str(Path(__file__).parent))


class KismetIntegrationManager:
    """Manages Kismet integration with the AI Framework"""

    def __init__(self, framework_path: str = "."):
        self.framework_path = Path(framework_path)
        self.logger = logging.getLogger(__name__)

    async def integrate_kismet(self) -> bool:
        """Integrate Kismet capabilities into the AI Framework"""
        try:
            self.logger.info("Starting Kismet integration...")

            # Check if framework exists
            if not self.framework_path.exists():
                raise FileNotFoundError(f"AI Framework not found at {self.framework_path}")

            # Create integration directories
            await self._create_integration_structure()

            # Copy integration files
            await self._copy_integration_files()

            # Update framework configuration
            await self._update_framework_config()

            # Register wireless security agent
            await self._register_wireless_agent()

            # Add wireless routes to server
            await self._add_wireless_routes()

            # Create example tasks
            await self._create_example_tasks()

            self.logger.info("Kismet integration completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Integration failed: {e}")
            return False

    async def _create_integration_structure(self) -> None:
        """Create necessary directory structure"""
        directories = [
            "integrations",
            "agents/wireless",
            "configs/wireless",
            "logs/wireless",
            "data/wireless/baselines",
            "data/wireless/reports",
            "web/static/wireless",
            "web/templates/wireless"
        ]

        for dir_path in directories:
            full_path = self.framework_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {full_path}")

    async def _copy_integration_files(self) -> None:
        """Copy integration files to framework"""
        # This would copy the files we created in the artifacts
        # For now, we'll create the essential files directly

        # Create __init__.py files
        init_files = [
            "integrations/__init__.py",
            "agents/wireless/__init__.py"
        ]

        for init_file in init_files:
            init_path = self.framework_path / init_file
            if not init_path.exists():
                init_path.write_text("# Wireless security integration\n")

    async def _update_framework_config(self) -> None:
        """Update framework configuration for wireless security"""
        config_content = """
# Wireless Security Configuration
wireless_security:
  enabled: true
  default_interface: "wlan0"

  kismet:
    host: "localhost"
    port: 2501
    api_port: 2501

  monitoring:
    auto_start: false
    channel_hop: true
    channel_hop_speed: 3

  alerts:
    enable_notifications: true
    alert_threshold: "MEDIUM"
    email_alerts: false

  security:
    rogue_ap_detection: true
    weak_encryption_alerts: true
    baseline_monitoring: true

  reporting:
    auto_generate: true
    report_interval: 3600  # 1 hour
    keep_reports: 168      # 1 week
"""

        config_path = self.framework_path / "configs" / "wireless" / "wireless_config.yaml"
        config_path.write_text(config_content)

        self.logger.info(f"Created wireless config: {config_path}")

    async def _register_wireless_agent(self) -> None:
        """Register wireless security agent with orchestrator"""
        registration_script = '''
# Add this to your agent registration in main.py or server.py

from agents.wireless_security_agent import WirelessSecurityAgent

# Register wireless security agent
wireless_agent = WirelessSecurityAgent()
await wireless_agent.initialize(interface="wlan0")  # Use your wireless interface
agent_orchestrator.register_agent(wireless_agent)

print("Wireless Security Agent registered successfully")
'''

        registration_path = self.framework_path / "scripts" / "register_wireless_agent.py"
        registration_path.parent.mkdir(exist_ok=True)
        registration_path.write_text(registration_script)

        self.logger.info("Created agent registration script")

    async def _add_wireless_routes(self) -> None:
        """Add wireless security routes to the web server"""
        routes_code = '''
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
'''

        routes_path = self.framework_path / "scripts" / "wireless_routes.py"
        routes_path.write_text(routes_code)

        self.logger.info("Created wireless routes script")

    async def _create_example_tasks(self) -> None:
        """Create example wireless security tasks"""
        examples_code = '''
"""
Example Wireless Security Tasks
These examples show how to use the wireless security capabilities
"""

import asyncio
from agents.wireless_security_agent import WirelessSecurityAgent
from agents.base import Task

async def example_wireless_monitoring():
    """Example: Start wireless monitoring and threat detection"""

    # Initialize the wireless agent
    agent = WirelessSecurityAgent()

    # Initialize with your wireless interface
    if await agent.initialize(interface="wlan0"):
        print("✅ Wireless Security Agent initialized")

        # Task 1: Start monitoring
        monitor_task = Task(
            task_id="monitor_001",
            task_type="start_monitoring",
            description="Monitor wireless networks for 10 minutes",
            requirements={"duration": 600}  # 10 minutes
        )

        result = await agent.execute_task(monitor_task)
        print(f"📡 Monitoring started: {result.success}")

        # Wait a bit for some data to be collected
        await asyncio.sleep(30)

        # Task 2: Scan for networks
        scan_task = Task(
            task_id="scan_001",
            task_type="scan_networks",
            description="Scan for nearby networks"
        )

        result = await agent.execute_task(scan_task)
        print(f"🔍 Network scan completed: {result.data}")

        # Task 3: Detect threats
        threat_task = Task(
            task_id="threat_001",
            task_type="detect_threats",
            description="Analyze for security threats"
        )

        result = await agent.execute_task(threat_task)
        print(f"⚠️  Threat analysis: {result.data}")

        # Task 4: Generate report
        report_task = Task(
            task_id="report_001",
            task_type="generate_report",
            description="Generate security summary",
            requirements={"report_type": "summary"}
        )

        result = await agent.execute_task(report_task)
        print(f"📋 Security report generated")

        # Task 5: Establish baseline
        baseline_task = Task(
            task_id="baseline_001",
            task_type="baseline_network",
            description="Establish network baseline"
        )

        result = await agent.execute_task(baseline_task)
        print(f"📊 Network baseline established: {result.success}")

        # Stop monitoring
        stop_task = Task(
            task_id="stop_001",
            task_type="stop_monitoring",
            description="Stop wireless monitoring"
        )

        result = await agent.execute_task(stop_task)
        print(f"🛑 Monitoring stopped: {result.success}")

    else:
        print("❌ Failed to initialize wireless agent")

async def example_rogue_ap_detection():
    """Example: Hunt for rogue access points"""

    agent = WirelessSecurityAgent()

    if await agent.initialize():
        # Start monitoring
        await agent.execute_task(Task(
            task_id="monitor_rogue",
            task_type="start_monitoring",
            requirements={"duration": 300}  # 5 minutes
        ))

        # Wait for data collection
        await asyncio.sleep(60)

        # Hunt for rogue APs
        rogue_task = Task(
            task_id="rogue_hunt_001",
            task_type="rogue_ap_hunt",
            description="Hunt for rogue access points"
        )

        result = await agent.execute_task(rogue_task)

        if result.success:
            rogue_aps = result.data.get("rogue_aps", [])
            suspicious_aps = result.data.get("suspicious_aps", [])

            print(f"🚨 Found {len(rogue_aps)} rogue access points")
            print(f"⚠️  Found {len(suspicious_aps)} suspicious access points")

            for ap in rogue_aps:
                print(f"  ROGUE: {ap['ssid']} ({ap['mac_address']})")

            for ap in suspicious_aps:
                print(f"  SUSPICIOUS: {ap['ssid']} ({ap['mac_address']})")

        # Stop monitoring
        await agent.execute_task(Task(
            task_id="stop_rogue",
            task_type="stop_monitoring"
        ))

async def example_device_analysis():
    """Example: Analyze specific wireless device"""

    agent = WirelessSecurityAgent()

    if await agent.initialize():
        # Start monitoring to detect devices
        await agent.execute_task(Task(
            task_id="monitor_device",
            task_type="start_monitoring",
            requirements={"duration": 180}  # 3 minutes
        ))

        await asyncio.sleep(60)  # Wait for device detection

        # Get detected devices first
        scan_result = await agent.execute_task(Task(
            task_id="scan_device",
            task_type="scan_networks"
        ))

        if scan_result.success and scan_result.data.get("devices_found", 0) > 0:
            # Analyze the first detected device (you'd normally specify a specific MAC)
            analyze_task = Task(
                task_id="analyze_001",
                task_type="analyze_device",
                description="Analyze specific device",
                requirements={"device_mac": "aa:bb:cc:dd:ee:ff"}  # Replace with actual MAC
            )

            result = await agent.execute_task(analyze_task)

            if result.success:
                device_info = result.data.get("device", {})
                analysis = result.data.get("analysis", {})

                print(f"📱 Device Analysis:")
                print(f"   MAC: {device_info.get('mac_address')}")
                print(f"   Type: {device_info.get('device_type')}")
                print(f"   Manufacturer: {device_info.get('manufacturer')}")
                print(f"   Risk Score: {analysis.get('risk_score', 0)}/100")
                print(f"   Security Assessment: {analysis.get('security_assessment', {})}")

        # Stop monitoring
        await agent.execute_task(Task(
            task_id="stop_device",
            task_type="stop_monitoring"
        ))

# Main execution
if __name__ == "__main__":
    print("🔒 Wireless Security Examples")
    print("=" * 40)

    # Run basic monitoring example
    print("\\n1. Basic Wireless Monitoring:")
    asyncio.run(example_wireless_monitoring())

    print("\\n2. Rogue AP Detection:")
    asyncio.run(example_rogue_ap_detection())

    print("\\n3. Device Analysis:")
    asyncio.run(example_device_analysis())

    print("\\n✅ Examples completed!")
'''

        examples_path = self.framework_path / "examples" / "wireless_security_examples.py"
        examples_path.parent.mkdir(exist_ok=True)
        examples_path.write_text(examples_code)

        self.logger.info("Created wireless security examples")

    async def _create_dashboard_integration(self) -> None:
        """Create dashboard integration for wireless security"""
        dashboard_code = '''
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
'''

        dashboard_path = self.framework_path / "scripts" / "wireless_dashboard.py"
        dashboard_path.write_text(dashboard_code)

        # Create basic HTML template
        template_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wireless Security Dashboard</title>
    <style>
        .dashboard-container { padding: 20px; }
        .status-card { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .alert-high { border-left: 4px solid #dc3545; }
        .alert-medium { border-left: 4px solid #ffc107; }
        .alert-low { border-left: 4px solid #28a745; }
        .device-list { max-height: 300px; overflow-y: auto; }
        .monitoring-active { color: #28a745; }
        .monitoring-inactive { color: #dc3545; }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>🔒 Wireless Security Dashboard</h1>

        {% if agent_available %}
            <div class="status-card">
                <h3>Monitoring Status:
                    <span class="{% if monitoring_active %}monitoring-active{% else %}monitoring-inactive{% endif %}">
                        {{ "Active" if monitoring_active else "Inactive" }}
                    </span>
                </h3>

                <div id="wireless-data">
                    <p>Loading wireless data...</p>
                </div>
            </div>

            <div class="status-card">
                <h3>Controls</h3>
                <button onclick="startMonitoring()">Start Monitoring</button>
                <button onclick="stopMonitoring()">Stop Monitoring</button>
                <button onclick="scanNetworks()">Scan Networks</button>
                <button onclick="detectThreats()">Detect Threats</button>
                <button onclick="generateReport()">Generate Report</button>
            </div>

            <div class="status-card">
                <h3>Recent Devices</h3>
                <div id="device-list" class="device-list">
                    <p>No devices detected</p>
                </div>
            </div>

            <div class="status-card">
                <h3>Security Alerts</h3>
                <div id="alert-list">
                    <p>No alerts</p>
                </div>
            </div>

        {% else %}
            <div class="status-card">
                <h3>❌ Wireless Security Agent Not Available</h3>
                <p>The wireless security agent is not initialized. Please check the installation.</p>
            </div>
        {% endif %}
    </div>

    <script>
        // Auto-refresh dashboard data
        async function refreshData() {
            try {
                const response = await fetch('/api/wireless/dashboard-data');
                const data = await response.json();

                if (data.error) {
                    document.getElementById('wireless-data').innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

                // Update summary
                const summary = data.summary || {};
                document.getElementById('wireless-data').innerHTML = `
                    <p><strong>Total Devices:</strong> ${summary.total_devices || 0}</p>
                    <p><strong>Access Points:</strong> ${summary.access_points || 0}</p>
                    <p><strong>Clients:</strong> ${summary.clients || 0}</p>
                    <p><strong>Total Alerts:</strong> ${summary.total_alerts || 0}</p>
                    <p><strong>High Severity Alerts:</strong> ${summary.high_severity_alerts || 0}</p>
                `;

                // Update device list
                const devices = data.devices || [];
                const deviceHtml = devices.map(device => `
                    <div>
                        <strong>${device.ssid || 'Unknown'}</strong> (${device.mac_address})<br>
                        Type: ${device.device_type}, Manufacturer: ${device.manufacturer}<br>
                        Signal: ${device.signal_strength} dBm, Encryption: ${device.encryption}
                    </div>
                `).join('<hr>');

                document.getElementById('device-list').innerHTML = deviceHtml || '<p>No devices detected</p>';

                // Update alerts
                const alerts = data.alerts || [];
                const alertHtml = alerts.map(alert => `
                    <div class="alert-${alert.severity.toLowerCase()}">
                        <strong>${alert.alert_type}</strong>: ${alert.description}<br>
                        <small>${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');

                document.getElementById('alert-list').innerHTML = alertHtml || '<p>No alerts</p>';

            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }

        // Control functions
        async function startMonitoring() {
            const response = await fetch('/api/wireless/start-monitoring', { method: 'POST' });
            const result = await response.json();
            alert(result.success ? 'Monitoring started' : `Error: ${result.error}`);
            refreshData();
        }

        async function stopMonitoring() {
            const response = await fetch('/api/wireless/stop-monitoring', { method: 'POST' });
            const result = await response.json();
            alert(result.success ? 'Monitoring stopped' : `Error: ${result.error}`);
            refreshData();
        }

        async function scanNetworks() {
            const response = await fetch('/api/wireless/scan');
            const result = await response.json();
            alert(`Scan completed. Found ${result.data?.devices_found || 0} devices`);
            refreshData();
        }

        async function detectThreats() {
            const response = await fetch('/api/wireless/threats');
            const result = await response.json();
            const threatCount = (result.data?.high_threats?.length || 0) + (result.data?.critical_threats?.length || 0);
            alert(`Threat detection completed. Found ${threatCount} high/critical threats`);
            refreshData();
        }

        async function generateReport() {
            const response = await fetch('/api/wireless/report/summary');
            const result = await response.json();
            alert(result.success ? 'Report generated successfully' : `Error: ${result.error}`);
        }

        // Initial load and auto-refresh
        refreshData();
        setInterval(refreshData, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
'''

        template_path = self.framework_path / "web" / "templates" / "wireless" / "dashboard.html"
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(template_html)

        self.logger.info("Created wireless dashboard template")

    async def create_installation_guide(self) -> None:
        """Create complete installation and usage guide"""
        guide_content = '''
# 🔒 Kismet Wireless Security Integration Guide

## Installation Complete!

Your AI Framework now includes comprehensive wireless security monitoring capabilities powered by Kismet.

## 📁 Files Created

### Core Integration Files:
- `integrations/kismet_adapter.py` - Kismet integration adapter
- `agents/wireless_security_agent.py` - Wireless security AI agent
- `configs/wireless/wireless_config.yaml` - Configuration settings

### Scripts and Examples:
- `scripts/register_wireless_agent.py` - Agent registration
- `scripts/wireless_routes.py` - API routes
- `scripts/wireless_dashboard.py` - Dashboard integration
- `examples/wireless_security_examples.py` - Usage examples

### Web Interface:
- `web/templates/wireless/dashboard.html` - Dashboard UI

## 🚀 Quick Start

### 1. Install Kismet (if not already done)
```bash
# Run the installation script
chmod +x setup_kismet.sh
./setup_kismet.sh
```

### 2. Register the Wireless Agent
Add to your main AI framework initialization:

```python
from agents.wireless_security_agent import WirelessSecurityAgent

# Initialize and register wireless agent
wireless_agent = WirelessSecurityAgent()
await wireless_agent.initialize(interface="wlan0")  # Use your interface
agent_orchestrator.register_agent(wireless_agent)
```

### 3. Add Routes to Your Server
Include the wireless routes in your FastAPI app:

```python
# Add to server.py
from scripts.wireless_routes import wireless_router
app.include_router(wireless_router)
```

### 4. Access the Dashboard
Visit: `http://localhost:8000/dashboard/wireless`

## 🔧 API Endpoints

### Start Monitoring
```bash
curl -X POST "http://localhost:8000/api/wireless/start-monitoring?interface=wlan0&duration=3600"
```

### Scan Networks
```bash
curl "http://localhost:8000/api/wireless/scan"
```

### Detect Threats
```bash
curl "http://localhost:8000/api/wireless/threats"
```

### Generate Reports
```bash
curl "http://localhost:8000/api/wireless/report/summary"
curl "http://localhost:8000/api/wireless/report/detailed"
curl "http://localhost:8000/api/wireless/report/threat_analysis"
```

### Establish Baseline
```bash
curl -X POST "http://localhost:8000/api/wireless/baseline"
```

## 🛡️ Security Features

### Threat Detection
- **Rogue Access Point Detection**: Identifies unauthorized APs
- **Evil Twin Detection**: Detects duplicate SSIDs with different characteristics
- **Weak Encryption Alerts**: Flags WEP/Open networks
- **Hidden Network Discovery**: Finds non-broadcasting SSIDs
- **Deauthentication Attack Detection**: Identifies DoS attacks
- **Beacon Flooding Detection**: Detects beacon spam attacks

### Device Analysis
- **Device Fingerprinting**: Identifies device types and manufacturers
- **Signal Strength Monitoring**: Tracks device proximity
- **Behavior Analysis**: Monitors device patterns over time
- **Baseline Comparison**: Compares against known good state

### Automated Monitoring
- **Continuous Scanning**: Real-time network monitoring
- **Alert Generation**: Automated threat notifications
- **Report Generation**: Scheduled security reports
- **Baseline Management**: Automatic baseline updates

## 📊 Dashboard Features

The wireless security dashboard provides:

- **Real-time Monitoring Status**: Active/inactive monitoring state
- **Device Discovery**: List of detected wireless devices
- **Security Alerts**: Color-coded threat notifications
- **Network Statistics**: Access points, clients, and device counts
- **Interactive Controls**: Start/stop monitoring, scan, and threat detection

## 🔧 Configuration

Edit `configs/wireless/wireless_config.yaml` to customize:

```yaml
wireless_security:
  kismet:
    interface: "wlan0"          # Your wireless interface
    host: "localhost"           # Kismet server host
    port: 2501                  # Kismet server port

  monitoring:
    auto_start: false           # Auto-start monitoring
    channel_hop: true           # Enable channel hopping
    channel_hop_speed: 3        # Channels per second

  alerts:
    enable_notifications: true  # Enable alert notifications
    alert_threshold: "MEDIUM"   # Minimum alert severity

  security:
    rogue_ap_detection: true    # Enable rogue AP detection
    weak_encryption_alerts: true # Alert on weak encryption
    baseline_monitoring: true   # Enable baseline monitoring
```

## 🏃‍♂️ Running Examples

```bash
cd ai_framework
python examples/wireless_security_examples.py
```

This will demonstrate:
1. Basic wireless monitoring
2. Rogue AP detection
3. Device analysis
4. Report generation

## ⚠️ Important Notes

### Legal Compliance
- Only monitor networks you own or have permission to test
- Comply with local laws regarding wireless monitoring
- Use for security assessment and authorized testing only

### Technical Requirements
- Wireless adapter capable of monitor mode
- Root/sudo access for interface management
- Kismet installed and configured
- Python 3.8+ with required dependencies

### Performance Considerations
- Monitor mode may disrupt wireless connectivity
- Continuous monitoring can generate large log files
- Consider network impact when scanning

## 🔍 Troubleshooting

### Common Issues

1. **Interface not found**
   ```bash
   iwconfig  # Check available interfaces
   ```

2. **Permission denied**
   ```bash
   sudo usermod -aG kismet $USER
   # Log out and back in
   ```

3. **Monitor mode failed**
   ```bash
   sudo systemctl stop NetworkManager
   # Or use nmcli to unmanage interface
   ```

4. **Kismet not starting**
   ```bash
   # Check logs
   tail -f /var/log/syslog | grep kismet
   ```

### Logs and Debugging
- AI Framework logs: `logs/wireless/`
- Kismet logs: `/tmp/kismet_logs/`
- System logs: `/var/log/syslog`

## 🚀 Next Steps

1. **Integrate with Notifications**: Add email/Slack alerts for threats
2. **GPS Integration**: Add location tracking for mobile monitoring
3. **ML Enhancement**: Improve threat detection with machine learning
4. **Report Automation**: Schedule automated security reports
5. **API Integration**: Connect with other security tools

## 📚 Additional Resources

- [Kismet Documentation](https://www.kismetwireless.net/docs/)
- [Wireless Security Best Practices](https://www.sans.org/white-papers/1321/)
- [AI Framework Documentation](./README.md)

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Kismet logs for errors
3. Verify wireless interface compatibility
4. Ensure proper permissions and group membership

---

**🎉 Congratulations! Your AI Framework now has enterprise-grade wireless security capabilities!**
'''

        guide_path = Path.cwd() / "KISMET_INTEGRATION_GUIDE.md"
        guide_path.write_text(guide_content)

        self.logger.info(f"Created installation guide: {guide_path}")


async def main():
    """Main integration function"""
    print("🔒 Kismet Wireless Security Integration")
    print("=" * 50)

    # Initialize integration manager
    manager = KismetIntegrationManager()

    # Run integration
    if await manager.integrate_kismet():
        # Create dashboard integration
        await manager._create_dashboard_integration()

        # Create installation guide
        await manager.create_installation_guide()

        print("\n✅ Integration completed successfully!")
        print("\nNext steps:")
        print("1. Run the Kismet installation script: ./setup_kismet.sh")
        print("2. Register the wireless agent in your main.py")
        print("3. Add wireless routes to your server.py")
        print("4. Access the dashboard at: http://localhost:8000/dashboard/wireless")
        print("5. Read the guide: ./KISMET_INTEGRATION_GUIDE.md")

    else:
        print("\n❌ Integration failed!")
        print("Check the logs for more information.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
