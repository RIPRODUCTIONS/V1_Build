
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
    print("\n1. Basic Wireless Monitoring:")
    asyncio.run(example_wireless_monitoring())
    
    print("\n2. Rogue AP Detection:")
    asyncio.run(example_rogue_ap_detection())
    
    print("\n3. Device Analysis:")
    asyncio.run(example_device_analysis())
    
    print("\n✅ Examples completed!")
