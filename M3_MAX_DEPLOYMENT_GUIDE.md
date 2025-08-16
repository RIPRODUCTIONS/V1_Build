# 🚀 M3 Max AI Framework Deployment Guide

## Overview

This guide covers deploying your AI Framework in production mode on MacBook Pro M3 Max, with comprehensive port conflict resolution, SSH tunnel handling, and Apple Silicon optimizations.

## 🎯 Deployment Options

### 1. **Development Mode** (Local Development)
- Uses ports: 8000, 5432, 6379, 9090, 3000
- Single worker process
- Hot reload enabled
- Local database and cache

### 2. **Production Mode** (M3 Max Optimized)
- Uses ports: 8100, 5434, 6380, 9091, 3001, 8080
- 12 worker processes
- Load balancing with Nginx
- Production-grade monitoring
- ARM64 native containers

## 🚀 Quick Deployment

### Step 1: Run Deployment Script
```bash
./deploy_m3_max.sh
```

This script will:
- ✅ Resolve port conflicts automatically
- ✅ Handle SSH tunnel conflicts intelligently
- ✅ Create M3 Max optimized configurations
- ✅ Generate production Docker files
- ✅ Setup monitoring and Nginx

### Step 2: Start Production Environment
```bash
./start-m3-production.sh
```

## 🔧 Port Conflict Resolution

### **Automatic Conflict Detection**
The deployment script automatically detects and resolves:
- **SSH Tunnels**: Identifies remote connections and offers options
- **Local Services**: Kills conflicting processes safely
- **Port Reuse**: Suggests alternative ports when needed

### **Production Port Mapping**
| Service | Development Port | Production Port | Purpose |
|---------|------------------|-----------------|---------|
| AI Framework | 8000 | 8100 | Main API |
| PostgreSQL | 5432 | 5434 | Database |
| Redis | 6379 | 6380 | Cache |
| Prometheus | 9090 | 9091 | Metrics |
| Grafana | 3000 | 3001 | Dashboards |
| Nginx | 80 | 8080 | Reverse Proxy |

### **SSH Tunnel Handling**
When SSH tunnels are detected, you'll get options:
1. **Kill Tunnel**: Disconnects remote connections
2. **Use Alternative Port**: Automatically assigns new port
3. **Skip**: Continue without resolution

## 🐳 Docker Optimization

### **M3 Max Specific Optimizations**
```dockerfile
# ARM64 native builds
FROM --platform=linux/arm64 python:3.11-slim

# M3 Max environment variables
ENV PYTHONMALLOC=pymalloc
ENV MALLOC_ARENA_MAX=4
ENV WEB_CONCURRENCY=12
```

### **Resource Allocation**
- **AI Framework**: 6 CPU cores, 8GB RAM
- **PostgreSQL**: 2 CPU cores, 4GB RAM
- **Redis**: 1 CPU core, 2GB RAM
- **Monitoring**: 0.5 CPU core, 1GB RAM each

### **Docker Desktop Settings**
Recommended for M3 Max:
- **CPUs**: 8-10 (out of 12 cores)
- **Memory**: 16-24GB (out of 48GB)
- **Swap**: 4GB
- **Disk**: 100GB+
- **VirtioFS**: Enabled for performance

## 📊 Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx (8080)  │───▶│ AI Framework    │───▶│ PostgreSQL      │
│   (Load Balancer)│    │   (8100)        │    │   (5434)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Redis (6380)  │              │
         │              │   (Cache)       │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Grafana (3001) │    │ Prometheus      │    │   Monitoring    │
│  (Dashboards)   │    │   (9091)        │    │   & Alerts      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔍 Monitoring & Observability

### **Prometheus Metrics**
- API response times
- Database performance
- System resource usage
- Custom business metrics

### **Grafana Dashboards**
- Real-time performance monitoring
- Resource utilization graphs
- Error rate tracking
- Custom alerting rules

### **Health Checks**
```bash
# Run comprehensive health check
./health-check-m3.sh

# Check specific service
curl http://localhost:8100/health
```

## 🚀 Performance Optimizations

### **M3 Max Specific**
```bash
# Environment variables
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16
OPENBLAS_NUM_THREADS=16
PYTHONOPTIMIZE=1
```

### **Database Optimizations**
```sql
-- PostgreSQL settings for M3 Max
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 8GB
max_worker_processes = 12
max_parallel_workers = 8
```

### **Redis Optimizations**
```bash
# Redis configuration
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
```

## 🔐 Security Features

### **Nginx Security Headers**
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

