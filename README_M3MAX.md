# 🚀 M3 Max AI Framework Setup

## Overview

This directory contains everything you need to set up and optimize your AI Framework for MacBook Pro M3 Max with 48GB RAM. The setup is designed to leverage the full power of Apple Silicon for maximum performance.

## 📁 Files Overview

### 🎯 Setup Scripts

- **`setup_m3_max.sh`** - Complete automated setup script
- **`quick_start_m3max.sh`** - Quick start script for immediate use
- **`deploy_m3_max.sh`** - Production deployment with port conflict resolution

### 🐳 Docker Configuration

- **`docker-compose.m3max.yml`** - M3 Max optimized Docker Compose (development)
- **`docker-compose.m3-production.yml`** - Production deployment (auto-generated)
- **`ai_framework/Dockerfile.m3max`** - Multi-stage Dockerfile with M3 Max optimizations
- **`ai_framework/Dockerfile.m3-production`** - Production Dockerfile (auto-generated)

### 📦 Dependencies

- **`ai_framework/requirements-m3max.txt`** - M3 Max optimized Python packages
- **`M3_MAX_SETUP_GUIDE.md`** - Comprehensive setup documentation
- **`M3_MAX_DEPLOYMENT_GUIDE.md`** - Production deployment guide
- **`DEPLOYMENT_QUICK_REFERENCE.md`** - Quick reference for deployment

## 🚀 Quick Start

### Option 1: Quick Setup (Recommended for first-time users)

```bash
# Make script executable and run
chmod +x quick_start_m3max.sh
./quick_start_m3max.sh
```

This will:
- ✅ Install essential tools (Homebrew, Python, Redis, PostgreSQL)
- ✅ Setup AI Framework environment
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Apply M3 Max optimizations

### Option 2: Complete Setup (Full automation)

```bash
# Make script executable and run
chmod +x setup_m3_max.sh
./setup_m3_max.sh
```

This will:
- ✅ Install all development tools
- ✅ Setup monitoring (Prometheus, Grafana)
- ✅ Install Docker Desktop
- ✅ Configure all services
- ✅ Apply comprehensive optimizations

### Option 3: Production Deployment (Advanced users)

```bash
# Make script executable and run
chmod +x deploy_m3_max.sh
./deploy_m3_max.sh
```

This will:
- ✅ Resolve port conflicts automatically
- ✅ Handle SSH tunnel conflicts intelligently
- ✅ Create production-optimized configurations
- ✅ Setup load balancing with Nginx
- ✅ Configure production monitoring

### Option 4: Manual Setup

Follow the detailed guide in `M3_MAX_SETUP_GUIDE.md`

## 🎯 What Gets Installed

### Core Tools
- **Python 3.11** - Optimized for Apple Silicon
- **Homebrew** - Package manager
- **Docker Desktop** - Containerization
- **Node.js 18** - JavaScript runtime

### Database Services
- **Redis 7** - In-memory cache
- **PostgreSQL 15** - Relational database

### Monitoring
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards

### Development Tools
- **Poetry** - Python dependency management
- **Pre-commit** - Git hooks
- **Jupyter** - Interactive notebooks

## 🔧 M3 Max Optimizations

### Environment Variables
```bash
# CPU optimizations (16 cores)
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16
OPENBLAS_NUM_THREADS=16

# Python optimizations
PYTHONOPTIMIZE=1
PYTHONUNBUFFERED=1
```

### Resource Allocation
- **Development**: 4 CPU cores, 4GB RAM
- **Production**: 6 CPU cores, 8GB RAM
- **Database**: 2 CPU cores, 4GB RAM
- **Cache**: 1 CPU core, 3GB RAM
- **Monitoring**: 0.5 CPU core, 1GB RAM each

## 🐳 Docker Usage

### Development Mode
```bash
docker-compose -f docker-compose.m3max.yml up -d
```

### Production Mode
```bash
# Deploy first
./deploy_m3_max.sh

# Then start production
./start-m3-production.sh
```

### View Logs
```bash
# Development
docker-compose -f docker-compose.m3max.yml logs -f

# Production
docker-compose -f docker-compose.m3-production.yml logs -f
```

