# 🚀 M3 Max Deployment Quick Reference

## ⚡ One-Command Deployment

```bash
./deploy_m3_max.sh
```

## 📋 Pre-Deployment Checklist

- [ ] Docker Desktop running
- [ ] 16GB+ RAM available
- [ ] Ports 8100, 5434, 6380, 9091, 3001, 8080 free
- [ ] SSH tunnels closed (if any)

## 🔧 Port Mapping

| Service | Port | URL |
|---------|------|-----|
| AI Framework | 8100 | http://localhost:8100 |
| PostgreSQL | 5434 | localhost:5434 |
| Redis | 6380 | localhost:6380 |
| Prometheus | 9091 | http://localhost:9091 |
| Grafana | 3001 | http://localhost:3001 |
| Nginx | 8080 | http://localhost:8080 |

## 🚀 Quick Commands

### **Start Production**
```bash
./start-m3-production.sh
```

### **Health Check**
```bash
./health-check-m3.sh
```

### **View Logs**
```bash
docker-compose -f docker-compose.m3-production.yml logs -f
```

### **Stop Services**
```bash
docker-compose -f docker-compose.m3-production.yml down
```

### **Restart Services**
```bash
docker-compose -f docker-compose.m3-production.yml restart
```

## 🔍 Troubleshooting

### **Port Conflicts**
```bash
# Check what's using port
lsof -i :8100

# Kill process
sudo lsof -ti:8100 | xargs kill -9
```

### **Docker Issues**
```bash
# Check Docker status
docker info

# Clean up Docker
docker system prune -a
```

### **Service Not Starting**
```bash
# Check container logs
docker-compose -f docker-compose.m3-production.yml logs ai-framework-production

# Check container status
docker-compose -f docker-compose.m3-production.yml ps
```

## 📊 Monitoring URLs

- **Main App**: http://localhost:8100
- **API Docs**: http://localhost:8100/docs
- **Grafana**: http://localhost:3001 (admin/password from .env)
- **Prometheus**: http://localhost:9091
- **Nginx**: http://localhost:8080

## 🎯 Performance Targets

- **Response Time**: < 25ms (95th percentile)
- **Throughput**: 10,000+ req/sec
- **Concurrent Users**: 1000+
- **Memory Usage**: < 80% of 48GB

## 🔄 Update Commands

### **Update Containers**
```bash
docker-compose -f docker-compose.m3-production.yml pull
docker-compose -f docker-compose.m3-production.yml up -d
```

### **Rebuild Images**
```bash
docker-compose -f docker-compose.m3-production.yml build --no-cache
docker-compose -f docker-compose.m3-production.yml up -d
```

## 📁 Key Files

- `deploy_m3_max.sh` - Main deployment script
- `start-m3-production.sh` - Production startup
- `health-check-m3.sh` - Health monitoring
- `docker-compose.m3-production.yml` - Production services
- `.env.m3-production` - Production environment

## 🆘 Emergency Commands

### **Force Stop Everything**
```bash
docker-compose -f docker-compose.m3-production.yml down --remove-orphans
docker system prune -a --force
```

### **Reset to Development**
```bash
docker-compose -f docker-compose.m3max.yml up -d
```

---

**Need help? Run `./health-check-m3.sh` for diagnostics! 🏥**
