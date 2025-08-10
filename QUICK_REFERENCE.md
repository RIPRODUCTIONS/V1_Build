# n8n Quick Reference Guide

## 🚀 Common Automation Patterns

### 1. Email Processing
```json
{
  "trigger": "emailTrigger",
  "filter": "if (subject contains 'urgent')",
  "action": "emailSend"
}
```

### 2. API Integration
```json
{
  "trigger": "scheduleTrigger",
  "api": "httpRequest",
  "condition": "if (temperature > 30)",
  "notification": "emailSend"
}
```

### 3. File Processing
```json
{
  "trigger": "fileTrigger",
  "filter": "if (extension == '.csv')",
  "process": "csv",
  "action": "emailSend"
}
```

### 4. Database Operations
```json
{
  "trigger": "scheduleTrigger",
  "query": "postgres",
  "condition": "if (count > 0)",
  "action": "postgres"
}
```

## 📋 Node Types Reference

### Triggers
- **Schedule Trigger**: Time-based automation
- **Email Trigger**: Monitor email inbox
- **File Trigger**: Watch for new files
- **Webhook Trigger**: Real-time events
- **Manual Trigger**: Manual execution

### Actions
- **Email Send**: Send notifications
- **HTTP Request**: API calls
- **PostgreSQL**: Database operations
- **Slack**: Team notifications
- **File Write**: Save files

### Processing
- **IF**: Conditional logic
- **Switch**: Multiple conditions
- **Code**: Custom JavaScript
- **CSV**: Data parsing
- **Set**: Variable assignment

## 🔧 Configuration Tips

### Email Setup
1. Go to Settings → Credentials
2. Add email provider (Gmail, Outlook, etc.)
3. Test connection
4. Use in workflow nodes

### API Configuration
1. Get API key from service provider
2. Store in n8n credentials
3. Use in HTTP Request nodes
4. Handle rate limits

### Database Setup
1. Add database credentials
2. Test connection
3. Use in PostgreSQL nodes
4. Set up proper indexes

## 📊 Best Practices

### Error Handling
```javascript
// In Code node
try {
  // Your logic here
  return { success: true, data: result };
} catch (error) {
  return { success: false, error: error.message };
}
```

### Rate Limiting
```javascript
// Add delay between API calls
await new Promise(resolve => setTimeout(resolve, 1000));
```

### Data Validation
```javascript
// Validate required fields
if (!data.email || !data.name) {
  throw new Error('Missing required fields');
}
```

## 🎯 Common Use Cases

### 1. Customer Support Automation
- Monitor support tickets
- Auto-assign based on category
- Send follow-up emails
- Update CRM records

### 2. E-commerce Automation
- Process orders
- Update inventory
- Send shipping notifications
- Generate reports

### 3. Marketing Automation
- Email campaign triggers
- Lead scoring
- Social media posting
- Analytics tracking

### 4. Development Workflow
- GitHub issue tracking
- Code review reminders
- Deployment notifications
- Performance monitoring

## 🔍 Debugging Tips

### 1. Test Individual Nodes
- Click "Execute Node" to test
- Check output data
- Verify connections

### 2. Use Debug Mode
- Enable debug logging
- Check execution logs
- Monitor performance

### 3. Common Issues
- **Credentials**: Verify API keys
- **Permissions**: Check file/database access
- **Rate Limits**: Add delays
- **Data Format**: Validate JSON/CSV

## 📈 Performance Optimization

### 1. Batch Processing
```javascript
// Process items in batches
const batchSize = 100;
for (let i = 0; i < items.length; i += batchSize) {
  const batch = items.slice(i, i + batchSize);
  // Process batch
}
```

### 2. Caching
```javascript
// Cache API responses
const cache = new Map();
if (cache.has(key)) {
  return cache.get(key);
}
```

### 3. Parallel Processing
- Use multiple execution paths
- Process independent tasks simultaneously
- Monitor resource usage

## 🔒 Security Checklist

- [ ] Store credentials securely
- [ ] Use environment variables
- [ ] Implement proper error handling
- [ ] Monitor access logs
- [ ] Regular security updates
- [ ] Data encryption
- [ ] Access control

## 📞 Support Resources

- **Documentation**: https://docs.n8n.io/
- **Community**: https://community.n8n.io/
- **GitHub**: https://github.com/n8n-io/n8n
- **Discord**: n8n Discord server

---

**Remember**: Start simple, test thoroughly, and scale gradually! 🚀 