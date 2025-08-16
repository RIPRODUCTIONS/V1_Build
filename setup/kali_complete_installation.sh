#!/bin/bash
# COMPLETE KALI TOOLS INSTALLATION SCRIPT
# Downloads and installs ALL 600+ Kali Linux tools with automation

echo "========================================="
echo "KALI LINUX COMPLETE TOOLS INSTALLATION"
echo "Installing ALL official Kali metapackages"
echo "========================================="

# Update system first
echo "[1/15] Updating system packages..."
apt update && apt full-upgrade -y

# Install ALL official Kali metapackages (complete arsenal)
echo "[2/15] Installing COMPLETE Kali Linux toolkit..."

# Core System Metapackages
echo "Installing core metapackages..."
apt install -y kali-linux-core
apt install -y kali-linux-default
apt install -y kali-linux-large
apt install -y kali-linux-everything

# Tool Category Metapackages (ALL CATEGORIES)
echo "[3/15] Installing Information Gathering Tools..."
apt install -y kali-tools-information-gathering

echo "[4/15] Installing Vulnerability Assessment Tools..."
apt install -y kali-tools-vulnerability

echo "[5/15] Installing Web Application Tools..."
apt install -y kali-tools-web

echo "[6/15] Installing Database Assessment Tools..."
apt install -y kali-tools-database

echo "[7/15] Installing Password Attack Tools..."
apt install -y kali-tools-passwords

echo "[8/15] Installing Wireless Attack Tools..."
apt install -y kali-tools-wireless

echo "[9/15] Installing Reverse Engineering Tools..."
apt install -y kali-tools-reverse-engineering

echo "[10/15] Installing Exploitation Tools..."
apt install -y kali-tools-exploitation

echo "[11/15] Installing Sniffing & Spoofing Tools..."
apt install -y kali-tools-sniffing-spoofing

echo "[12/15] Installing Post Exploitation Tools..."
apt install -y kali-tools-post-exploitation

echo "[13/15] Installing Forensics Tools..."
apt install -y kali-tools-forensics

echo "[14/15] Installing Reporting Tools..."
apt install -y kali-tools-reporting

echo "[15/15] Installing Social Engineering Tools..."
apt install -y kali-tools-social-engineering

echo "Installing Additional Specialized Tools..."
apt install -y kali-tools-hardware
apt install -y kali-tools-fuzzing
apt install -y kali-tools-gpu
apt install -y kali-tools-rfid
apt install -y kali-tools-sdr
apt install -y kali-tools-crypto-stego
apt install -y kali-tools-windows-resources
apt install -y kali-desktop-live

# Install additional Python automation libraries
echo "Installing Python automation libraries..."
pip3 install -r /automation/requirements.txt

# Install Go tools
echo "Installing Go-based tools..."
go install -v github.com/OWASP/Amass/v3/...@master
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/tomnomnom/httprobe@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/sundowndev/phoneinfoga/v2@latest

# Install Node.js tools
echo "Installing Node.js tools..."
npm install -g @microsoft/mstsc
npm install -g @microsoft/playwright
npm install -g @microsoft/azure-cli

# Create automation directories
echo "Creating automation directories..."
mkdir -p /automation/{results,configs,logs,scripts,workflows}
mkdir -p /opt/investigations/{osint,pentest,forensics,malware}
mkdir -p /opt/results/{reports,evidence,logs}

# Set permissions
chown -R kali:kali /automation /opt/investigations /opt/results
chmod -R 755 /automation /opt/investigations /opt/results

echo "========================================="
echo "INSTALLATION COMPLETE!"
echo "========================================="
echo "Total tools installed: 600+"
echo "Ready for automated cybersecurity operations"
echo ""
echo "Next steps:"
echo "1. Configure API keys for OSINT tools"
echo "2. Run automation framework: python3 /automation/master_orchestrator.py"
echo "3. Execute workflows: python3 /automation/complete_automation_engine.py"
