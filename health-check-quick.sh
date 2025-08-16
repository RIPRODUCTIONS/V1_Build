#!/bin/bash
# Quick Health Check for M3 Max Quick Fix

echo "🏥 Quick Health Check for M3 Max"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Check Docker
echo "🐳 Checking Docker..."
if docker info > /dev/null 2>&1; then
    print_status "Docker is running"
    echo "   Architecture: $(docker version --format '{{.Server.Arch}}')"
else
    print_error "Docker is not running"
    exit 1
fi

# Check containers
echo ""
echo "📦 Checking containers..."
if docker-compose -f docker-compose.quick-fix.yml ps | grep -q "Up"; then
    print_status "Containers are running"
    docker-compose -f docker-compose.quick-fix.yml ps
else
    print_warning "No containers are running"
fi

# Check ports
echo ""
echo "🔌 Checking ports..."
declare -A PORTS=(
    ["8100"]="AI Framework"
    ["5434"]="PostgreSQL"
    ["6380"]="Redis"
    ["9091"]="Prometheus"
    ["3001"]="Grafana"
)

for port in "${!PORTS[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        print_status "Port $port (${PORTS[$port]}) is active"
    else
        print_warning "Port $port (${PORTS[$port]}) is not active"
    fi
done

# Check services
echo ""
echo "🌐 Checking services..."
services=(
    "http://localhost:8100/health"
    "http://localhost:9091"
    "http://localhost:3001"
)

for service in "${services[@]}"; do
    if curl -f $service > /dev/null 2>&1; then
        print_status "$service is responding"
    else
        print_error "$service is not responding"
    fi
done

# System resources
echo ""
echo "💻 System Resources..."
echo "   CPU Cores: $(sysctl -n hw.ncpu)"
echo "   Memory: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')"
echo "   Architecture: $(uname -m)"

echo ""
echo "🎯 Quick health check complete!"
