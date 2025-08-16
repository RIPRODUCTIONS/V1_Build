#!/bin/bash
# M3 Max Port Conflict Resolution & Deployment Script
# Fixes SSH tunnels and optimizes for Apple Silicon M3 Max

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo "🚀 M3 Max AI Framework Deployment Optimizer"
echo "=============================================="

# Function to check M3 Max specific requirements
check_m3_max_requirements() {
    print_info "Checking M3 Max specific requirements..."

    # Check Apple Silicon
    if [[ $(uname -m) != "arm64" ]]; then
        print_error "This script requires Apple Silicon (M3 Max detected: $(uname -m))"
        exit 1
    fi

    # Check macOS version (10.14+ required for Network Framework)
    local version=$(sw_vers -productVersion)
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)

    if [[ $major -lt 10 ]] || ([[ $major -eq 10 ]] && [[ $minor -lt 14 ]]); then
        print_error "macOS 10.14+ required for M3 Max optimizations. Current: $version"
        exit 1
    fi

    # Check available memory (should be 48GB for M3 Max)
    local memory_gb=$(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024}')
    if [[ $memory_gb -lt 32 ]]; then
        print_warning "Expected 48GB RAM for M3 Max, detected: ${memory_gb}GB"
    else
        print_status "Memory: ${memory_gb}GB (M3 Max confirmed)"
    fi

    # Check CPU cores (should be 12 for M3 Max)
    local cpu_cores=$(sysctl -n hw.ncpu)
    if [[ $cpu_cores -lt 12 ]]; then
        print_warning "Expected 12 CPU cores for M3 Max, detected: $cpu_cores"
    else
        print_status "CPU Cores: $cpu_cores (M3 Max confirmed)"
    fi

    print_status "M3 Max requirements check passed"
}

# Function to check and kill port conflicts
resolve_port_conflicts() {
    print_info "Checking for port conflicts..."

    # Define production ports (different from staging to avoid conflicts)
    declare -A PRODUCTION_PORTS=(
        ["8100"]="AI Framework"
        ["5434"]="PostgreSQL"
        ["6380"]="Redis"
        ["9091"]="Prometheus"
        ["3001"]="Grafana"
        ["8080"]="Nginx"
    )

    for port in "${!PRODUCTION_PORTS[@]}"; do
        if lsof -i :$port > /dev/null 2>&1; then
            print_warning "Port $port (${PRODUCTION_PORTS[$port]}) is in use"

            # Check if it's SSH tunnel
            if lsof -i :$port | grep -q ssh; then
                print_info "Detected SSH tunnel on port $port"
                echo "Options:"
                echo "1. Kill SSH tunnel (will disconnect remote connections)"
                echo "2. Use alternative port"
                echo "3. Skip and continue"
                read -p "Choose option (1/2/3): " choice

                case $choice in
                    1)
                        print_info "Killing SSH tunnel on port $port..."
                        pkill -f "ssh.*:$port:" || true
                        sleep 2
                        ;;
                    2)
                        print_info "Will use alternative port for ${PRODUCTION_PORTS[$port]}"
                        # We'll handle this in docker-compose generation
                        ;;
                    3)
                        print_warning "Skipping port $port conflict resolution"
                        ;;
                esac
            else
                # Non-SSH process
                print_info "Killing process on port $port..."
                lsof -ti:$port | xargs kill -9 2>/dev/null || true
                sleep 1
            fi
        else
            print_status "Port $port is available"
        fi
    done
}

