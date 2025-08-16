#!/bin/bash

# COMPLETE KALI LINUX AUTOMATION PLATFORM SETUP
# This script installs and configures the entire Kali Linux automation platform

set -e

echo "🚀 Starting Kali Linux Automation Platform Setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Kali Linux metapackages
echo "🔧 Installing Kali Linux metapackages..."
sudo apt-get install -y \
    kali-linux-everything \
    kali-tools-top10 \
    kali-tools-information-gathering \
    kali-tools-vulnerability \
    kali-tools-web \
    kali-tools-database \
    kali-tools-passwords \
    kali-tools-wireless \
    kali-tools-reverse-engineering \
    kali-tools-exploitation \
    kali-tools-social-engineering \
    kali-tools-sniffing-spoofing \
    kali-tools-post-exploitation \
    kali-tools-forensics \
    kali-tools-reporting \
    kali-tools-gpu \
    kali-tools-hardware \
    kali-tools-crypto-stego \
    kali-tools-fuzzing \
    kali-tools-802-11 \
    kali-tools-bluetooth \
    kali-tools-rfid \
    kali-tools-sdr \
    kali-tools-voip \
    kali-tools-windows-resources

# Install development dependencies
echo "🐍 Installing Python and development tools..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

# Install Go
echo "🐹 Installing Go..."
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Install Node.js
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python security libraries
echo "🔐 Installing Python security libraries..."
pip3 install \
    python-nmap \
    scapy \
    impacket \
    pwntools \
    requests \
    beautifulsoup4 \
    selenium \
    sqlmap \
    paramiko \
    cryptography \
    pillow \
    matplotlib \
    numpy \
    pandas \
    celery \
    redis \
    sqlalchemy \
    yara-python \
    pefile \
    ssdeep \
    tlsh

# Install Go security tools
echo "🔧 Installing Go security tools..."
go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install github.com/projectdiscovery/notify/cmd/notify@latest
go install github.com/projectdiscovery/chaos-client/cmd/chaos@latest

# Install Node.js security tools
echo "📦 Installing Node.js security tools..."
npm install -g \
    wappalyzer \
    retire \
    snyk \
    auditjs

# Clone and install GitHub tools
echo "📚 Installing GitHub security tools..."
cd /opt
sudo git clone https://github.com/sqlmapproject/sqlmap.git
sudo git clone https://github.com/rapid7/metasploit-framework.git
sudo git clone https://github.com/SpiderLabs/Responder.git
sudo git clone https://github.com/PowerShellMafia/PowerSploit.git
sudo git clone https://github.com/BloodHoundAD/BloodHound.git
sudo git clone https://github.com/gentilkiwi/mimikatz.git

# Install specialized tools
echo "🎯 Installing specialized security tools..."
sudo apt-get install -y \
    maltego \
    burpsuite \
    owasp-zap \
    ghidra \
    ida-free \
    volatility3 \
    autopsy \
    sleuthkit

# Create automation directories
echo "📁 Creating automation directories..."
sudo mkdir -p /kali-automation/{tools,scripts,results,logs,configs}
sudo mkdir -p /kali-automation/tools/{information_gathering,vulnerability_assessment,web_application,database_assessment,password_attacks,wireless_attacks,reverse_engineering,exploitation,sniffing_spoofing,post_exploitation,forensics,reporting,social_engineering}

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R $USER:$USER /kali-automation
chmod -R 755 /kali-automation

# Copy automation framework
echo "📋 Copying automation framework..."
cp -r kali_automation/* /kali-automation/
cp -r tools/* /kali-automation/tools/

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/kali-automation.service > /dev/null <<EOF
[Unit]
Description=Kali Linux Automation Platform
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/kali-automation
ExecStart=/usr/bin/python3 /kali-automation/kali_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable kali-automation
sudo systemctl start kali-automation

# Create startup script
echo "📜 Creating startup script..."
tee /kali-automation/start.sh > /dev/null <<EOF
#!/bin/bash
cd /kali-automation
python3 kali_orchestrator.py
EOF

chmod +x /kali-automation/start.sh

# Create API key configuration script
echo "🔑 Creating API key configuration script..."
tee /kali-automation/configure_api_keys.sh > /dev/null <<EOF
#!/bin/bash
echo "🔑 Configuring API keys for Kali automation tools..."
echo "Please enter your API keys when prompted:"

read -p "Shodan API Key: " shodan_key
read -p "VirusTotal API Key: " virustotal_key
read -p "HaveIBeenPwned API Key: " hibp_key
read -p "Censys API Key: " censys_key

# Save to configuration file
cat > /kali-automation/configs/api_keys.conf <<CONFIG
SHODAN_API_KEY=$shodan_key
VIRUSTOTAL_API_KEY=$virustotal_key
HIBP_API_KEY=$hibp_key
CENSYS_API_KEY=$censys_key
CONFIG

echo "✅ API keys configured successfully!"
EOF

chmod +x /kali-automation/configure_api_keys.sh

# Create test script
echo "🧪 Creating test script..."
tee /kali-automation/test_platform.sh > /dev/null <<EOF
#!/bin/bash
echo "🧪 Testing Kali automation platform..."

# Test basic functionality
echo "Testing Nmap automation..."
python3 -c "from tools.information_gathering import NmapAutomation; print('✅ Nmap automation imported successfully')"

echo "Testing Masscan automation..."
python3 -c "from tools.information_gathering import MasscanAutomation; print('✅ Masscan automation imported successfully')"

echo "Testing orchestrator..."
python3 -c "from kali_automation.kali_orchestrator import KaliToolsOrchestrator; print('✅ Orchestrator imported successfully')"

echo "🎉 All tests passed! Platform is ready."
EOF

chmod +x /kali-automation/test_platform.sh

# Create usage examples
echo "📖 Creating usage examples..."
tee /kali-automation/USAGE_EXAMPLES.md > /dev/null <<EOF
# Kali Automation Platform Usage Examples

## Basic Usage
\`\`\`bash
cd /kali-automation
python3 kali_orchestrator.py
\`\`\`

## Run Specific Tool
\`\`\`bash
python3 -c "
from tools.information_gathering import NmapAutomation
nmap = NmapAutomation()
result = await nmap.execute_automated('192.168.1.1', {}, 'high')
print(result)
"
\`\`\`

## Full Penetration Test
\`\`\`bash
python3 -c "
from kali_automation.kali_orchestrator import KaliToolsOrchestrator
orchestrator = KaliToolsOrchestrator()
result = await orchestrator.full_penetration_test('example.com')
print(result)
"
\`\`\`

## Docker Usage
\`\`\`bash
docker-compose -f docker-compose.kali.yml up -d
\`\`\`
EOF

echo "🎉 Kali Linux Automation Platform setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure API keys: /kali-automation/configure_api_keys.sh"
echo "2. Test platform: /kali-automation/test_platform.sh"
echo "3. Start platform: sudo systemctl start kali-automation"
echo "4. View logs: sudo journalctl -u kali-automation -f"
echo ""
echo "📚 Documentation: /kali-automation/USAGE_EXAMPLES.md"
echo "🌐 Web interface: http://localhost:8001"
echo "📊 Monitoring: http://localhost:3000 (Grafana)"
echo "📈 Metrics: http://localhost:9090 (Prometheus)"
echo "📝 Logs: http://localhost:5601 (Kibana)"
