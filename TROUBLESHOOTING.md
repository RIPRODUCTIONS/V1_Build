# Troubleshooting Guide

## Common Issues and Solutions

### 1. Python Scripts Not Working

**Problem**: `ModuleNotFoundError: No module named 'transformers'`

**Solution**:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install manually
pip install transformers torch
```

**Alternative**: Use virtual environment
```bash
python3 -m venv n8n_env
source n8n_env/bin/activate  # On Windows: n8n_env\Scripts\activate
pip install -r requirements.txt
```

### 2. API Key Issues

**Problem**: Weather/GitHub APIs returning 401 Unauthorized

**Solution**:
1. Copy `.env.template` to `.env.local`
2. Update with your actual API keys:
   ```bash
   OPENWEATHER_API_KEY=your_actual_api_key
   GITHUB_ACCESS_TOKEN=your_github_token
   ```
3. Restart n8n: `docker-compose restart`

**Get API Keys**:
- OpenWeatherMap: https://openweathermap.org/api
- GitHub: Settings → Developer settings → Personal access tokens

### 3. n8n Not Starting

**Problem**: `docker-compose up -d` fails

**Solutions**:
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check ports
sudo netstat -tulpn | grep 5678

# View logs
docker-compose logs n8n

# Reset and restart
docker-compose down
docker-compose up -d
```

### 4. File Permissions Issues

**Problem**: Permission denied errors

**Solutions**:
```bash
# Fix directory permissions
chmod -R 755 workflows/ data/

# Fix ownership (if needed)
sudo chown -R $USER:$USER workflows/ data/

# For Docker volumes
docker-compose down
docker volume rm v1_build_n8n_data
docker-compose up -d
```

### 5. Workflow Import Errors

**Problem**: JSON syntax errors when importing

**Solutions**:
1. Validate JSON files:
   ```bash
   # Check JSON syntax
   cat workflows/email/email_automation.json | python -m json.tool
   ```

2. Common fixes:
   - Remove trailing commas
   - Check quote marks
   - Verify bracket matching

### 6. Email Notifications Not Working

**Problem**: Email sends failing

**Solutions**:
1. Check SMTP credentials in n8n
2. Test email configuration:
   - Gmail: Enable 2FA and use App Password
   - Outlook: Enable SMTP access
3. Check firewall/network restrictions

### 7. Database Connection Issues

**Problem**: PostgreSQL node failures

**Solutions**:
```bash
# Check database is running
docker ps | grep postgres

# Test connection
psql -h localhost -U username -d database

# Check credentials in n8n Settings → Credentials
```

### 8. GitHub API Rate Limits

**Problem**: API rate limit exceeded

**Solutions**:
1. Use authenticated requests (GitHub token)
2. Add delays between requests
3. Cache responses when possible
4. Use webhooks instead of polling

### 9. Slack Integration Issues

**Problem**: Slack messages not sending

**Solutions**:
1. Check Slack app configuration
2. Verify webhook URL
3. Test with curl:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
   --data '{"text":"Test message"}' \
   YOUR_WEBHOOK_URL
   ```

### 10. File Monitoring Not Working

**Problem**: File triggers not activating

**Solutions**:
1. Check file paths in workflow
2. Verify directory permissions
3. Use absolute paths
4. Test with manual file copy

## Debugging Tips

### Enable Debug Mode
1. In n8n: Settings → Debug → Enable
2. Check execution logs
3. Use "Execute Node" for testing

### Check Logs
```bash
# n8n logs
docker-compose logs -f n8n

# System logs
tail -f /var/log/syslog | grep n8n
```

### Test Individual Components

**Test Python Scripts**:
```bash
cd /path/to/project
python3 gpt2_test.py
python3 mini_chat.py
```

**Test Node.js Project**:
```bash
cd my-project
npm test
npm start
```

**Test Docker Setup**:
```bash
docker-compose config  # Validate compose file
docker-compose ps      # Check running services
```

### Validate Configuration

**Check Environment Variables**:
```bash
# In n8n container
docker exec -it v1_build_n8n_1 env | grep -i api
```

**Test API Endpoints**:
```bash
# Test OpenWeatherMap
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_API_KEY"

# Test GitHub
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

## Performance Issues

### High CPU Usage
1. Reduce workflow frequency
2. Add delays between API calls
3. Use batch processing
4. Optimize database queries

### Memory Issues
1. Limit parallel executions
2. Clear old execution data
3. Restart n8n regularly
4. Monitor Docker memory usage

### Network Timeouts
1. Increase timeout values
2. Add retry mechanisms
3. Use connection pooling
4. Check network stability

## Getting Help

1. **Documentation**: https://docs.n8n.io/
2. **Community**: https://community.n8n.io/
3. **GitHub Issues**: https://github.com/n8n-io/n8n/issues
4. **Discord**: n8n Community Discord

## Emergency Recovery

### Reset Everything
```bash
# Stop all services
docker-compose down

# Remove volumes (CAUTION: This deletes all data)
docker volume rm v1_build_n8n_data

# Clean restart
docker-compose up -d
```

### Backup/Restore
```bash
# Backup workflows
docker exec v1_build_n8n_1 tar -czf - /home/node/.n8n > n8n_backup.tar.gz

# Restore workflows
docker exec -i v1_build_n8n_1 tar -xzf - -C / < n8n_backup.tar.gz
```