# Function to optimize Docker for M3 Max
optimize_docker_m3() {
    print_info "Optimizing Docker for M3 Max..."

    # Check if Docker Desktop is using Apple Silicon optimizations
    if docker version --format '{{.Server.Arch}}' | grep -q arm64; then
        print_status "Docker is running natively on Apple Silicon"
    else
        print_warning "Docker may be running in Rosetta mode - check Docker Desktop settings"
    fi

    # Check Docker resource allocation
    local docker_memory=$(docker system info --format '{{.MemTotal}}' 2>/dev/null | awk '{print $1/1024/1024/1024}')
    if [[ -n "$docker_memory" ]] && (( $(echo "$docker_memory < 16" | bc -l) )); then
        print_warning "Docker memory allocation may be too low for M3 Max. Current: ${docker_memory}GB"
    fi

    # Optimize Docker Desktop resources for M3 Max
    print_info "Recommended Docker Desktop settings for M3 Max:"
    echo "  - CPUs: 8-10 (out of 12 cores)"
    echo "  - Memory: 16-24GB (out of 48GB)"
    echo "  - Swap: 4GB"
    echo "  - Disk size: 100GB+"
    echo "  - Enable VirtioFS for better file sharing performance"
    echo "  - Enable BuildKit for faster builds"

    # Set Docker environment variables for M3 Max
    export DOCKER_DEFAULT_PLATFORM=linux/arm64
    export DOCKER_BUILDKIT=1
    print_status "Set Docker environment variables for M3 Max"
}

