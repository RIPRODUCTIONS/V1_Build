# n8n Automation Workflows Repository

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

This repository contains n8n automation workflows designed to streamline business processes. The system runs n8n via Docker and includes pre-built workflows for email automation, API integrations, data processing, and team notifications.

## Working Effectively

### Bootstrap and Setup
- Install Docker and Docker Compose: Required for running n8n instance
- Start n8n automation environment:
  - `docker compose up -d` -- takes 45 seconds on first pull, 1 second on subsequent starts. NEVER CANCEL. Set timeout to 120+ seconds for first run, 30+ seconds for subsequent starts.
  - Access n8n at: http://localhost:5678
  - **CRITICAL**: On first access, complete initial setup with admin account (email: admin@example.com, password: yourSecurePassword123)
- Run environment setup: `chmod +x setup.sh && ./setup.sh` -- takes 2 seconds. Creates necessary directories and sample data files.
- Install npm dependencies: `npm install` -- takes 10 seconds. NEVER CANCEL. Set timeout to 60+ seconds.

### Core Operations
- Start n8n: `docker compose up -d` -- 1 second (cached), 45 seconds (first time). NEVER CANCEL.
- Stop n8n: `docker compose down` -- takes 10 seconds. NEVER CANCEL. Set timeout to 30+ seconds.
- Check n8n status: `curl -s http://localhost:5678` -- returns HTML if running
- View logs: `docker compose logs -f n8n` -- real-time log monitoring

## Validation

### Manual Testing Requirements
- ALWAYS manually validate workflow functionality after making changes
- Test the complete setup process:
  1. Run `./setup.sh` to initialize environment
  2. Start n8n with `docker compose up -d`
  3. Access http://localhost:5678 and complete initial setup if needed
  4. Import a sample workflow and verify it can be activated
- **CRITICAL VALIDATION SCENARIOS**:
  - **Email workflows**: Verify email trigger configuration and test message filtering
  - **API integrations**: Test API credential setup and response handling
  - **Data processing**: Upload sample CSV file to data/input/ and verify processing
  - **Slack integrations**: Test webhook configuration and message posting
- Run through at least one complete end-to-end workflow scenario after making changes

### Performance Expectations
- Docker image pull (first time): 45 seconds
- n8n startup (cached): 1 second
- n8n startup (fresh): 30 seconds after container starts
- Environment setup script: 2 seconds
- npm install: 10 seconds
- Container shutdown: 10 seconds

## Common Tasks

### Working with Workflows
- Import workflow: Access http://localhost:5678 → "Import from File" → Select JSON file from workflows/ directory
- Workflow categories:
  - `workflows/email/`: Email automation and filtering
  - `workflows/api/`: Weather alerts and API integrations
  - `workflows/data-processing/`: CSV processing and data transformation
  - `workflows/integrations/`: Slack notifications and database sync
- Test individual workflows: Use n8n "Execute Node" feature to test nodes individually
- Monitor executions: Check n8n execution logs for workflow status and errors

### Repository Structure
```
.
├── README.md                   # Comprehensive workflow documentation
├── QUICK_REFERENCE.md         # Common patterns and troubleshooting
├── docker-compose.yml         # n8n service configuration  
├── .env                       # n8n authentication settings
├── setup.sh                   # Environment initialization script
├── package.json               # Node.js dependencies (@octokit/rest, puppeteer)
├── workflows/                 # n8n workflow JSON files
│   ├── email/                 # Email automation workflows
│   ├── api/                   # API integration workflows  
│   ├── data-processing/       # Data processing workflows
│   └── integrations/          # Slack and database workflows
├── data/                      # Sample data and processing directories
│   └── input/                 # Input files for data processing workflows
├── mini_chat.py              # GPT-2 chat demo (requires transformers library)
├── gpt2_test.py              # GPT-2 text generation test (requires transformers library)
└── my-project/               # Additional Node.js project with GitHub/Supabase deps
```

### Credential Configuration
- Access n8n Settings → Credentials to add API keys and authentication
- Required for workflows:
  - Email provider credentials (Gmail, Outlook, etc.)
  - OpenWeatherMap API key: Sign up at openweathermap.org
  - GitHub personal access token: For repository monitoring
  - Slack webhook URL: Create app and get webhook
  - Database credentials: PostgreSQL connections for sync workflows
- Test all credential connections before activating workflows

### Development Dependencies
- Node.js 20.19.4+ and npm 10.8.2+: For package management
- Docker and Docker Compose: Essential for n8n operation
- Python 3.12.3+: For GPT-2 demo scripts (optional)
- transformers library: Required only for Python ML demos (not core functionality)

## Troubleshooting

### Common Issues
- **n8n not accessible**: Ensure Docker is running and container started successfully
- **Workflow import fails**: Check JSON file format and n8n node version compatibility  
- **Email workflows not triggering**: Verify email credentials and trigger configuration
- **API rate limits**: Add delays between API calls and monitor usage
- **File processing errors**: Ensure n8n has read/write permissions to data directories

### Build and Test Process
- No traditional build process required - workflows are imported directly into n8n
- Validation process:
  1. Start n8n environment
  2. Import workflows via web interface
  3. Configure credentials for external services
  4. Test individual workflow nodes
  5. Activate workflows and monitor execution logs
- No automated test suite - validation is done through n8n interface

### Error Recovery
- Restart n8n: `docker compose restart n8n` -- takes 10 seconds
- Reset environment: `docker compose down && docker compose up -d` -- takes 11 seconds total
- Clear volumes: `docker compose down -v` to reset all n8n data
- Check logs: `docker compose logs n8n` for troubleshooting

### Documentation References
- n8n official docs: https://docs.n8n.io/
- Community forum: https://community.n8n.io/
- Workflow patterns: See QUICK_REFERENCE.md for common automation patterns
- API documentation: See README.md for detailed workflow setup instructions

### Python Scripts (Optional)
- `mini_chat.py`: Interactive GPT-2 chat interface (requires `pip install transformers`)
- `gpt2_test.py`: Simple text generation test (requires `pip install transformers`)
- These scripts are independent of the main n8n functionality and require additional setup

## Security Considerations

- Store API keys and credentials securely in n8n credential manager
- Use environment variables for sensitive configuration
- Regularly rotate access tokens and API keys  
- Monitor workflow execution logs for security issues
- Limit file system permissions for data processing workflows

## Key Project Areas

### Email Automation (`workflows/email/`)
- **Purpose**: Process and route emails based on content and priority
- **Key files**: `email_automation.json`, `email_automation_fixed.json`
- **Features**: Urgent email filtering, automatic routing, invoice processing

### API Integrations (`workflows/api/`)
- **Purpose**: Weather monitoring and alert system
- **Key files**: `weather_notification.json`
- **Features**: Hourly weather checks, temperature alerts, daily reports

### Data Processing (`workflows/data-processing/`)
- **Purpose**: CSV file processing and transaction monitoring
- **Key files**: Sample workflows for transaction analysis
- **Features**: File monitoring, data validation, alert generation

### Team Integrations (`workflows/integrations/`)
- **Purpose**: Slack notifications and database synchronization
- **Key files**: `slack_notifications.json`, `database_sync.json`
- **Features**: GitHub monitoring, team alerts, data sync between systems

Always start with the setup script, ensure n8n is running properly, and test workflow imports before making any modifications to the automation logic.