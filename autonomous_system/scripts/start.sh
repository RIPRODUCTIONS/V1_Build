#!/bin/bash

# Autonomous Task Solver System - Startup Script
# Production-ready startup with health checks and graceful shutdown

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Configuration
APP_NAME="Autonomous Task Solver"
APP_DIR="/app"
CONFIG_DIR="/app/config"
DATA_DIR="/app/data"
LOGS_DIR="/app/logs"
PYTHON_PATH="/usr/local/bin/python"
PID_FILE="/tmp/autonomous_system.pid"

# Environment variables with defaults
export ENVIRONMENT=${ENVIRONMENT:-"production"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
export DATABASE_PATH=${DATABASE_PATH:-"/app/data/databases"}
export CONFIG_PATH=${CONFIG_PATH:-"/app/config"}

# Function to check if system is ready
check_system_ready() {
    log "Checking system readiness..."

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not available"
        return 1
    fi

    # Check if required directories exist
    if [ ! -d "$CONFIG_DIR" ]; then
        log_error "Configuration directory not found: $CONFIG_DIR"
        return 1
    fi

    if [ ! -d "$DATA_DIR" ]; then
        log_warning "Data directory not found, creating: $DATA_DIR"
        mkdir -p "$DATA_DIR"
    fi

    if [ ! -d "$LOGS_DIR" ]; then
        log_warning "Logs directory not found, creating: $LOGS_DIR"
        mkdir -p "$LOGS_DIR"
    fi

    # Check if configuration file exists
    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        log_warning "Configuration file not found, using defaults"
    fi

    # Check if required Python packages are installed
    if ! python3 -c "import autonomous_system" 2>/dev/null; then
        log_error "Autonomous system package not found"
        return 1
    fi

    log_success "System readiness check passed"
    return 0
}

# Function to start the system
start_system() {
    log "Starting $APP_NAME..."

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warning "$APP_NAME is already running with PID $PID"
            return 1
        else
            log_warning "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    # Change to app directory
    cd "$APP_DIR" || {
        log_error "Failed to change to app directory: $APP_DIR"
        return 1
    }

    # Start the system
    log "Launching autonomous system orchestrator..."

    # Start in background and capture PID
    nohup python3 -m autonomous_system.autonomous_orchestrator > "$LOGS_DIR/startup.log" 2>&1 &
    PID=$!

    # Save PID
    echo "$PID" > "$PID_FILE"

    # Wait a moment for startup
    sleep 2

    # Check if process is running
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "$APP_NAME started successfully with PID $PID"
        log "Logs are being written to: $LOGS_DIR/startup.log"
        return 0
    else
        log_error "Failed to start $APP_NAME"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the system
stop_system() {
    log "Stopping $APP_NAME..."

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Sending SIGTERM to PID $PID..."
            kill -TERM "$PID"

            # Wait for graceful shutdown
            for i in {1..30}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    log_success "$APP_NAME stopped gracefully"
                    rm -f "$PID_FILE"
                    return 0
                fi
                sleep 1
            done

            # Force kill if still running
            log_warning "Force killing process..."
            kill -KILL "$PID"
            rm -f "$PID_FILE"
            log_success "$APP_NAME stopped forcefully"
        else
            log_warning "Process not running, removing stale PID file"
            rm -f "$PID_FILE"
        fi
    else
        log_warning "PID file not found, $APP_NAME may not be running"
    fi
}

# Function to check system status
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_success "$APP_NAME is running with PID $PID"
            return 0
        else
            log_error "$APP_NAME is not running (stale PID file)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        log_warning "$APP_NAME is not running"
        return 1
    fi
}

# Function to restart the system
restart_system() {
    log "Restarting $APP_NAME..."
    stop_system
    sleep 2
    start_system
}

# Function to show logs
show_logs() {
    if [ -f "$LOGS_DIR/startup.log" ]; then
        log "Showing recent logs:"
        tail -n 50 "$LOGS_DIR/startup.log"
    else
        log_warning "No log file found"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "Commands:"
    echo "  start   - Start the autonomous system"
    echo "  stop    - Stop the autonomous system"
    echo "  restart - Restart the autonomous system"
    echo "  status  - Check system status"
    echo "  logs    - Show recent logs"
    echo "  help    - Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  ENVIRONMENT     - Environment (production/development/testing)"
    echo "  LOG_LEVEL       - Logging level (DEBUG/INFO/WARNING/ERROR)"
    echo "  DATABASE_PATH   - Path to database files"
    echo "  CONFIG_PATH     - Path to configuration files"
}

# Main script logic
case "${1:-start}" in
    start)
        if check_system_ready; then
            start_system
        else
            log_error "System not ready, cannot start"
            exit 1
        fi
        ;;
    stop)
        stop_system
        ;;
    restart)
        restart_system
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
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
