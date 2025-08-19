#!/bin/bash

# n8n Automation Setup Script
# Enhanced setup with error handling, security checks, and resource optimization

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="$SCRIPT_DIR/setup.log"
readonly N8N_URL="http://localhost:5678"
readonly REQUIRED_COMMANDS=("docker" "docker-compose" "curl" "node" "npm")

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "❌ ERROR: $1"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    log "🔍 Checking system requirements..."
    
    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command_exists "$cmd"; then
            error_exit "$cmd is not installed. Please install it first."
        fi
    done
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        error_exit "Docker daemon is not running. Please start Docker first."
    fi
    
    # Check available disk space (minimum 2GB)
    local available_space=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 2097152 ]; then  # 2GB in KB
        log "⚠️  WARNING: Less than 2GB disk space available"
    fi
    
    log "✅ All requirements met"
}

# Setup environment
setup_environment() {
    log "📁 Setting up environment..."
    
    # Create necessary directories with proper permissions
    mkdir -p workflows/{email,api,data-processing,notifications,integrations}
    mkdir -p data/{input,output,processed}
    mkdir -p logs
    mkdir -p backups
    
    # Set secure permissions
    chmod 755 workflows/ data/ logs/ backups/
    chmod 700 backups/  # Backup directory should be more secure
    
    # Set file permissions if JSON files exist
    find workflows/ -name "*.json" -type f -exec chmod 644 {} \; 2>/dev/null || true
    
    log "✅ Directory structure created"
}

# Validate environment file
validate_env_file() {
    log "🔐 Validating environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            log "📋 Creating .env from template..."
            cp .env.template .env
            log "⚠️  Please edit .env file with your actual credentials before starting n8n"
        else
            error_exit ".env file not found and no template available"
        fi
    fi
    
    # Check for weak passwords
    if grep -q "yourSecurePassword123\|password123\|admin123" .env; then
        log "⚠️  WARNING: Weak password detected in .env file. Please change it!"
    fi
    
    # Check for placeholder values
    if grep -q "CHANGE_THIS\|YOUR_API_KEY\|your_" .env; then
        log "⚠️  WARNING: Placeholder values detected in .env file. Please update them!"
    fi
    
    log "✅ Environment validation completed"
}

# Check if n8n is running
check_n8n_status() {
    log "🔍 Checking n8n status..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$N8N_URL/healthz" >/dev/null 2>&1 || curl -f -s "$N8N_URL" >/dev/null 2>&1; then
            log "✅ n8n is running at $N8N_URL"
            return 0
        fi
        
        if [ $attempt -eq 1 ]; then
            log "⏳ n8n is not running. Starting it now..."
            docker-compose up -d
        fi
        
        log "⏳ Waiting for n8n to start... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    error_exit "n8n failed to start after $max_attempts attempts"
}

# Setup monitoring
setup_monitoring() {
    log "📊 Setting up monitoring..."
    
    # Make backup script executable
    if [ -f "backup.sh" ]; then
        chmod +x backup.sh
        log "✅ Backup script configured"
    fi
    
    # Create log rotation configuration
    cat > /tmp/n8n-logrotate << EOF
/var/log/n8n*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
    
    log "✅ Monitoring setup completed"
}

# Create sample data files
create_sample_data() {
    log "📄 Creating sample data files..."
    
    # Create sample CSV with more realistic data
    cat > data/input/sample_transactions.csv << EOF
id,amount,customer,date,status,category,description
1,1500.00,John Doe,2024-01-15,completed,purchase,Office supplies
2,500.50,Jane Smith,2024-01-15,pending,refund,Product return
3,2500.75,Bob Johnson,2024-01-15,completed,purchase,Software license
4,750.25,Alice Brown,2024-01-15,pending,purchase,Hardware equipment
5,125.00,Charlie Wilson,2024-01-16,completed,purchase,Monthly subscription
6,3000.00,Diana Prince,2024-01-16,failed,purchase,Server hardware
7,89.99,Eddie Murphy,2024-01-16,completed,purchase,Software tools
8,1200.50,Fiona Green,2024-01-17,pending,purchase,Consulting services
EOF
    
    # Create sample email data
    cat > data/input/sample_emails.json << EOF
[
  {
    "from": "support@example.com",
    "to": "admin@company.com",
    "subject": "URGENT: System Alert",
    "body": "Critical system alert requires immediate attention.",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  {
    "from": "info@vendor.com",
    "to": "purchasing@company.com",
    "subject": "Invoice #12345",
    "body": "Please find attached invoice for recent purchase.",
    "timestamp": "2024-01-15T14:20:00Z"
  }
]
EOF
    
    log "✅ Sample data files created"
}

# Optimize performance
optimize_performance() {
    log "⚡ Optimizing performance..."
    
    # Clean up old Docker images and containers
    docker system prune -f >/dev/null 2>&1 || true
    
    # Optimize Docker Compose configuration
    if grep -q "restart: always" docker-compose.yml; then
        log "🔄 Updating restart policy to 'unless-stopped'"
        sed -i 's/restart: always/restart: unless-stopped/g' docker-compose.yml
    fi
    
    log "✅ Performance optimization completed"
}

# Security hardening
security_hardening() {
    log "🔒 Applying security hardening..."
    
    # Ensure sensitive files have proper permissions
    chmod 600 .env 2>/dev/null || true
    chmod 600 .env.template 2>/dev/null || true
    
    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        log "📝 Creating .gitignore file"
        cat > .gitignore << EOF
.env
node_modules/
*.log
.DS_Store
EOF
    fi
    
    log "✅ Security hardening completed"
}

# Health check and final validation
final_health_check() {
    log "🏥 Performing final health check..."
    
    # Check container status
    if ! docker-compose ps | grep -q "Up"; then
        log "⚠️  WARNING: Some containers may not be running properly"
    fi
    
    # Check API responsiveness
    if curl -f -s "$N8N_URL/healthz" >/dev/null 2>&1; then
        log "✅ n8n API is responsive"
    else
        log "⚠️  WARNING: n8n API may not be fully ready yet"
    fi
    
    # Check disk usage
    local disk_usage=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        log "⚠️  WARNING: Disk usage is high (${disk_usage}%)"
    fi
    
    log "✅ Health check completed"
}

# Display final instructions
show_completion_message() {
    log "✅ Setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Access n8n at: $N8N_URL"
    echo "2. Login with credentials from your .env file"
    echo "3. Import workflows from the workflows/ directory"
    echo "4. Configure your API keys and credentials"
    echo "5. Test each workflow individually"
    echo ""
    echo "📚 Additional resources:"
    echo "- README.md: Detailed workflow documentation"
    echo "- DEVELOPMENT.md: Development and troubleshooting guide"
    echo "- QUICK_REFERENCE.md: Quick reference for common tasks"
    echo ""
    echo "🔧 Useful commands:"
    echo "- npm start: Start all services"
    echo "- npm stop: Stop all services"
    echo "- npm run logs: View container logs"
    echo "- ./backup.sh: Run manual backup"
    echo ""
    echo "⚠️  Important: Please review and update your .env file with actual credentials!"
}

# Main execution
main() {
    log "🚀 Starting n8n Automation Environment Setup..."
    
    check_requirements
    setup_environment
    validate_env_file
    security_hardening
    optimize_performance
    setup_monitoring
    create_sample_data
    check_n8n_status
    final_health_check
    show_completion_message
    
    log "🎉 Setup completed successfully!"
}

# Trap errors
trap 'error_exit "Setup failed on line $LINENO"' ERR

# Run main function
main "$@" 