### **Rate Limiting**
```nginx
# API rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

### **Authentication**
- JWT-based authentication
- Secure password generation
- Environment-based secrets

## 📈 Scaling & Load Balancing

### **Worker Processes**
- **Development**: 1 worker
- **Production**: 12 workers
- **Auto-scaling**: Based on CPU usage

### **Connection Pooling**
- **Database**: 40 connections with 20 overflow
- **Redis**: 100 max connections
- **HTTP**: 2000 worker connections

### **Load Balancing**
```nginx
upstream ai_framework {
    server ai-framework-production:8000;
    keepalive 32;
}
```

## 🔄 Deployment Workflow

### **1. Pre-deployment Checks**
```bash
# Check system resources
./health-check-m3.sh

# Verify Docker resources
docker system df
docker stats --no-stream
```

### **2. Deploy**
```bash
# Run deployment script
./deploy_m3_max.sh

# Start production environment
./start-m3-production.sh
```

### **3. Post-deployment Verification**
```bash
# Health checks
./health-check-m3.sh

# Monitor logs
docker-compose -f docker-compose.m3-production.yml logs -f

# Check metrics
open http://localhost:3001  # Grafana
open http://localhost:9091  # Prometheus
```

## 🛠️ Troubleshooting

### **Common Issues**

#### 1. **Port Conflicts**
```bash
# Check what's using a port
lsof -i :8100

# Kill conflicting process
sudo lsof -ti:8100 | xargs kill -9
```

#### 2. **Docker Resource Issues**
```bash
# Check Docker stats
docker stats

# Clean up Docker
docker system prune -a
docker volume prune
```

#### 3. **Service Not Starting**
```bash
# Check container logs
docker-compose -f docker-compose.m3-production.yml logs ai-framework-production

# Check container status
docker-compose -f docker-compose.m3-production.yml ps
```

#### 4. **Performance Issues**
```bash
# Monitor system resources
htop
vm_stat

# Check Docker resource limits
docker stats --no-stream
```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Restart with debug
docker-compose -f docker-compose.m3-production.yml restart ai-framework-production
```

## 📊 Performance Benchmarks

### **Expected Performance on M3 Max**
- **API Response**: < 25ms (95th percentile)
- **Database Queries**: < 5ms (simple queries)
- **Concurrent Users**: 1000+ simultaneous
- **Throughput**: 10,000+ requests/second
- **Memory Usage**: Efficient 48GB utilization

### **Load Testing**
```bash
# Install load testing tools
pip install locust

# Run load test
locust -f performance_tests/locustfile.py --host=http://localhost:8100
```

## 🔄 Maintenance & Updates

### **Regular Maintenance**
```bash
# Update containers
docker-compose -f docker-compose.m3-production.yml pull
docker-compose -f docker-compose.m3-production.yml up -d

# Backup database
docker exec ai-framework-postgres-production pg_dump -U ai_user ai_framework > backup.sql

# Clean up logs
docker system prune -f
```

### **Monitoring Alerts**
- **High CPU Usage**: > 80% for 5 minutes
- **High Memory Usage**: > 90% for 5 minutes
- **High Error Rate**: > 5% for 1 minute
- **Service Down**: Health check failure

### **Backup Strategy**
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec ai-framework-postgres-production pg_dump -U ai_user ai_framework > backup_$DATE.sql
tar -czf backup_$DATE.tar.gz backup_$DATE.sql logs/ data/
```

## 🎯 Next Steps

### **Immediate Actions**
1. **Run Deployment**: `./deploy_m3_max.sh`
2. **Start Production**: `./start-m3-production.sh`
3. **Verify Health**: `./health-check-m3.sh`
4. **Access Services**: http://localhost:8100

### **Advanced Configuration**
1. **Custom Metrics**: Add business-specific Prometheus metrics
2. **Alerting Rules**: Configure Grafana alerting
3. **SSL/TLS**: Add HTTPS with Let's Encrypt
4. **Backup Automation**: Setup automated backup scripts

### **Production Hardening**
1. **Firewall Rules**: Configure macOS firewall
2. **VPN Access**: Secure remote access
3. **Log Aggregation**: Centralized logging
4. **Disaster Recovery**: Multi-region deployment

## 📚 Additional Resources

### **Documentation**
- [AI Framework README](ai_framework/README.md)
- [M3 Max Setup Guide](M3_MAX_SETUP_GUIDE.md)
- [Architecture Docs](docs/ARCHITECTURE.md)

### **Scripts**
- `deploy_m3_max.sh` - Main deployment script
- `start-m3-production.sh` - Production startup
- `health-check-m3.sh` - Health monitoring

### **Configuration Files**
- `docker-compose.m3-production.yml` - Production services
- `Dockerfile.m3-production` - M3 Max optimized build
- `.env.m3-production` - Production environment

---

**Ready to deploy your AI Framework in production mode? 🚀**

*Run `./deploy_m3_max.sh` to get started!*
