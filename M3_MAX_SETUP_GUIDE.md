# 🚀 M3 Max AI Framework Setup Guide

## Overview

This guide provides comprehensive setup instructions for optimizing your AI Framework on a MacBook Pro M3 Max with 48GB RAM. The setup is designed to leverage the full power of Apple Silicon for maximum performance.

## 🖥️ System Requirements

- **Hardware**: MacBook Pro M3 Max (16-core CPU, 40-core GPU, 48GB RAM)
- **OS**: macOS 13+ (Ventura) or macOS 14+ (Sonoma)
- **Storage**: 1TB+ SSD recommended
- **Network**: High-speed internet for package downloads

## 🚀 Quick Start

### 1. Run the Setup Script

```bash
# Make the script executable
chmod +x setup_m3_max.sh

# Run the setup script
./setup_m3_max.sh
```

The script will automatically:
- ✅ Verify Apple Silicon compatibility
- ✅ Install Homebrew and development tools
- ✅ Setup Python 3.11 with M3 Max optimizations
- ✅ Install Docker Desktop
- ✅ Setup Redis and PostgreSQL
- ✅ Configure monitoring tools
- ✅ Install AI Framework dependencies
- ✅ Apply performance optimizations

### 2. Manual Setup (Alternative)

If you prefer manual setup, follow the sections below.

## 🛠️ Core Tools Installation

### Homebrew Setup

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add to PATH for M3 Max
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Python 3.11 Installation

```bash
# Install Python 3.11 (optimized for Apple Silicon)
brew install python@3.11

# Create symbolic links
ln -sf /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3
ln -sf /opt/homebrew/bin/pip3.11 /opt/homebrew/bin/pip3

# Upgrade pip
python3 -m pip install --upgrade pip

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile
```

### Docker Desktop

```bash
# Install Docker Desktop
brew install --cask docker

# Start Docker
open /Applications/Docker.app

# Wait for Docker daemon to be ready
while ! docker info &> /dev/null; do
    sleep 2
done
```

### Database Services

```bash
# Install Redis
brew install redis
brew services start redis

# Install PostgreSQL 15
brew install postgresql@15
brew services start postgresql@15

# Create symbolic links
ln -sf /opt/homebrew/opt/postgresql@15/bin/psql /opt/homebrew/bin/psql
ln -sf /opt/homebrew/opt/postgresql@15/bin/pg_ctl /opt/homebrew/bin/pg_ctl
```

### Monitoring Tools

```bash
# Install Prometheus
brew install prometheus
brew services start prometheus

# Install Grafana
brew install grafana
brew services start grafana
```

## 🐍 AI Framework Setup

### 1. Navigate to AI Framework Directory

```bash
cd ai_framework
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt

# Install M3 Max optimized dependencies
pip install -r requirements-m3max.txt

# Install additional performance packages
pip install \
    numpy \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    jupyter \
    ipykernel \
    torch \
    transformers \
    accelerate
```

### 4. Register Jupyter Kernel

```bash
# Register kernel for Jupyter
python -m ipykernel install --user --name=ai_framework --display-name="AI Framework (M3 Max)"
```

## 🔧 Performance Optimizations

### 1. Run M3 Max Optimization Script

```bash
# Navigate to scripts directory
cd scripts

# Run optimization script
python optimize_m3_max.py
```

### 2. Environment Variables

The setup script automatically creates a `.env` file with M3 Max optimizations:

```bash
# M3 Max Optimizations
PYTHONOPTIMIZE=1
PYTHONUNBUFFERED=1
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16
OPENBLAS_NUM_THREADS=16
```

### 3. Manual Environment Setup

```bash
# Create .env file
cat > .env << EOF
# AI Framework Environment Configuration
# Optimized for M3 Max MacBook Pro

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=ai_framework.db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_framework
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Development
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# M3 Max Optimizations
PYTHONOPTIMIZE=1
PYTHONUNBUFFERED=1
OMP_NUM_THREADS=16
MKL_NUM_THREADS=16
OPENBLAS_NUM_THREADS=16
EOF
```

## 🐳 Docker Setup

### 1. Build M3 Max Optimized Images

```bash
# Build development image
docker build -f Dockerfile.m3max --target development -t ai-framework:dev .

# Build production image
docker build -f Dockerfile.m3max --target production -t ai-framework:prod .

# Build Celery worker image
docker build -f Dockerfile.m3max --target celery -t ai-framework:celery .
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.m3max.yml up -d

# View logs
docker-compose -f docker-compose.m3max.yml logs -f

# Stop services
docker-compose -f docker-compose.m3max.yml down
```

### 3. Individual Service Management