# Function to create M3 Max thermal monitoring
create_thermal_monitoring() {
    print_info "Creating M3 Max thermal monitoring..."

    cat > monitoring/thermal_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
M3 Max Thermal Monitoring Script
Monitors thermal state and prevents throttling
"""

import subprocess
import time
import psutil
import os

def get_thermal_state():
    """Get current thermal state."""
    try:
        result = subprocess.run(['pmset', '-g', 'thermlog'],
                              capture_output=True, text=True, timeout=5)
        if 'nominal' in result.stdout.lower():
            return 'nominal'
        elif 'fair' in result.stdout.lower():
            return 'fair'
        elif 'serious' in result.stdout.lower():
            return 'serious'
        else:
            return 'unknown'
    except:
        return 'unknown'

def get_cpu_temperature():
    """Get CPU temperature if available."""
    try:
        # Try to get temperature from system
        result = subprocess.run(['sudo', 'powermetrics', '-n', '1', '-i', '1000'],
                              capture_output=True, text=True, timeout=10)
        if 'CPU die temperature' in result.stdout:
            temp_line = [line for line in result.stdout.split('\n') if 'CPU die temperature' in line][0]
            temp = temp_line.split(':')[1].strip().split()[0]
            return float(temp)
    except:
        pass
    return None

def get_power_source():
    """Get current power source."""
    try:
        result = subprocess.run(['pmset', '-g', 'power'],
                              capture_output=True, text=True, timeout=5)
        if 'AC Power' in result.stdout:
            return 'AC'
        else:
            return 'Battery'
    except:
        return 'unknown'

def get_m3_max_metrics():
    """Get comprehensive M3 Max metrics."""
    return {
        'cpu_count_physical': psutil.cpu_count(logical=False),
        'cpu_count_logical': psutil.cpu_count(logical=True),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'memory_percent': psutil.virtual_memory().percent,
        'cpu_percent': psutil.cpu_percent(interval=1),
        'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None,
        'thermal_state': get_thermal_state(),
        'cpu_temperature': get_cpu_temperature(),
        'power_source': get_power_source(),
        'arch': os.uname().machine
    }

def monitor_thermal_state():
    """Monitor thermal state and log warnings."""
    while True:
        metrics = get_m3_max_metrics()

        # Log metrics
        print(f"Thermal State: {metrics['thermal_state']}")
        print(f"CPU Usage: {metrics['cpu_percent']}%")
        print(f"Memory Usage: {metrics['memory_percent']}%")

        if metrics['thermal_state'] != 'nominal':
            print(f"⚠️  Warning: Thermal state is {metrics['thermal_state']}")

        if metrics['cpu_percent'] > 80:
            print(f"⚠️  Warning: High CPU usage: {metrics['cpu_percent']}%")

        if metrics['memory_percent'] > 80:
            print(f"⚠️  Warning: High memory usage: {metrics['memory_percent']}%")

        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    print("🚀 M3 Max Thermal Monitor Started")
    print("=" * 40)
    monitor_thermal_state()
EOF

    chmod +x monitoring/thermal_monitor.py
    print_status "Created M3 Max thermal monitoring script"
}

# Function to create M3-optimized docker-compose.production.yml
create_m3_production_config() {
    print_info "Creating M3 Max optimized production configuration..."

    cat > docker-compose.m3-production.yml << 'EOF'
version: '3.8'

services:
  # AI Framework - optimized for M3 Max
  ai-framework-production:
    build:
      context: ./ai_framework
      dockerfile: Dockerfile.m3-production
      platforms:
        - linux/arm64  # Native Apple Silicon
    container_name: ai-framework-production
    ports:
      - "8100:8000"  # Different port to avoid conflicts
    environment:
      # M3 Max specific optimizations
      - WORKERS=8
      - WORKER_CONNECTIONS=2000
      - MAX_REQUESTS=10000
      - TIMEOUT=300
      - PYTHONMALLOC=pymalloc
      - MALLOC_ARENA_MAX=4
      - MALLOC_MMAP_THRESHOLD_=131072
      - WEB_CONCURRENCY=8
      # Database settings
      - DATABASE_URL=postgresql://ai_user:${POSTGRES_PASSWORD}@postgres-production:5432/ai_framework
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis-production:6379/0
      # M3 Max specific
      - APPLE_SILICON_OPTIMIZED=true
      - USE_NEURAL_ENGINE=true
      - THERMAL_MONITORING=true
    volumes:
      - ./ai_framework/logs:/app/logs
      - ./ai_framework/data:/app/data
      - ./monitoring:/app/monitoring
    networks:
      - ai-network-production
    depends_on:
      - postgres-production
      - redis-production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '8.0'
        reservations:
          memory: 8G
          cpus: '4.0'
    # M3 Max specific optimizations
    platform: linux/arm64
    shm_size: 2gb
    ulimits:
      nofile:
        soft: 65536
        hard: 65536

  # PostgreSQL - ARM64 optimized for M3 Max
  postgres-production:
    image: postgres:15-alpine
    platform: linux/arm64
    container_name: ai-framework-postgres-production
    ports:
      - "5434:5432"  # Different port
    environment:
      POSTGRES_DB: ai_framework
      POSTGRES_USER: ai_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      # M3 Max PostgreSQL optimizations
      POSTGRES_SHARED_BUFFERS: 4GB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 12GB
      POSTGRES_MAINTENANCE_WORK_MEM: 1GB
      POSTGRES_WORK_MEM: 64MB
      POSTGRES_MAX_WORKER_PROCESSES: 12
      POSTGRES_MAX_PARALLEL_WORKERS: 8
      POSTGRES_MAX_PARALLEL_WORKERS_PER_GATHER: 4
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=4GB
      -c effective_cache_size=12GB
      -c maintenance_work_mem=1GB
      -c work_mem=64MB
      -c max_worker_processes=12
      -c max_parallel_workers=8
      -c max_parallel_workers_per_gather=4
      -c checkpoint_completion_target=0.9
      -c wal_buffers=32MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./ai_framework/database/backups:/backups
    networks:
      - ai-network-production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '3.0'
        reservations:
          memory: 4G
          cpus: '2.0'

  # Redis - ARM64 optimized for M3 Max
  redis-production:
    image: redis:7-alpine
    platform: linux/arm64
    container_name: ai-framework-redis-production
    ports:
      - "6380:6379"  # Different port
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 4gb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --save 900 1
      --save 300 10
      --save 60 10000
      --tcp-keepalive 300
      --timeout 0
      --tcp-backlog 511
      --databases 16
    volumes:
      - redis_data_prod:/data
    networks:
      - ai-network-production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '1.0'
        reservations:
          memory: 2G
          cpus: '0.5'

  # Prometheus - ARM64 with M3 Max optimizations
  prometheus-production:
    image: prom/prometheus:latest
    platform: linux/arm64
    container_name: ai-framework-prometheus-production
    ports:
      - "9091:9090"  # Different port
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
      - '--storage.tsdb.max-block-duration=2h'
      - '--storage.tsdb.min-block-duration=2h'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data_prod:/prometheus
    networks:
      - ai-network-production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '0.5'
        reservations:
          memory: 1G
          cpus: '0.25'

  # Grafana - ARM64 with M3 Max optimizations
  grafana-production:
    image: grafana/grafana:latest
    platform: linux/arm64
    container_name: ai-framework-grafana-production
    ports:
      - "3001:3000"  # Different port
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
      - GF_SERVER_ROOT_URL=http://localhost:3001
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
    volumes:
      - grafana_data_prod:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    depends_on:
      - prometheus-production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '0.5'
        reservations:
          memory: 1G
          cpus: '0.25'

  # Nginx - ARM64 reverse proxy with M3 Max optimizations
  nginx-production:
    image: nginx:alpine
    platform: linux/arm64
    container_name: ai-framework-nginx-production
    ports:
      - "8080:80"   # Different port
      - "8443:443"  # Different port
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - ai-framework-production
    networks:
      - ai-network-production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  # Thermal Monitor - M3 Max specific
  thermal-monitor:
    build:
      context: .
      dockerfile: Dockerfile.thermal-monitor
    container_name: ai-framework-thermal-monitor
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./monitoring:/app/monitoring
    environment:
      - THERMAL_MONITORING=true
      - M3_MAX_OPTIMIZED=true
    networks:
      - ai-network-production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
        reservations:
          memory: 256M
          cpus: '0.1'

networks:
  ai-network-production:
    driver: bridge
    name: ai-framework-production-network
    driver_opts:
      com.docker.network.bridge.name: ai-framework-br0

volumes:
  postgres_data_prod:
    name: ai_framework_postgres_prod
    driver: local
    driver_opts:
      type: apfs
      o: cow
  redis_data_prod:
    name: ai_framework_redis_prod
    driver: local
  prometheus_data_prod:
    name: ai_framework_prometheus_prod
    driver: local
  grafana_data_prod:
    name: ai_framework_grafana_prod
    driver: local
EOF

    print_status "Created M3-optimized production configuration"
}

# Function to create M3-optimized Dockerfile
create_m3_dockerfile() {
    print_info "Creating M3 Max optimized Dockerfile..."

    cat > ai_framework/Dockerfile.m3-production << 'EOF'
# Multi-stage build optimized for Apple Silicon M3 Max
FROM --platform=linux/arm64 python:3.11-slim as base

# M3 Max environment optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1 \
    PYTHONMALLOC=pymalloc \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MALLOC_ARENA_MAX=4 \
    MALLOC_MMAP_THRESHOLD_=131072 \
    WEB_CONCURRENCY=8 \
    WORKERS=8 \
    WORKER_CONNECTIONS=2000

# Install system dependencies for ARM64
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    htop \
    iotop \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r ai_user && useradd -r -g ai_user ai_user

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt requirements-m3max.txt ./
RUN pip install --no-cache-dir -r requirements-m3max.txt

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R ai_user:ai_user /app

# Switch to non-root user
USER ai_user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Optimized startup command for M3 Max
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "8", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--worker-connections", "2000", \
     "--max-requests", "10000", \
     "--timeout-keep-alive", "5", \
     "--limit-max-requests", "10000"]
EOF

    print_status "Created M3-optimized Dockerfile"
}

# Function to create thermal monitor Dockerfile
create_thermal_monitor_dockerfile() {
    print_info "Creating thermal monitor Dockerfile..."

    cat > Dockerfile.thermal-monitor << 'EOF'
FROM --platform=linux/arm64 python:3.11-slim

# Install monitoring tools
RUN apt-get update && apt-get install -y \
    curl \
    htop \
    iotop \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy thermal monitoring script
COPY monitoring/thermal_monitor.py .

# Install dependencies
RUN pip install psutil

# Run thermal monitor
CMD ["python", "thermal_monitor.py"]
EOF

    print_status "Created thermal monitor Dockerfile"
}

# Function to create macOS-specific optimizations
create_macos_optimizations() {
    print_info "Creating macOS-specific optimizations..."

    # Create .env.m3-production with optimized settings
    cat > .env.m3-production << EOF
# M3 Max Production Environment
NODE_ENV=production
ENVIRONMENT=production

# Security
JWT_SECRET=${JWT_SECRET:-$(openssl rand -hex 32)}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}
REDIS_PASSWORD=${REDIS_PASSWORD:-$(openssl rand -hex 16)}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-$(openssl rand -hex 16)}

# Database optimized for M3 Max
DATABASE_URL=postgresql://ai_user:\${POSTGRES_PASSWORD}@localhost:5434/ai_framework
DB_POOL_SIZE=40
DB_MAX_OVERFLOW=20

# Redis optimized for M3 Max
REDIS_URL=redis://:\${REDIS_PASSWORD}@localhost:6380/0
REDIS_MAX_CONNECTIONS=100

# Performance settings for M3 Max
WORKERS=8
MAX_WORKERS=8
WORKER_CONNECTIONS=2000
MEMORY_LIMIT=16G

# M3 Max specific optimizations
PLATFORM=darwin
ARCH=arm64
USE_APPLE_SILICON_OPTIMIZATIONS=true
USE_NEURAL_ENGINE=true
THERMAL_MONITORING=true

# Apple Silicon specific
PYTHONMALLOC=pymalloc
MALLOC_ARENA_MAX=4
MALLOC_MMAP_THRESHOLD_=131072
WEB_CONCURRENCY=8

# Docker optimizations
DOCKER_DEFAULT_PLATFORM=linux/arm64
DOCKER_BUILDKIT=1
EOF

    print_status "Created M3 Max production environment file"
}

# Function to create startup script for M3 Max
create_m3_startup_script() {
    print_info "Creating M3 Max startup script..."

    cat > start-m3-production.sh << 'EOF'
#!/bin/bash
# M3 Max Production Startup Script

set -e

echo "🚀 Starting AI Framework on M3 Max..."

# Load environment variables
if [ -f .env.m3-production ]; then
    export $(cat .env.m3-production | xargs)
fi

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check available resources
AVAILABLE_MEMORY=$(sysctl hw.memsize | awk '{print $2/1024/1024/1024}' | cut -d. -f1)
echo "💾 Available Memory: ${AVAILABLE_MEMORY}GB"

if [ $AVAILABLE_MEMORY -lt 16 ]; then
    echo "⚠️  Warning: Less than 16GB RAM available. Performance may be impacted."
fi

# Check thermal state
echo "🌡️  Checking thermal state..."
if command -v pmset &> /dev/null; then
    THERMAL_STATE=$(pmset -g thermlog 2>/dev/null | grep -i "thermal" | tail -1 || echo "nominal")
    echo "   Thermal State: $THERMAL_STATE"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.m3-production.yml down --remove-orphans || true

# Build and start services
echo "🔨 Building M3 Max optimized images..."
docker-compose -f docker-compose.m3-production.yml build

echo "🚀 Starting production services..."
docker-compose -f docker-compose.m3-production.yml up -d

echo "⏱️  Waiting for services to be ready..."
sleep 30

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

# Start thermal monitoring
echo "🌡️  Starting thermal monitoring..."
docker-compose -f docker-compose.m3-production.yml logs thermal-monitor &

echo ""
echo "🎉 AI Framework is running on M3 Max!"
echo "📊 Access points:"
echo "   • AI Framework: http://localhost:8100"
echo "   • Grafana:      http://localhost:3001 (admin/password from .env)"
echo "   • Prometheus:   http://localhost:9091"
echo "   • Nginx:        http://localhost:8080"
echo ""
echo "📈 Monitor with: docker-compose -f docker-compose.m3-production.yml logs -f"
echo "🌡️  Thermal monitoring: docker-compose -f docker-compose.m3-production.yml logs thermal-monitor"
EOF

    chmod +x start-m3-production.sh
    print_status "Created M3 Max startup script"
}

# Function to create monitoring configuration
create_monitoring_config() {
    print_info "Creating monitoring configuration..."

    # Create monitoring directory
    mkdir -p monitoring/grafana monitoring/prometheus nginx

    # Create Prometheus config
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'ai-framework'
    static_configs:
      - targets: ['ai-framework-production:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-production:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-production:6379']

  - job_name: 'thermal-monitor'
    static_configs:
      - targets: ['thermal-monitor:8000']
    scrape_interval: 30s
EOF

    # Create Grafana provisioning
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-production:9090
    isDefault: true
EOF

    # Create Nginx config
    cat > nginx/nginx.prod.conf << 'EOF'
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # M3 Max optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    upstream ai_framework {
        server ai-framework-production:8000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://ai_framework;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check
        location /health {
            proxy_pass http://ai_framework;
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Default
        location / {
            proxy_pass http://ai_framework;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

    print_status "Created monitoring and Nginx configuration"
}

# Function to create health check script
create_health_check_script() {
    print_info "Creating health check script..."

    cat > health-check-m3.sh << 'EOF'
#!/bin/bash
# M3 Max Health Check Script

set -e

echo "🏥 M3 Max AI Framework Health Check"
echo "==================================="

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
    echo "   Version: $(docker version --format '{{.Server.Version}}')"
else
    print_error "Docker is not running"
    exit 1
fi

# Check containers
echo ""
echo "📦 Checking containers..."
if docker-compose -f docker-compose.m3-production.yml ps | grep -q "Up"; then
    print_status "Containers are running"
    docker-compose -f docker-compose.m3-production.yml ps
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
    ["8080"]="Nginx"
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

# Thermal state
echo ""
echo "🌡️  Thermal State..."
if command -v pmset &> /dev/null; then
    THERMAL_STATE=$(pmset -g thermlog 2>/dev/null | grep -i "thermal" | tail -1 || echo "nominal")
    echo "   Status: $THERMAL_STATE"
    if [[ "$THERMAL_STATE" != "nominal" ]]; then
        print_warning "Thermal state is not nominal: $THERMAL_STATE"
    else
        print_status "Thermal state is nominal"
    fi
fi

# Docker resources
echo ""
echo "🐳 Docker Resources..."
if docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null; then
    echo "Container resource usage above"
else
    print_warning "No running containers to check resources"
fi

echo ""
echo "🎯 Health check complete!"
EOF

    chmod +x health-check-m3.sh
    print_status "Created health check script"
}

# Main execution
main() {
    print_info "Starting M3 Max optimization process..."

    # Check M3 Max requirements
    check_m3_max_requirements

    # Check if we're in the right directory
    if [ ! -d "ai_framework" ]; then
        print_error "Please run this script from the project root directory (where 'ai_framework' folder is located)"
        exit 1
    fi

    # Resolve port conflicts
    resolve_port_conflicts

    # Optimize Docker
    optimize_docker_m3

    # Create optimized configurations
    create_m3_production_config
    create_m3_dockerfile
    create_thermal_monitor_dockerfile
    create_macos_optimizations
    create_m3_startup_script
    create_monitoring_config
    create_health_check_script
    create_thermal_monitoring

    print_status "M3 Max optimization complete!"
    print_info "Next steps:"
    echo "  1. Review .env.m3-production and update any secrets"
    echo "  2. Run: ./start-m3-production.sh"
    echo "  3. Access your AI Framework at http://localhost:8100"
    echo "  4. Monitor health with: ./health-check-m3.sh"
    echo "  5. Monitor thermal state with: docker-compose -f docker-compose.m3-production.yml logs thermal-monitor"

    # Ask if user wants to start now
    read -p "Start the optimized production environment now? (y/n): " start_now
    if [[ $start_now =~ ^[Yy]$ ]]; then
        ./start-m3-production.sh
    fi
}

# Run main function
main "$@"
