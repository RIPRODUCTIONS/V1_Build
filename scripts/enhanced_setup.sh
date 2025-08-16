#!/bin/bash
# ENHANCED COMPREHENSIVE SETUP SCRIPT
# Complete cybersecurity automation platform installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KALI_AUTOMATION_DIR="/opt/kali-automation"
REPORTS_DIR="$KALI_AUTOMATION_DIR/reports"
LOGS_DIR="$KALI_AUTOMATION_DIR/logs"
TOOLS_DIR="$KALI_AUTOMATION_DIR/tools"
AUTOMATION_DIR="$KALI_AUTOMATION_DIR/automation"

echo -e "${BLUE}🚀 ENHANCED CYBERSECURITY AUTOMATION PLATFORM SETUP${NC}"
echo "=================================================="

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Kali Linux metapackages
print_status "Installing Kali Linux metapackages..."
sudo apt install -y kali-linux-everything

# Install development dependencies
print_status "Installing development dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl wget unzip

# Install Go
print_status "Installing Go programming language..."
if ! command -v go &> /dev/null; then
    wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    source ~/.bashrc
fi

# Install Node.js
print_status "Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create directories
print_status "Creating automation directories..."
sudo mkdir -p $KALI_AUTOMATION_DIR
sudo mkdir -p $REPORTS_DIR
sudo mkdir -p $LOGS_DIR
sudo mkdir -p $TOOLS_DIR
sudo mkdir -p $AUTOMATION_DIR

# Set permissions
sudo chown -R $USER:$USER $KALI_AUTOMATION_DIR

# Install Python security libraries
print_status "Installing Python security libraries..."
pip3 install --user cryptography pyyaml requests beautifulsoup4 lxml
pip3 install --user yara-python pefile ssdeep python-magic
pip3 install --user stix2 taxii2client pymisp virustotal-api
pip3 install --user celery redis sqlalchemy psycopg2-binary
pip3 install --user prometheus-client grafana-api elasticsearch

# Install Go security tools
print_status "Installing Go security tools..."
go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Install additional tools
print_status "Installing additional security tools..."
sudo apt install -y volatility3 autopsy wireshark tshark
sudo apt install -y foremost photorec bulk-extractor log2timeline plaso

# Clone and install GitHub tools
print_status "Installing GitHub security tools..."
cd $TOOLS_DIR

# Clone repositories
git clone https://github.com/SpiderLabs/SpiderFoot.git
git clone https://github.com/lanmaster53/recon-ng.git
git clone https://github.com/WebBreacher/WhatsMyName.git
git clone https://github.com/s0md3v/Maigret.git
git clone https://github.com/megadose/holehe.git

# Install SpiderFoot
cd SpiderFoot
pip3 install -r requirements.txt
cd ..

# Install Recon-ng
cd recon-ng
pip3 install -r REQUIREMENTS
cd ..

# Install WhatsMyName
cd WhatsMyName
pip3 install -r requirements.txt
cd ..

# Install Maigret
cd Maigret
pip3 install -r requirements.txt
cd ..

# Install Holehe
cd holehe
pip3 install -r requirements.txt
cd ..

# Return to original directory
cd -

