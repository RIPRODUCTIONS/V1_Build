# 🚀 AI Business Engine Operations Guide

**Your complete guide to running, monitoring, and maintaining the AI Business Engine in
production.**

## 📋 Table of Contents

1. [Daily Operations](#daily-operations)
2. [Security & Key Management](#security--key-management)
3. [Monitoring & Alerting](#monitoring--alerting)
4. [Troubleshooting](#troubleshooting)
5. [Recovery Procedures](#recovery-procedures)
6. [Performance Tuning](#performance-tuning)
7. [Backup & Disaster Recovery](#backup--disaster-recovery)

## 🏃‍♂️ Daily Operations

### Health Check Routine

```bash
# 1. Check system health
curl http://localhost:8000/health
curl http://localhost:8000/health/manager

# 2. Check metrics
curl http://localhost:8000/metrics | grep -E "(up|error|latency)"

# 3. Check recent runs
curl http://localhost:8000/runs?limit=5

# 4. Check queue depths
curl http://localhost:8000/metrics | grep queue_depth
```

### Key Metrics to Monitor

- **API Latency**: p95 < 300ms
- **Error Rate**: < 1% (4xx/5xx responses)
- **Redis Stream Lag**: < 60 seconds
- **Manager Health**: Status = "healthy"
- **Queue Depth**: < 100 items per stream

## 🔐 Security & Key Management

### JWT Secret Rotation

```bash
# 1. Generate new secret
openssl rand -hex 32

# 2. Update environment
export JWT_SECRET="new-secret-here"

# 3. Restart backend services
cd backend
pkill -f uvicorn
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# 4. Verify new tokens work
python scripts/mint_jwt.py --scopes "runs.read"
```

### API Key Rotation

```bash
# 1. Check current keys in use
grep -r "API_KEY" backend/app/

# 2. Generate new keys
openssl rand -hex 16

# 3. Update environment variables
export GOOGLE_API_KEY="new-key"
export REDDIT_API_KEY="new-key"

# 4. Restart services
docker-compose restart backend
```

### Scope Management

```bash
# View current user scopes
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me

# Generate token with specific scopes
python scripts/mint_jwt.py --scopes "runs.read,runs.write,departments.read"

# Revoke token (if using Redis for token storage)
redis-cli DEL "token:$TOKEN_HASH"
```

## 📊 Monitoring & Alerting

### Grafana Dashboard Setup

```bash
# 1. Access Grafana
open http://localhost:3001
# Default: admin/admin

# 2. Import dashboards
# - AI Business Engine Dashboard: deploy/observability/grafana/dashboard_ai_business_engine.json
# - API SLO Dashboard: deploy/observability/grafana/dashboard_api_slo.json

# 3. Set up alerts
# - High latency: p95 > 1s for 5 minutes
# - High error rate: > 5% for 2 minutes
# - Manager down: status != "healthy"
```

### Prometheus Alerts

```yaml
# Example alert rules
groups:
  - name: ai-business-engine
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(api_request_latency_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'API latency is high'
          description: 'P95 latency is {{ $value }}s'

      - alert: ManagerDown
        expr: up{job="manager"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: 'Manager orchestrator is down'
```

### Log Monitoring

```bash
# Check application logs
tail -f backend/logs/app.log | grep -E "(ERROR|WARN|CRITICAL)"

# Check system logs
journalctl -u ai-business-engine -f

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. High API Latency

```bash
# Check current latency
curl http://localhost:8000/metrics | grep "api_request_latency_seconds"

# Check database performance
curl http://localhost:8000/metrics | grep "db_connection_pool"

# Check Redis performance
redis-cli --latency
redis-cli --latency-history
```

**Solutions:**

- Increase database connection pool size
- Add Redis connection pooling
- Enable query result caching
- Check for N+1 queries

#### 2. Redis Stream Lag

```bash
# Check stream lag
curl http://localhost:8000/metrics | grep "redis_stream_lag_seconds"

# Check consumer groups
redis-cli XINFO GROUPS automation.events
redis-cli XINFO CONSUMERS automation.events manager
```

**Solutions:**

- Increase consumer concurrency
- Check consumer health
- Restart stuck consumers
- Scale consumer instances

#### 3. Manager Orchestrator Issues

```bash
# Check manager health
curl http://localhost:8000/health/manager

# Check manager logs
tail -f platform/orchestration/manager/manager.log

# Check Redis connection
redis-cli PING
```

**Solutions:**

- Restart manager service
- Check Redis connectivity
- Verify event stream health
- Check consumer group status

## 🔄 Recovery Procedures

### Stuck Stream Recovery

```bash
# 1. Identify stuck streams
redis-cli XINFO STREAM automation.events
redis-cli XINFO GROUPS automation.events

# 2. Check pending messages
redis-cli XPENDING automation.events manager

# 3. Claim stuck messages
redis-cli XCLAIM automation.events manager consumer2 3600000 1234567890-0

# 4. Reset consumer group (if necessary)
redis-cli XGROUP DELCONSUMER automation.events manager consumer1
redis-cli XGROUP SETID automation.events manager 0
```

### Dead Letter Queue (DLQ) Recovery

```bash
# 1. Check DLQ contents
redis-cli XRANGE automation.dlq - + COUNT 10

# 2. Analyze failed events
redis-cli XINFO STREAM automation.dlq

# 3. Reprocess specific events
redis-cli XREAD COUNT 1 STREAMS automation.dlq 0

# 4. Move back to main stream
redis-cli XADD automation.events * event_type "automation.run.requested" ...
```

### Database Recovery

```bash
# 1. Check database health
curl http://localhost:8000/readyz

# 2. Check connection pool
curl http://localhost:8000/metrics | grep "db_connections"

# 3. Restart database (if using Docker)
docker-compose restart postgres

# 4. Run migrations
cd backend
alembic upgrade head
```

### Service Recovery

```bash
# 1. Restart backend
cd backend
pkill -f uvicorn
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# 2. Restart frontend
cd apps/web
pkill -f "next dev"
npm run dev

# 3. Restart manager
cd platform/orchestration/manager
pkill -f consumer.py
python consumer.py
```

## ⚡ Performance Tuning

### Backend Optimization

```python
# 1. Increase worker processes
uvicorn app.main:app --workers 4 --port 8000

# 2. Enable connection pooling
DATABASE_URL="postgresql://user:pass@localhost/db?pool_size=20&max_overflow=30"

# 3. Enable Redis connection pooling
REDIS_URL="redis://localhost:6379?max_connections=50"
```

### Frontend Optimization

```bash
# 1. Enable production build
npm run build
npm start

# 2. Enable compression
# Add to next.config.mjs
const nextConfig = {
  compress: true,
  poweredByHeader: false,
}
```

### Redis Optimization

```bash
# 1. Check Redis memory usage
redis-cli INFO memory

# 2. Enable persistence
redis-cli CONFIG SET save "900 1 300 10 60 10000"

# 3. Set memory limits
redis-cli CONFIG SET maxmemory "2gb"
redis-cli CONFIG SET maxmemory-policy "allkeys-lru"
```

## 💾 Backup & Disaster Recovery

### Database Backup

```bash
# SQLite backup
cp backend/dev.db backend/dev.db.backup.$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h localhost -U username -d ai_business_engine > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
pg_dump -h localhost -U username -d ai_business_engine > $BACKUP_DIR/db_backup.sql
cp -r backend/artifacts $BACKUP_DIR/
tar -czf $BACKUP_DIR/backup.tar.gz $BACKUP_DIR/
```

### Configuration Backup

```bash
# Backup environment files
cp .env .env.backup.$(date +%Y%m%d)

# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  backend/app/core/config.py \
  deploy/ \
  docker-compose.yml
```

### Recovery Procedures

```bash
# 1. Restore database
psql -h localhost -U username -d ai_business_engine < backup_20241201.sql

# 2. Restore configuration
tar -xzf config_backup_20241201.tar.gz

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. Verify recovery
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## 🧪 Testing & Validation

### Load Testing

```bash
# Using k6
k6 run tools/k6/life_smoke.js

# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

### Chaos Testing

```bash
# Kill Redis
docker-compose stop redis
# Wait 30 seconds
docker-compose start redis

# Kill database
docker-compose stop postgres
# Wait 60 seconds
docker-compose start postgres

# Kill manager
pkill -f consumer.py
# Wait 30 seconds
python consumer.py
```

## 📞 Emergency Contacts

### Escalation Path

1. **Level 1**: Automated monitoring and self-healing
2. **Level 2**: Manual intervention and recovery procedures
3. **Level 3**: System administrator (you)

### Emergency Procedures

```bash
# 1. Stop all services
docker-compose down
pkill -f "uvicorn\|next\|python.*consumer"

# 2. Check system resources
df -h
free -h
top

# 3. Restart core services
docker-compose up -d redis postgres
cd backend && python -m uvicorn app.main:app --port 8000
cd apps/web && npm run dev

# 4. Verify recovery
curl http://localhost:8000/health
```

---

**Remember**: This is your personal AI business engine. Keep it running smoothly, and it will keep
your business running autonomously! 🚀
