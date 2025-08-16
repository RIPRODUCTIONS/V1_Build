#!/bin/bash
# Quick Start for M3 Max Quick Fix

set -e

echo "🚀 Starting Quick Fix Environment on M3 Max..."

# Load environment variables
if [ -f .env.quick-fix ]; then
    export $(cat .env.quick-fix | xargs)
fi

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check available resources
AVAILABLE_MEMORY=$(sysctl hw.memsize | awk '{print $2/1024/1024/1024}' | cut -d. -f1)
echo "💾 Available Memory: ${AVAILABLE_MEMORY}GB"

if [ $AVAILABLE_MEMORY -lt 8 ]; then
    echo "⚠️  Warning: Less than 8GB RAM available. Performance may be impacted."
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.quick-fix.yml down --remove-orphans || true

# Build and start services
echo "🔨 Building quick fix images..."
docker-compose -f docker-compose.quick-fix.yml build

echo "🚀 Starting quick fix services..."
docker-compose -f docker-compose.quick-fix.yml up -d

echo "⏱️  Waiting for services to be ready..."
sleep 20

# Health checks
echo "🏥 Performing health checks..."
services=("http://localhost:8100/health" "http://localhost:9091" "http://localhost:3001")

for service in "${services[@]}"; do
    if curl -f $service > /dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not responding"
    fi
done

echo ""
echo "🎉 Quick Fix Environment is running on M3 Max!"
echo "📊 Access points:"
echo "   • AI Framework: http://localhost:8100"
echo "   • Grafana:      http://localhost:3001 (admin/admin123)"
echo "   • Prometheus:   http://localhost:9091"
echo ""
echo "📈 Monitor with: docker-compose -f docker-compose.quick-fix.yml logs -f"
echo "🛑 Stop with: docker-compose -f docker-compose.quick-fix.yml down"
