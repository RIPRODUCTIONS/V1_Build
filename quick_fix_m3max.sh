#!/bin/bash
# Quick fix for port conflicts on M3 Max

echo "🔧 Quick Fix for M3 Max Port Conflicts"
echo "======================================"

# Stop all existing containers first
echo "🛑 Stopping existing containers..."
docker stop $(docker ps -q) 2>/dev/null || echo "No containers to stop"

# Kill processes on conflicting ports
echo "🔪 Killing processes on conflicting ports..."
for port in 8000 5432 6379 3000 9090; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "Killing process on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

# Create quick production config with different ports
echo "📝 Creating conflict-free production config..."
cat > docker-compose.quick-fix.yml << 'EOF'
version: '3.8'

services:
  ai-framework:
    build:
      context: ./ai_framework
      dockerfile: Dockerfile
      platforms:
        - linux/arm64
    container_name: ai-framework-quick
    ports:
      - "8100:8000"  # Changed port
    environment:
      - DATABASE_URL=postgresql://ai_user:secure_pass@postgres:5432/ai_framework
      - REDIS_URL=redis://:redis_pass@redis:6379/0
      - WORKERS=8
    volumes:
      - ./ai_framework/logs:/app/logs
    networks:
      - ai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    platform: linux/arm64
    container_name: postgres-quick
    ports:
      - "5434:5432"  # Changed port
    environment:
      POSTGRES_DB: ai_framework
      POSTGRES_USER: ai_user
      POSTGRES_PASSWORD: secure_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ai-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    platform: linux/arm64
    container_name: redis-quick
    ports:
      - "6380:6379"  # Changed port
    command: redis-server --requirepass redis_pass
    volumes:
      - redis_data:/data
    networks:
      - ai-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    platform: linux/arm64
    container_name: grafana-quick
    ports:
      - "3001:3000"  # Changed port
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - ai-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    platform: linux/arm64
    container_name: prometheus-quick
    ports:
      - "9091:9090"  # Changed port
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - ai-network
    restart: unless-stopped

networks:
  ai-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  prometheus_data:
EOF

# Create minimal prometheus config if it doesn't exist
mkdir -p monitoring
if [ ! -f monitoring/prometheus.yml ]; then
    echo "📊 Creating Prometheus config..."
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "ai-framework"
    static_configs:
      - targets: ["ai-framework:8000"]
    metrics_path: "/metrics"
    scrape_interval: 10s

  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
EOF
fi

# Start the services
echo "🚀 Starting AI Framework with conflict-free ports..."
docker-compose -f docker-compose.quick-fix.yml up -d

echo "⏱️  Waiting for services to start..."
sleep 30

# Check health
echo "🏥 Checking service health..."
services=(
    "http://localhost:8100/health|AI Framework"
    "http://localhost:3001|Grafana"
    "http://localhost:9091|Prometheus"
)

for service_info in "${services[@]}"; do
    url=$(echo $service_info | cut -d'|' -f1)
    name=$(echo $service_info | cut -d'|' -f2)

    if curl -f $url > /dev/null 2>&1; then
        echo "✅ $name is healthy at $url"
    else
        echo "❌ $name is not responding at $url"
    fi
done

echo ""
echo "🎉 Quick Fix Complete!"
echo "📍 Your AI Framework is now running on:"
echo "   • AI Framework: http://localhost:8100"
echo "   • Grafana:      http://localhost:3001 (admin/admin123)"
echo "   • Prometheus:   http://localhost:9091"
echo "   • PostgreSQL:   localhost:5434"
echo "   • Redis:        localhost:6380"
echo ""
echo "📝 To stop: docker-compose -f docker-compose.quick-fix.yml down"
echo "📊 To monitor: docker-compose -f docker-compose.quick-fix.yml logs -f"
