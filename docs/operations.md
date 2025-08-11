# AI Business Engine Operations Guide

## Overview

This guide provides operational procedures for running, monitoring, and maintaining the AI Business Engine in both development and production environments.

## Quick Start

### 1. Start All Services
```bash
# Start platform infrastructure
cd platform/infra
docker-compose up -d

# Start backend
cd ../../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend
cd ../apps/web
npm run dev

# Start manager orchestrator
cd ../../platform/orchestration/manager
REDIS_URL=redis://localhost:6379 python consumer.py
```

### 2. Verify Health
```bash
# Backend health
curl http://localhost:8000/health

# Manager health
curl http://localhost:8080/health

# Metrics
curl http://localhost:8000/metrics
```

### 3. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## Key Management

### JWT Secret Rotation

#### 1. Generate New Secret
```bash
# Generate new secret
openssl rand -hex 32

# Update environment variable
export JWT_SECRET=new-secret-here
```

#### 2. Update Configuration
```bash
# Backend .env
JWT_SECRET=new-secret-here

# Restart backend service
pkill -f "uvicorn app.main:app"
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 3. Verify Rotation
```bash
# Test with old token (should fail)
curl -H "Authorization: Bearer old-token" http://localhost:8000/life/health/wellness_daily

# Test with new token (should work)
curl -H "Authorization: Bearer new-token" http://localhost:8000/life/health/wellness_daily
```

### Admin Token Management
```bash
# Mint new admin token
cd backend
python scripts/mint_jwt.py admin@example.com --scopes admin.*,life.read,runs.write

# Use token
export ADMIN_TOKEN="your-token-here"
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/admin/status
```

## Redis Stream Management

### 1. Check Stream Health
```bash
# Connect to Redis
redis-cli

# Check stream info
XINFO STREAM events
XINFO GROUPS events
XINFO CONSUMERS events manager_group
```

### 2. Recover Stuck Streams

#### Identify Stuck Consumers
```bash
# Check consumer lag
XINFO GROUPS events

# Check pending messages
XPENDING events manager_group
```

#### Reset Consumer Group
```bash
# Reset to beginning of stream
XGROUP SETID events manager_group 0

# Or reset to specific message ID
XGROUP SETID events manager_group 1234567890-0
```

#### Clear Pending Messages
```bash
# Claim pending messages
XCLAIM events manager_group manager_1 0 1234567890-0

# Or acknowledge all pending
XPENDING events manager_group - + 10 manager_1
```

### 3. Dead Letter Queue Management

#### Check DLQ
```bash
# View DLQ contents
XREAD COUNT 10 STREAMS automation.dlq 0

# Check DLQ size
XLEN automation.dlq
```

#### Reprocess DLQ Messages
```bash
# Move messages back to main stream
XADD events * data "reprocessed-message"
XDEL automation.dlq message-id
```

## Database Operations

### 1. Schema Management
```bash
# Check current schema
cd backend
python -c "from app.db import engine; from app.models import Base; Base.metadata.create_all(engine)"

# Run migrations
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### 2. Data Recovery
```bash
# Backup database
sqlite3 dev.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Restore from backup
sqlite3 dev.db ".restore backup_20241201_120000.db"
```

### 3. Performance Monitoring
```bash
# Check slow queries
sqlite3 dev.db "PRAGMA stats;"

# Analyze table performance
sqlite3 dev.db "ANALYZE;"
```

## Monitoring & Alerting

### 1. Prometheus Metrics

#### Key Metrics to Monitor
- **API Performance**: `api_request_latency_seconds`
- **Error Rate**: `api_errors_total`
- **Redis Health**: `redis_stream_lag_seconds`
- **Manager Health**: `manager_planning_duration_seconds`

#### Check Metrics
```bash
# Get current metrics
curl http://localhost:8000/metrics

# Query specific metric
curl "http://localhost:9090/api/v1/query?query=rate(api_requests_total[5m])"
```

### 2. Grafana Dashboards

#### Dashboard Access
- **API SLO**: http://localhost:3001/d/api-slo
- **Orchestrator**: http://localhost:3001/d/orchestrator
- **Manager Health**: http://localhost:3001/d/manager-health

#### Create Alerts
```yaml
# Example alert rule
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate detected"
```

### 3. Health Check Endpoints

#### Backend Health
```bash
# Basic health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/readyz

# Metrics endpoint
curl http://localhost:8000/metrics
```