### Scale Services
```bash
# Development
docker-compose -f docker-compose.m3max.yml up -d --scale celery-worker=4

# Production
docker-compose -f docker-compose.m3-production.yml up -d --scale ai-framework-production=3
```

## 📊 Monitoring URLs

### Development Mode
- **AI Framework API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

### Production Mode
- **AI Framework API**: http://localhost:8100
- **API Documentation**: http://localhost:8100/docs
- **Nginx Load Balancer**: http://localhost:8080
- **Redis**: localhost:6380
- **PostgreSQL**: localhost:5434
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3001

## 🧪 Testing

### Run Tests
```bash
cd ai_framework
source venv/bin/activate
pytest
```

### Performance Testing
```bash
# Run optimization script
python scripts/optimize_m3_max.py

# Start framework (development)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start framework (production)
./start-m3-production.sh
```

### Health Checks
```bash
# Development health check
curl http://localhost:8000/health

# Production health check
./health-check-m3.sh
```

## 🔍 Troubleshooting

### Common Issues
1. **Port Conflicts**: Check what's using ports with `lsof -i :8000`
2. **Permission Issues**: Fix Docker permissions with `sudo chown $USER:docker /var/run/docker.sock`
3. **Memory Issues**: Monitor with `htop` and `vm_stat`
4. **Performance Issues**: Use `python -m cProfile` for profiling

### Health Checks
```bash
# Check all services
./health-check-m3.sh

# Check specific service
curl http://localhost:8000/health
redis-cli ping
pg_isready -h localhost
```

## 📈 Performance Expectations

On M3 Max with 48GB RAM:
- **Development Mode**: < 50ms API response, single worker
- **Production Mode**: < 25ms API response, 12 workers, 1000+ concurrent users
- **Database Queries**: < 10ms (dev) / < 5ms (prod)
- **ML Inference**: 2-5x faster than Intel Macs
- **Memory Usage**: Efficient 48GB utilization
- **CPU Usage**: Optimal 16-core utilization

## 🔄 Maintenance

### Regular Updates
```bash
# Update packages
brew update && brew upgrade
pip install --upgrade -r ai_framework/requirements-m3max.txt

# Update Docker images
docker-compose -f docker-compose.m3max.yml pull
docker-compose -f docker-compose.m3-production.yml pull
```

### Backup and Recovery
```bash
# Database backup
pg_dump -h localhost -U ai_user ai_framework > backup.sql

# Application backup
tar -czf backup_$(date +%Y%m%d).tar.gz ai_framework/ data/ logs/
```

## 📚 Documentation

- **Setup Guide**: `M3_MAX_SETUP_GUIDE.md` - Comprehensive setup instructions
- **Deployment Guide**: `M3_MAX_DEPLOYMENT_GUIDE.md` - Production deployment
- **Quick Reference**: `DEPLOYMENT_QUICK_REFERENCE.md` - Deployment commands
- **AI Framework**: `ai_framework/README.md` - Framework documentation
- **Architecture**: `docs/ARCHITECTURE.md` - System architecture

## 🆘 Support

- **Issues**: Check troubleshooting section above
- **Documentation**: Review setup and deployment guides
- **Health Checks**: Run `./health-check-m3.sh` for diagnostics
- **Community**: GitHub issues and discussions

## 🎯 Next Steps

1. **Quick Start**: `./quick_start_m3max.sh` (for development)
2. **Full Setup**: `./setup_m3_max.sh` (for complete environment)
3. **Production Deploy**: `./deploy_m3_max.sh` (for production)
4. **Explore API**: Visit http://localhost:8000/docs (dev) or http://localhost:8100/docs (prod)
5. **Monitor**: Use Grafana dashboards
6. **Scale**: Add more workers and services

## 🚀 Deployment Workflow

### Development → Production
```bash
# 1. Setup development environment
./setup_m3_max.sh

# 2. Test and develop
docker-compose -f docker-compose.m3max.yml up -d

# 3. Deploy to production
./deploy_m3_max.sh

# 4. Start production
./start-m3-production.sh

# 5. Monitor health
./health-check-m3.sh
```

---

**Ready to unleash the power of your M3 Max? 🚀**

*Choose your path:*
- **Quick Start**: `./quick_start_m3max.sh`
- **Full Setup**: `./setup_m3_max.sh`
- **Production**: `./deploy_m3_max.sh`
