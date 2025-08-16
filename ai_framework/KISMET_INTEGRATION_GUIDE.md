
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
