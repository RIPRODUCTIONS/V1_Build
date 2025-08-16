# 🚀 Autonomous Task Solver System - Deployment Guide

This guide provides comprehensive instructions for deploying the Autonomous Task Solver System in various environments.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Configuration](#configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Troubleshooting](#troubleshooting)
9. [Scaling](#scaling)

## 🔧 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS 12+, or Windows 11 with WSL2
- **Python**: 3.11 or higher
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: Minimum 10GB free space
- **CPU**: 2+ cores recommended

### Software Dependencies
- Python 3.11+
- pip (Python package manager)
- Git
- Docker & Docker Compose (for containerized deployment)
- Redis (for task queues and caching)
- PostgreSQL (optional, for production)

### AI Model Access
- OpenAI API key (for GPT models)
- Anthropic API key (for Claude models)
- Ollama (for local models)
- Access to Hugging Face models

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd autonomous_system
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### 3. Run the Demo
```bash
# Start the system with demo tasks
python quick_start.py
```

The demo will:
- Start the autonomous system
- Create sample tasks
- Monitor performance
- Show results and recommendations

## 💻 Local Development

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configuration
```bash
# Copy configuration template
cp config/config.yaml config/config.local.yaml

# Edit configuration for local development
nano config/config.local.yaml
```

### 3. Start Development Mode
```bash
# Start the system in development mode
python -m autonomous_system.autonomous_orchestrator --config config/config.local.yaml
```

### 4. Development Tools
```bash
# Run tests
pytest tests/

# Code formatting
black autonomous_system/
isort autonomous_system/

# Linting
flake8 autonomous_system/
mypy autonomous_system/
```

## 🐳 Docker Deployment

### 1. Build the Image
```bash
# Build production image
docker build -f docker/Dockerfile -t autonomous-system:latest .

# Build development image
docker build -f docker/Dockerfile -t autonomous-system:dev --target development .
```

### 2. Run with Docker Compose
```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Start specific profiles
docker-compose -f docker/docker-compose.yml --profile dev up -d
docker-compose -f docker/docker-compose.yml --profile production up -d
docker-compose -f docker/docker-compose.yml --profile monitoring up -d
```

### 3. Service Ports
- **Main System**: http://localhost:8000
- **Development**: http://localhost:8001
- **Monitoring**: http://localhost:8080
- **WebSocket**: ws://localhost:9000
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **ChromaDB**: http://localhost:8002
- **Flower**: http://localhost:5555

### 4. Docker Commands
```bash
# View logs
docker-compose -f docker/docker-compose.yml logs -f autonomous-system

# Stop services
docker-compose -f docker/docker-compose.yml down

# Restart specific service
docker-compose -f docker/docker-compose.yml restart autonomous-system

# Scale workers
docker-compose -f docker/docker-compose.yml up -d --scale celery-worker=3
```

## 🏭 Production Deployment

### 1. Environment Configuration
```bash
# Create production environment file
cp config/.env.example .env.production

# Edit production settings
nano .env.production
```

### 2. Production Docker Compose
```bash
# Start production stack
docker-compose -f docker/docker-compose.yml --profile production up -d

# Start with monitoring
docker-compose -f docker/docker-compose.yml --profile production --profile monitoring up -d
```

### 3. Reverse Proxy (Nginx)
```bash
# Start with Nginx
docker-compose -f docker/docker-compose.yml --profile production up -d

# Access via Nginx
curl http://localhost
```

### 4. SSL/TLS Configuration
```bash
# Generate SSL certificates
mkdir -p docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/nginx.key \
  -out docker/nginx/ssl/nginx.crt

# Restart Nginx
docker-compose -f docker/docker-compose.yml restart nginx
```

### 5. Database Migration
```bash
# For PostgreSQL migrations
docker-compose -f docker/docker-compose.yml exec autonomous-system \
  python -m alembic upgrade head
```

## ⚙️ Configuration

### Configuration Files
- `config/config.yaml` - Main configuration
- `config/.env.example` - Environment variables template
- `docker/docker-compose.yml` - Docker services
- `docker/Dockerfile` - Container build instructions

### Key Configuration Sections

#### AI Models
```yaml
ai_models:
  openai:
    api_key: "${OPENAI_API_KEY}"
    models: ["gpt-4", "gpt-4-turbo"]
    default_model: "gpt-4"
```

#### Task Detection
```yaml
task_detection:
  email:
    enabled: true
    imap_server: "${IMAP_SERVER}"
    username: "${EMAIL_USERNAME}"
    password: "${EMAIL_PASSWORD}"
```

#### System Monitoring
```yaml
system_monitoring:
  thresholds:
    cpu_usage:
      warning: 70.0
      critical: 90.0
    memory_usage:
      warning: 80.0
      critical: 95.0
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
POSTGRES_PASSWORD=your_db_password
REDIS_PASSWORD=your_redis_password

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
```

## 📊 Monitoring & Observability

### 1. System Health
```bash
# Check system status
curl http://localhost:8000/health

# View system metrics
curl http://localhost:8000/metrics
```

### 2. Grafana Dashboards
- **System Overview**: http://localhost:3000/d/system-overview
- **Performance Metrics**: http://localhost:3000/d/performance
- **Task Execution**: http://localhost:3000/d/tasks
- **System Health**: http://localhost:3000/d/health

### 3. Prometheus Metrics
```bash
# View available metrics
curl http://localhost:9090/api/v1/label/__name__/values

# Query specific metrics
curl "http://localhost:9090/api/v1/query?query=autonomous_system_tasks_total"
```

### 4. Logs
```bash
# View application logs
docker-compose -f docker/docker-compose.yml logs -f autonomous-system

# View specific component logs
docker-compose -f docker/docker-compose.yml logs -f celery-worker
docker-compose -f docker/docker-compose.yml logs -f postgres
```

### 5. Health Checks
```bash
# Run health check script
./scripts/healthcheck.sh check

# Show health status
./scripts/healthcheck.sh status
```

## 🔍 Troubleshooting

### Common Issues

#### 1. System Won't Start
```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs autonomous-system

# Check configuration
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# Verify dependencies
pip list | grep autonomous
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
docker-compose -f docker/docker-compose.yml exec autonomous-system \
  python -c "import sqlite3; sqlite3.connect('/app/data/databases/autonomous_system.db')"

# Check PostgreSQL
docker-compose -f docker/docker-compose.yml exec postgres \
  psql -U autonomous_user -d autonomous_system -c "SELECT 1"
```

#### 3. AI Model Issues
```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Test Ollama
curl http://localhost:11434/api/tags
```

#### 4. Performance Issues
```bash
# Check system resources
docker stats

# Monitor task queue
curl http://localhost:5555

# Check Redis
docker-compose -f docker/docker-compose.yml exec redis redis-cli info
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Start with debug
python -m autonomous_system.autonomous_orchestrator --debug
```

## 📈 Scaling

### 1. Horizontal Scaling
```bash
# Scale workers
docker-compose -f docker/docker-compose.yml up -d --scale celery-worker=5

# Scale API instances
docker-compose -f docker/docker-compose.yml up -d --scale autonomous-system=3
```

### 2. Load Balancing
```bash
# Update Nginx configuration for multiple instances
upstream autonomous_backend {
    server autonomous-system:8000;
    server autonomous-system:8001;
    server autonomous-system:8002;
}
```

### 3. Database Scaling
```bash
# Use PostgreSQL for production
docker-compose -f docker/docker-compose.yml up -d postgres

# Configure connection pooling
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30
```

### 4. Cache Scaling
```bash
# Redis cluster
docker-compose -f docker/docker-compose.yml up -d redis-cluster

# Configure multiple Redis instances
export REDIS_CLUSTER_NODES="redis-1:6379,redis-2:6379,redis-3:6379"
```

## 🚀 Advanced Deployment

### 1. Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f deploy/k8s/

# Check deployment status
kubectl get pods -l app=autonomous-system
kubectl get services -l app=autonomous-system
```

### 2. Helm Charts
```bash
# Install with Helm
helm install autonomous-system ./deploy/helm/

# Upgrade deployment
helm upgrade autonomous-system ./deploy/helm/
```

### 3. CI/CD Pipeline
```bash
# Build and test
make build test

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-production
```

### 4. Infrastructure as Code
```bash
# Deploy infrastructure
cd infra/terraform
terraform init
terraform plan
terraform apply

# Deploy with Terragrunt
cd infra/terragrunt/dev
terragrunt plan
terragrunt apply
```

## 📚 Additional Resources

### Documentation
- [Architecture Guide](ARCHITECTURE.md)
- [API Reference](API.md)
- [Configuration Reference](CONFIGURATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Support
- [GitHub Issues](https://github.com/your-repo/issues)
- [Discord Community](https://discord.gg/your-community)
- [Email Support](mailto:support@yourdomain.com)

### Contributing
- [Development Guide](DEVELOPMENT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

**🎉 Congratulations!** You've successfully deployed the Autonomous Task Solver System.

The system is now running autonomously and will:
- Detect tasks from multiple sources
- Classify and prioritize them intelligently
- Execute tasks with minimal human intervention
- Learn from outcomes to improve performance
- Monitor system health and provide alerts
- Scale automatically based on demand

For ongoing operations, monitor the system through:
- Grafana dashboards
- System logs
- Health check endpoints
- Performance metrics

Happy automating! 🤖✨
