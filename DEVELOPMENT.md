# Development Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Node.js 16+ and npm 8+
- Python 3.8+ (for AI scripts)
- Git

## Quick Start

1. **Clone and setup environment**
   ```bash
   git clone <repository-url>
   cd V1_Build
   cp .env.template .env
   # Edit .env with your actual credentials
   ```

2. **Install dependencies**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install Node.js dependencies
   npm install
   cd my-project && npm install
   ```

3. **Start services**
   ```bash
   # Run setup script
   ./setup.sh
   
   # Start n8n with Docker Compose
   docker-compose up -d
   ```

4. **Access n8n interface**
   - URL: http://localhost:5678
   - Username: admin
   - Password: (check your .env file)

## Development Workflow

### Code Quality

```bash
# Lint JavaScript code
npm run lint

# Format code
npm run format

# Check Python code
python -m py_compile gpt2_test.py mini_chat.py
```

### Testing

```bash
# Test n8n utilities
cd my-project
npm test

# Test Python scripts
python gpt2_test.py
python mini_chat.py
```

### Monitoring

```bash
# Check container health
docker-compose ps

# View logs
docker-compose logs -f n8n

# Run backup manually
./backup.sh
```

## Security Checklist

- [ ] Change default passwords in .env
- [ ] Never commit .env file
- [ ] Use strong API keys
- [ ] Enable HTTPS in production
- [ ] Regularly update dependencies
- [ ] Monitor access logs
- [ ] Implement rate limiting

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check Docker daemon is running
   - Verify port 5678 is available
   - Check .env file syntax

2. **n8n not accessible**
   - Wait for container to fully start (30-60 seconds)
   - Check firewall settings
   - Verify nginx configuration

3. **Workflow execution errors**
   - Check API credentials
   - Verify network connectivity
   - Review execution logs in n8n

### Performance Optimization

1. **Reduce polling frequency**
   - Change workflows from every minute to every 5+ minutes
   - Use webhooks instead of polling when possible

2. **Optimize Docker resources**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Adjust memory limits in docker-compose.yml
   ```

3. **Database optimization**
   - Enable execution data pruning
   - Use PostgreSQL for production
   - Set up proper indexes

## Environment Configuration

### Development
```bash
NODE_ENV=development
N8N_LOG_LEVEL=debug
```

### Production
```bash
NODE_ENV=production
N8N_LOG_LEVEL=info
N8N_SECURE_COOKIE=true
N8N_PROTOCOL=https
```

## Backup and Recovery

### Automatic Backups
```bash
# Setup crontab for automatic backups
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Manual Backup
```bash
./backup.sh
```

### Restore from Backup
```bash
# Stop n8n
docker-compose down

# Restore data
tar -xzf /backups/n8n_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Start n8n
docker-compose up -d
```

## API Integration Guidelines

### Rate Limiting
- Implement delays between API calls
- Use exponential backoff for retries
- Monitor API usage quotas

### Error Handling
- Always wrap API calls in try-catch
- Implement circuit breaker pattern
- Log errors for debugging

### Security
- Store API keys in environment variables
- Use OAuth when available
- Rotate keys regularly

## Deployment

### Production Checklist
- [ ] Use production .env configuration
- [ ] Enable SSL/TLS
- [ ] Setup monitoring and alerting
- [ ] Configure backup automation
- [ ] Implement log rotation
- [ ] Setup reverse proxy with rate limiting
- [ ] Enable container security scanning

### Scaling Considerations
- Use external PostgreSQL database
- Implement horizontal scaling with load balancer
- Use Redis for session storage
- Monitor resource usage and bottlenecks