#### Manager Health
```bash
# Manager status
curl http://localhost:8080/health

# Manager metrics
curl http://localhost:8080/metrics
```

## Troubleshooting

### 1. Common Issues

#### Backend Won't Start
```bash
# Check dependencies
pip install -r requirements.txt

# Check environment variables
echo $JWT_SECRET
echo $DATABASE_URL

# Check port availability
lsof -i :8000
```

#### Manager Consumer Issues
```bash
# Check Redis connection
redis-cli ping

# Check consumer logs
cd platform/orchestration/manager
REDIS_URL=redis://localhost:6379 python consumer.py

# Reset consumer group if needed
redis-cli XGROUP SETID events manager_group 0
```

#### Frontend Issues
```bash
# Check API connectivity
curl http://localhost:8000/health

# Check environment variables
echo $NEXT_PUBLIC_API_URL

# Clear Next.js cache
rm -rf .next
npm run dev
```

### 2. Performance Issues

#### High Latency
```bash
# Check API metrics
curl http://localhost:8000/metrics | grep latency

# Check database performance
sqlite3 dev.db "PRAGMA stats;"

# Check Redis performance
redis-cli INFO stats
```

#### Memory Issues
```bash
# Check process memory
ps aux | grep python
ps aux | grep node

# Check Docker memory
docker stats

# Restart services if needed
docker-compose restart
```

### 3. Security Issues

#### Authentication Failures
```bash
# Check JWT secret
echo $JWT_SECRET

# Verify token format
python -c "import jwt; print(jwt.decode('your-token', options={'verify_signature': False})"

# Check scope requirements
curl -H "Authorization: Bearer your-token" http://localhost:8000/runs
```

#### CORS Issues
```bash
# Check allowed origins
echo $ALLOWED_ORIGINS

# Test CORS headers
curl -H "Origin: http://localhost:3000" -v http://localhost:8000/health
```

## Backup & Recovery

### 1. Regular Backups
```bash
# Database backup
sqlite3 dev.db ".backup backup_$(date +%Y%m%d).db"

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env platform/infra/

# Log backup
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### 2. Disaster Recovery
```bash
# Stop all services
docker-compose down
pkill -f "uvicorn app.main:app"
pkill -f "python consumer.py"

# Restore from backup
sqlite3 dev.db ".restore backup_20241201.db"
cp config_backup_20241201.tar.gz ./
tar -xzf config_backup_20241201.tar.gz

# Restart services
docker-compose up -d
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd ../platform/orchestration/manager && REDIS_URL=redis://localhost:6379 python consumer.py &
```

## Maintenance Procedures

### 1. Daily Checks
- [ ] Check service health endpoints
- [ ] Review error logs
- [ ] Monitor dashboard metrics
- [ ] Verify Redis stream health

### 2. Weekly Tasks
- [ ] Review performance metrics
- [ ] Check disk space usage
- [ ] Update dependencies
- [ ] Review security logs

### 3. Monthly Tasks
- [ ] Rotate JWT secrets
- [ ] Review and update alerts
- [ ] Performance optimization
- [ ] Security audit

## Emergency Procedures

### 1. Service Outage
```bash
# Immediate response
docker-compose restart
pkill -f "uvicorn app.main:app"
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Check logs
docker-compose logs -f
tail -f backend/logs/app.log
```

### 2. Data Corruption
```bash
# Stop all services
docker-compose down
pkill -f "uvicorn app.main:app"

# Restore from backup
sqlite3 dev.db ".restore latest_backup.db"

# Verify data integrity
sqlite3 dev.db "PRAGMA integrity_check;"

# Restart services
docker-compose up -d
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### 3. Security Breach
```bash
# Immediate actions
export JWT_SECRET=new-emergency-secret
pkill -f "uvicorn app.main:app"

# Restart with new secret
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Review access logs
tail -f logs/access.log | grep suspicious_ip
```

## Contact Information

### On-Call Engineer
- **Primary**: [Primary Engineer Name] - [Phone/Email]
- **Secondary**: [Secondary Engineer Name] - [Phone/Email]

### Escalation Path
1. On-call engineer (immediate)
2. Team lead (within 30 minutes)
3. Engineering manager (within 1 hour)
4. CTO (within 2 hours)

### External Dependencies
- **Redis**: Managed by platform team
- **Database**: Managed by DBA team
- **Monitoring**: Managed by SRE team

---

**Last Updated**: 2024-12-01
**Version**: v0.85.0-pre
**Next Review**: 2024-12-15
