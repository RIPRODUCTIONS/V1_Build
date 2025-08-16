#!/bin/bash

# Autonomous Task Solver System - Health Check Script
# Docker health check and system status verification

set -e

# Configuration
APP_NAME="Autonomous Task Solver"
PID_FILE="/tmp/autonomous_system.pid"
HEALTH_ENDPOINT="http://localhost:8000/health"
LOG_FILE="/app/logs/healthcheck.log"
MAX_LOG_SIZE=1048576  # 1MB

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Function to rotate log file if too large
rotate_log() {
    if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        touch "$LOG_FILE"
    fi
}

# Function to check if process is running
check_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Function to check system resources
check_resources() {
    # Check CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
        log_warning "High CPU usage: ${CPU_USAGE}%"
        return 1
    fi

    # Check memory usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
    if (( $(echo "$MEMORY_USAGE > 95" | bc -l) )); then
        log_warning "High memory usage: ${MEMORY_USAGE}%"
        return 1
    fi

    # Check disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    if [ "$DISK_USAGE" -gt 95 ]; then
        log_warning "High disk usage: ${DISK_USAGE}%"
        return 1
    fi

    return 0
}

# Function to check API health endpoint
check_api_health() {
    if command -v curl &> /dev/null; then
        if curl -f -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        # Fallback to checking if port is listening
        if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
            return 0
        else
            return 1
        fi
    fi
}

# Function to check database connectivity
check_database() {
    # Check if SQLite database is accessible
    if [ -f "/app/data/databases/autonomous_system.db" ]; then
        if python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/databases/autonomous_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    conn.close()
    print('Database OK')
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" 2>/dev/null; then
            return 0
        else
            return 1
        fi
    else
        # Database file doesn't exist yet (first run)
        return 0
    fi
}

# Function to check file permissions
check_permissions() {
    # Check if app directories are writable
    if [ ! -w "/app/data" ]; then
        log_error "Data directory not writable"
        return 1
    fi

    if [ ! -w "/app/logs" ]; then
        log_error "Logs directory not writable"
        return 1
    fi

    return 0
}

# Function to check network connectivity
check_network() {
    # Check if we can resolve external domains
    if ! nslookup google.com > /dev/null 2>&1; then
        log_warning "DNS resolution failed"
        return 1
    fi

    # Check if we can reach external services
    if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_warning "Network connectivity issues"
        return 1
    fi

    return 0
}

# Function to perform comprehensive health check
perform_health_check() {
    local exit_code=0

    log "Performing health check for $APP_NAME..."

    # Check process
    if check_process; then
        log_success "Process is running"
    else
        log_error "Process is not running"
        exit_code=1
    fi

    # Check resources
    if check_resources; then
        log_success "System resources are healthy"
    else
        log_warning "System resources show warnings"
        # Don't fail health check for resource warnings
    fi

    # Check API health
    if check_api_health; then
        log_success "API health endpoint is responding"
    else
        log_warning "API health endpoint is not responding"
        # Don't fail health check for API issues during startup
    fi

    # Check database
    if check_database; then
        log_success "Database connectivity is healthy"
    else
        log_error "Database connectivity issues"
        exit_code=1
    fi

    # Check permissions
    if check_permissions; then
        log_success "File permissions are correct"
    else
        log_error "File permission issues"
        exit_code=1
    fi

    # Check network (optional)
    if check_network; then
        log_success "Network connectivity is healthy"
    else
        log_warning "Network connectivity issues"
        # Don't fail health check for network issues
    fi

    if [ $exit_code -eq 0 ]; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
    fi

    return $exit_code
}

# Function to show health status
show_health_status() {
    echo "=== $APP_NAME Health Status ==="
    echo "Timestamp: $(date)"
    echo "Process: $(check_process && echo "RUNNING" || echo "STOPPED")"
    echo "PID File: $([ -f "$PID_FILE" ] && echo "EXISTS" || echo "MISSING")"

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "PID: $PID"
        echo "Process Status: $(ps -p "$PID" > /dev/null 2>&1 && echo "ACTIVE" || echo "INACTIVE")"
    fi

    echo "API Health: $(check_api_health && echo "HEALTHY" || echo "UNHEALTHY")"
    echo "Database: $(check_database && echo "HEALTHY" || echo "UNHEALTHY")"
    echo "Permissions: $(check_permissions && echo "OK" || echo "ISSUES")"

    # Show recent logs
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Recent Health Check Logs:"
        tail -n 10 "$LOG_FILE"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 {check|status|help}"
    echo ""
    echo "Commands:"
    echo "  check  - Perform comprehensive health check"
    echo "  status - Show current health status"
    echo "  help   - Show this help message"
    echo ""
    echo "This script is designed for Docker health checks and system monitoring."
}

# Main script logic
case "${1:-check}" in
    check)
        rotate_log
        perform_health_check
        exit $?
        ;;
    status)
        show_health_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

exit 0