```bash
# Start specific services
docker-compose -f docker-compose.m3max.yml up -d ai-framework postgres redis

# Scale services
docker-compose -f docker-compose.m3max.yml up -d --scale celery-worker=4

# View service status
docker-compose -f docker-compose.m3max.yml ps
```

## 🧪 Testing and Development

### 1. Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v
```

### 2. Development Tools

```bash
# Install pre-commit hooks
pre-commit install

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

### 3. Jupyter Notebook

```bash
# Start Jupyter
jupyter notebook

# Or start Jupyter Lab
jupyter lab
```

## 📊 Monitoring and Observability

### 1. Prometheus

- **URL**: http://localhost:9090
- **Purpose**: Metrics collection and alerting
- **Key Metrics**: API response times, database performance, system resources

### 2. Grafana

- **URL**: http://localhost:3000
- **Default Credentials**: admin/admin
- **Purpose**: Visualization and dashboards

### 3. Redis Monitoring

```bash
# Monitor Redis
redis-cli monitor

# Check Redis info
redis-cli info
```

### 4. PostgreSQL Monitoring

```bash
# Connect to PostgreSQL
psql -h localhost -U ai_user -d ai_framework

# Check database status
\dt
\du
```

## 🚀 Performance Tuning

### 1. Python Optimizations

```python
# In your Python code
import os
import multiprocessing

# Set M3 Max optimizations
os.environ['OMP_NUM_THREADS'] = str(multiprocessing.cpu_count())
os.environ['MKL_NUM_THREADS'] = str(multiprocessing.cpu_count())
os.environ['OPENBLAS_NUM_THREADS'] = str(multiprocessing.cpu_count())
```

### 2. Async/Await Usage

```python
import asyncio
import aiohttp

async def fetch_data(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses
```

### 3. Multiprocessing for CPU-Intensive Tasks

```python
from multiprocessing import Pool
import multiprocessing

def cpu_intensive_task(data):
    # Your CPU-intensive computation here
    return processed_data

# Use all M3 Max cores
with Pool(processes=multiprocessing.cpu_count()) as pool:
    results = pool.map(cpu_intensive_task, data_list)
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Docker Permission Issues

```bash
# Fix Docker permissions
sudo chown $USER:docker /var/run/docker.sock
```

#### 2. Port Conflicts

```bash
# Check what's using a port
lsof -i :8000

# Kill process using port
kill -9 <PID>
```

#### 3. Memory Issues

```bash
# Check memory usage
htop
vm_stat

# Monitor Python memory
python -m memory_profiler your_script.py
```

#### 4. Performance Issues

```bash
# Profile Python code
python -m cProfile -o profile.stats your_script.py

# Analyze profile
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### Health Checks

```bash
# Check all services
./scripts/health_check.sh

# Check specific service
curl http://localhost:8000/health
redis-cli ping
pg_isready -h localhost
```

## 📈 Performance Benchmarks

### Expected Performance on M3 Max

- **API Response Time**: < 50ms (95th percentile)
- **Database Queries**: < 10ms (simple queries)
- **ML Model Inference**: 2-5x faster than Intel Macs
- **Memory Usage**: Efficient utilization of 48GB RAM
- **CPU Utilization**: Optimal use of 16 cores

### Benchmarking Tools

```bash
# Install benchmarking tools
pip install pytest-benchmark locust

# Run benchmarks
pytest --benchmark-only

# Load testing
locust -f performance_tests/locustfile.py --host=http://localhost:8000
```

## 🔄 Maintenance

### Regular Updates

```bash
# Update Homebrew packages
brew update && brew upgrade

# Update Python packages
pip list --outdated
pip install --upgrade -r requirements-m3max.txt

# Update Docker images
docker-compose -f docker-compose.m3max.yml pull
```

### Backup and Recovery

```bash
# Backup database
pg_dump -h localhost -U ai_user ai_framework > backup.sql

# Backup Redis
redis-cli BGSAVE

# Backup application data
tar -czf ai_framework_backup_$(date +%Y%m%d).tar.gz data/ logs/ models/
```

## 📚 Additional Resources

### Documentation

- [AI Framework README](ai_framework/README.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs)

### Community

- GitHub Issues: [Report bugs and feature requests]
- Discussions: [Community discussions]
- Wiki: [Additional guides and tutorials]

### Support

- **Email**: support@ai-framework.com
- **Slack**: [Join our community]
- **Discord**: [Real-time support]

## 🎯 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run Examples**: Check the `examples/` directory
3. **Customize Agents**: Modify agent configurations
4. **Scale Up**: Add more workers and services
5. **Monitor Performance**: Use Grafana dashboards
6. **Contribute**: Submit pull requests and issues

---

**Happy coding on your M3 Max! 🚀**

*This setup guide is optimized for MacBook Pro M3 Max with 48GB RAM. For other configurations, adjust resource allocations accordingly.*
