# n8n Automation Workflows

This repository contains a collection of n8n automation workflows designed to streamline various business processes. Each workflow is organized by category and can be imported directly into your n8n instance.

## 🚀 Getting Started

### Prerequisites
- n8n instance running (already set up in this directory)
- Docker and Docker Compose installed
- Required API keys and credentials for external services

### Starting n8n
```bash
docker-compose up -d
```

Access n8n at: http://localhost:5678
- Username: admin
- Password: yourSecurePassword123

## 📁 Workflow Categories

### 1. Email Automations (`workflows/email/`)
**File: `email_automation.json`**

**Purpose**: Automatically process incoming emails and route them based on content.

**Features**:
- Monitors email inbox every minute
- Filters urgent emails (contains "urgent" in subject)
- Routes invoice emails to finance team
- Archives non-urgent emails

**Setup Required**:
- Configure email credentials in n8n
- Update email addresses for notifications
- Set up email trigger with your email provider

**Usage**:
1. Import the workflow into n8n
2. Configure email trigger with your email credentials
3. Update recipient email addresses
4. Activate the workflow

### 2. API Integrations (`workflows/api/`)
**File: `weather_notification.json`**

**Purpose**: Fetch weather data and send alerts based on conditions.

**Features**:
- Checks weather every hour
- Sends high temperature alerts (>30°C)
- Sends low temperature alerts (<0°C)
- Daily weather reports

**Setup Required**:
- OpenWeatherMap API key
- Email configuration for alerts
- Update location in API call

**Usage**:
1. Get API key from [OpenWeatherMap](https://openweathermap.org/api)
2. Replace `YOUR_API_KEY` in the workflow
3. Update location in the API call
4. Configure email settings
5. Activate the workflow

### 3. Data Processing (`workflows/data-processing/`)
**File: `csv_processor.json`**

**Purpose**: Process CSV files and trigger actions based on data.

**Features**:
- Monitors for new CSV files
- Processes transaction data
- Alerts on high-value transactions (>$1000)
- Notifies about pending transactions
- Creates processed CSV files

**Setup Required**:
- Configure file monitoring directory
- Set up email notifications
- Update transaction thresholds

**Usage**:
1. Import the workflow
2. Configure file trigger directory
3. Update email addresses
4. Adjust transaction thresholds
5. Activate the workflow

### 4. Slack Integrations (`workflows/integrations/`)
**File: `slack_notifications.json`**

**Purpose**: Send team notifications and monitor development activities.

**Features**:
- Daily morning messages with weather
- GitHub issue monitoring
- Pull request review reminders
- Team alerts for high issue counts

**Setup Required**:
- Slack app configuration
- GitHub API access
- OpenWeatherMap API key
- Update repository details

**Usage**:
1. Create Slack app and get webhook URL
2. Configure GitHub API credentials
3. Update repository owner/name
4. Set up Slack channels
5. Activate the workflow

### 5. Database Synchronization (`workflows/integrations/`)
**File: `database_sync.json``

**Purpose**: Synchronize data between different database systems.

**Features**:
- Syncs customer data every 10 minutes
- Tracks daily customer registrations
- Alerts on high registration rates
- Generates sync reports

**Setup Required**:
- Source and target database connections
- PostgreSQL credentials
- Email configuration for reports

**Usage**:
1. Configure database connections
2. Update table names and columns
3. Set up email notifications
4. Adjust sync frequency
5. Activate the workflow

## 🔧 Configuration Guide

### Common Setup Steps

1. **Email Configuration**
   - Go to n8n Settings → Credentials
   - Add your email provider credentials
   - Test the connection

2. **API Keys**
   - OpenWeatherMap: Sign up at openweathermap.org
   - GitHub: Create personal access token
   - Slack: Create app and get webhook URL

3. **Database Connections**
   - Add PostgreSQL credentials
   - Test connections before activating workflows

4. **File Monitoring**
   - Set up appropriate directories
   - Ensure n8n has read/write permissions

### Workflow Import Process

1. Open n8n interface
2. Click "Import from file"
3. Select the JSON workflow file
4. Review and adjust configurations
5. Save and activate the workflow

## 📊 Monitoring and Maintenance

### Workflow Health Checks
- Monitor execution logs in n8n
- Set up error notifications
- Review performance metrics

### Regular Maintenance
- Update API keys when needed
- Review and adjust thresholds
- Clean up old data files
- Monitor database performance

## 🛠️ Customization

### Adding New Triggers
- Schedule triggers for time-based automation
- Webhook triggers for real-time events
- File triggers for file-based automation

### Extending Workflows
- Add new conditions with IF nodes
- Include additional API calls
- Create custom data transformations
- Add new notification channels

### Error Handling
- Add error handling nodes
- Set up retry mechanisms
- Configure fallback actions

## 🔒 Security Considerations

- Store sensitive credentials securely
- Use environment variables for API keys
- Regularly rotate access tokens
- Monitor workflow access logs
- Implement proper error handling

## 📈 Best Practices

1. **Testing**: Always test workflows in development first
2. **Documentation**: Keep workflow documentation updated
3. **Monitoring**: Set up alerts for workflow failures
4. **Backup**: Regularly backup workflow configurations
5. **Version Control**: Use version control for workflow changes

## 🆘 Troubleshooting

### Common Issues

1. **Workflow not triggering**
   - Check trigger configuration
   - Verify credentials are valid
   - Review execution logs

2. **API rate limits**
   - Implement delays between calls
   - Use pagination for large datasets
   - Monitor API usage

3. **Email delivery issues**
   - Verify email credentials
   - Check spam filters
   - Test with different email providers

### Getting Help

- Check n8n documentation: https://docs.n8n.io/
- Review workflow execution logs
- Test individual nodes
- Use n8n community forums

## 📝 License

This project is for educational and business automation purposes. Please ensure compliance with all applicable laws and regulations when using these workflows.

---

**Happy Automating! 🚀** 