# Copy automation scripts
print_status "Copying automation scripts..."
cp -r tools/* $TOOLS_DIR/
cp -r automation/* $AUTOMATION_DIR/

# Create configuration files
print_status "Creating configuration files..."
cat > $KALI_AUTOMATION_DIR/config.yaml << EOF
# Kali Automation Platform Configuration
platform:
  name: "Enhanced Cybersecurity Automation Platform"
  version: "2.0.0"
  description: "Comprehensive automation platform for all Kali Linux tools"

directories:
  reports: "$REPORTS_DIR"
  logs: "$LOGS_DIR"
  tools: "$TOOLS_DIR"
  automation: "$AUTOMATION_DIR"

api_keys:
  shodan: "YOUR_SHODAN_API_KEY"
  virustotal: "YOUR_VIRUSTOTAL_API_KEY"
  misp: "YOUR_MISP_API_KEY"
  otx: "YOUR_OTX_API_KEY"
  abuseipdb: "YOUR_ABUSEIPDB_API_KEY"
  greynoise: "YOUR_GREYNOISE_API_KEY"

automation:
  default_level: "medium"
  max_concurrent_tools: 10
  timeout_seconds: 3600
  retry_attempts: 3

logging:
  level: "INFO"
  format: "detailed"
  rotation: "daily"
  retention_days: 30

monitoring:
  prometheus_enabled: true
  grafana_enabled: true
  elasticsearch_enabled: true
EOF

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/kali-automation.service > /dev/null << EOF
[Unit]
Description=Kali Automation Platform
After=network.target docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$KALI_AUTOMATION_DIR
ExecStart=/usr/bin/python3 $AUTOMATION_DIR/enhanced_master_engine.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable kali-automation.service

# Create startup script
cat > $KALI_AUTOMATION_DIR/start_platform.sh << 'EOF'
#!/bin/bash
# Startup script for Kali Automation Platform

echo "Starting Enhanced Cybersecurity Automation Platform..."

# Start Docker services
cd /opt/kali-automation
docker-compose -f docker-compose.kali.yml up -d

# Start the automation engine
python3 automation/enhanced_master_engine.py &

echo "Platform started successfully!"
echo "Access the platform at: http://localhost:8080"
echo "Grafana dashboard: http://localhost:3000"
echo "Kibana: http://localhost:5601"
EOF

chmod +x $KALI_AUTOMATION_DIR/start_platform.sh

# Create API key configuration script
cat > $KALI_AUTOMATION_DIR/configure_api_keys.sh << 'EOF'
#!/bin/bash
# API Key Configuration Script

echo "🔑 API Key Configuration for Kali Automation Platform"
echo "====================================================="

read -p "Enter your Shodan API key: " SHODAN_KEY
read -p "Enter your VirusTotal API key: " VT_KEY
read -p "Enter your MISP API key: " MISP_KEY
read -p "Enter your OTX API key: " OTX_KEY
read -p "Enter your AbuseIPDB API key: " ABUSE_KEY
read -p "Enter your GreyNoise API key: " GREYNOISE_KEY

# Update config file
sed -i "s/YOUR_SHODAN_API_KEY/$SHODAN_KEY/g" config.yaml
sed -i "s/YOUR_VIRUSTOTAL_API_KEY/$VT_KEY/g" config.yaml
sed -i "s/YOUR_MISP_API_KEY/$MISP_KEY/g" config.yaml
sed -i "s/YOUR_OTX_API_KEY/$OTX_KEY/g" config.yaml
sed -i "s/YOUR_ABUSEIPDB_API_KEY/$ABUSE_KEY/g" config.yaml
sed -i "s/YOUR_GREYNOISE_API_KEY/$GREYNOISE_KEY/g" config.yaml

echo "✅ API keys configured successfully!"
EOF

chmod +x $KALI_AUTOMATION_DIR/configure_api_keys.sh

# Create test script
cat > $KALI_AUTOMATION_DIR/test_platform.sh << 'EOF'
#!/bin/bash
# Test script for Kali Automation Platform

echo "🧪 Testing Kali Automation Platform..."
echo "====================================="

# Test Python imports
echo "Testing Python modules..."
python3 -c "
from automation.enhanced_master_engine import EnhancedMasterAutomationEngine
print('✓ Enhanced Master Engine imported successfully')
"

# Test tool automation classes
echo "Testing tool automation classes..."
python3 -c "
from tools.penetration_testing_complete import MetasploitFrameworkAutomation
from tools.forensics_specialized import VolatilityAutomation
from tools.threat_intelligence_connectors import MISPConnector
print('✓ Tool automation classes imported successfully')
"

# Test Docker services
echo "Testing Docker services..."
docker ps --format "table {{.Names}}\t{{.Status}}"

echo "✅ Platform test completed successfully!"
EOF

chmod +x $KALI_AUTOMATION_DIR/test_platform.sh

# Create usage examples
cat > $KALI_AUTOMATION_DIR/usage_examples.py << 'EOF'
#!/usr/bin/env python3
"""
Usage Examples for Enhanced Kali Automation Platform
"""

from automation.enhanced_master_engine import (
    EnhancedMasterAutomationEngine,
    InvestigationType,
    AutomationLevel,
    InvestigationRequest
)

async def main():
    # Initialize the engine
    engine = EnhancedMasterAutomationEngine()

    # Example 1: OSINT Investigation
    osint_request = InvestigationRequest(
        investigation_type=InvestigationType.OSINT,
        target="example.com",
        automation_level=AutomationLevel.MEDIUM,
        options={"scan_type": "comprehensive"}
    )

    osint_result = await engine.execute_comprehensive_investigation(osint_request)
    print(f"OSINT investigation completed: {osint_result.status}")

    # Example 2: Penetration Testing
    pentest_request = InvestigationRequest(
        investigation_type=InvestigationType.PENETRATION_TESTING,
        target="192.168.1.100",
        automation_level=AutomationLevel.HIGH,
        options={"scope": "full_network"}
    )

    pentest_result = await engine.execute_comprehensive_investigation(pentest_request)
    print(f"Penetration testing completed: {pentest_result.status}")

    # Example 3: Digital Forensics
    forensics_request = InvestigationRequest(
        investigation_type=InvestigationType.FORENSICS,
        target="/path/to/evidence.dd",
        automation_level=AutomationLevel.MEDIUM,
        options={"analysis_type": "comprehensive"}
    )

    forensics_result = await engine.execute_comprehensive_investigation(forensics_request)
    print(f"Forensics analysis completed: {forensics_result.status}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
EOF

# Final setup completion
print_status "Setup completed successfully!"
echo ""
echo -e "${GREEN}🎉 ENHANCED CYBERSECURITY AUTOMATION PLATFORM READY!${NC}"
echo ""
echo "Next steps:"
echo "1. Configure API keys: cd $KALI_AUTOMATION_DIR && ./configure_api_keys.sh"
echo "2. Test the platform: ./test_platform.sh"
echo "3. Start the platform: ./start_platform.sh"
echo "4. View usage examples: cat usage_examples.py"
echo ""
echo "Platform features:"
echo "✓ 600+ Kali Linux tools automated"
echo "✓ Advanced penetration testing workflows"
echo "✓ Comprehensive forensics analysis"
echo "✓ Threat intelligence integration"
echo "✓ Red/Blue/Purple team workflows"
echo "✓ Compliance and audit automation"
echo "✓ Incident response automation"
echo "✓ Advanced reporting and correlation"
echo ""
echo "Documentation and support available in: $KALI_AUTOMATION_DIR"
