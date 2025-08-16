# n8n Automation Workflows Repository

ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- Install and run n8n automation platform:
  - `docker compose up -d` -- takes ~45 seconds on first run (downloads n8n image), <1 second on subsequent runs. NEVER CANCEL. Set timeout to 90+ seconds.
  - Wait 30 seconds for n8n to fully start after container creation
  - Access n8n at: http://localhost:5678
  - Login credentials: admin / yourSecurePassword123
- Install Node.js dependencies:
  - `npm install` -- takes <1 second. Set timeout to 30+ seconds.
- Install Python dependencies for AI/ML features:
  - `pip3 install transformers torch` -- takes ~3 minutes. NEVER CANCEL. Set timeout to 300+ seconds.
  - WARNING: GPT-2 model download requires internet connectivity and may fail in restricted environments
- Run setup script for directory structure:
  - `chmod +x setup.sh && ./setup.sh` -- takes <5 seconds. Creates workflow directories and sample data.

### Build and Test Operations
- No traditional "build" process - this is a workflow configuration repository
- Validate n8n is running: `curl -I http://localhost:5678` (should return HTTP 200)
- Test Node.js dependencies: 
  - `node -e "const puppeteer = require('puppeteer'); console.log('Puppeteer loaded');"` 
  - `node -e "const { Octokit } = require('@octokit/rest'); console.log('Octokit loaded');"`
- Test Python components: `python3 gpt2_test.py` (requires internet for model download)
- Container management:
  - Stop: `docker compose down` -- takes ~10 seconds. NEVER CANCEL. Set timeout to 30+ seconds.
  - Restart: `docker compose up -d` -- takes <1 second after initial setup

### Running the Application
- ALWAYS run bootstrap steps first before starting n8n
- Start n8n: `docker compose up -d`
- Wait 30 seconds, then access web interface at http://localhost:5678
- Login with: admin / yourSecurePassword123
- The application runs entirely through the web interface - no CLI interaction needed

## Validation

### Manual Testing Requirements
- ALWAYS test complete end-to-end workflows after making changes to workflow files
- Validate n8n web interface accessibility:
  1. Navigate to http://localhost:5678 
  2. Login with admin credentials
  3. Verify workflow list is accessible
  4. Test importing a workflow from workflows/ directory
- Test workflow components:
  1. Import a workflow from workflows/email/, workflows/api/, or workflows/data-processing/
  2. Configure any required credentials (API keys, email settings)
  3. Test individual nodes using "Execute Node" feature
  4. Activate the workflow and monitor execution logs
- ALWAYS verify docker containers are running: `docker compose ps` should show n8n container as "Up"

### Required Testing Scenarios
- **n8n Access**: Navigate to http://localhost:5678, login, import a workflow
- **Workflow Import**: Import JSON file from workflows/ directory, verify nodes load correctly
- **API Integration Testing**: Configure and test HTTP request nodes with mock APIs
- **Email Workflow Testing**: Import email automation workflow, verify trigger and action nodes
- **Data Processing**: Test CSV processing workflow with sample data from data/input/

## Common Commands and Tasks

### Development Workflow
- Start development environment: `docker compose up -d && sleep 30`
- Check application status: `curl -I http://localhost:5678 && docker compose ps`
- View logs: `docker compose logs n8n | tail -20`
- Restart application: `docker compose restart && sleep 30`
- Clean restart: `docker compose down && docker compose up -d && sleep 30`

### Timing Expectations
- **NEVER CANCEL**: Initial Docker setup takes 45+ seconds, wait for completion
- **NEVER CANCEL**: Python dependency installation takes 3+ minutes, wait for completion  
- Docker shutdown: ~10 seconds
- Docker restart: <1 second after initial setup
- npm install: <1 second for existing dependencies
- n8n startup after container creation: ~30 seconds

### Network and External Dependencies
- **LIMITED INTERNET ACCESS**: Python GPT-2 models may fail to download
- **LIMITED INTERNET ACCESS**: Browser automation (Puppeteer) cannot download Chrome
- **WORKING**: n8n Docker image downloads successfully
- **WORKING**: Node.js package installations work correctly
- **WORKAROUND**: Use API testing via curl instead of browser automation for validation

## Key Repository Structure

### Important Directories
- `workflows/` - n8n workflow JSON files organized by category:
  - `workflows/email/` - Email automation workflows
  - `workflows/api/` - API integration workflows (weather, external services)
  - `workflows/data-processing/` - CSV and data transformation workflows
  - `workflows/integrations/` - Slack, database, and system integrations
- `data/` - Sample data files for testing workflows:
  - `data/input/` - Input data files (CSV, etc.)
  - `data/output/` - Processed output files
  - `data/processed/` - Archived processed files
- `my-project/` - Separate Node.js subproject with GitHub API integration

### Key Files
- `docker-compose.yml` - n8n container configuration
- `.env` - n8n environment variables and credentials
- `setup.sh` - Environment setup script
- `package.json` - Node.js dependencies (@octokit/rest, puppeteer)
- `mini_chat.py` - Interactive GPT-2 text generation
- `gpt2_test.py` - Automated GPT-2 testing script

### Configuration Notes
- n8n persists data in Docker volume `v1_build_n8n_data`
- Basic authentication enabled for n8n web interface
- All workflows require manual credential configuration after import
- External API integrations need valid API keys (OpenWeatherMap, GitHub, Slack)

## Troubleshooting

### Common Issues
- **n8n not accessible**: Wait 30+ seconds after `docker compose up -d`, check with `curl -I http://localhost:5678`
- **Workflow import fails**: Ensure JSON files are valid, check n8n logs with `docker compose logs n8n`
- **Python scripts fail**: Internet connectivity required for model downloads, use mock data for testing
- **Browser automation fails**: Chrome download requires internet, use curl for API testing instead

### Debug Commands
- Check container status: `docker compose ps`
- View n8n logs: `docker compose logs n8n | tail -30`
- Test API connectivity: `curl -I http://localhost:5678`
- Verify Node.js setup: `node --version && npm list --depth=0`
- Check Python environment: `python3 --version && pip3 list | grep transformers`

## Frequently Referenced Commands

### Quick Start (copy/paste ready)
```bash
# Complete startup sequence
docker compose up -d && sleep 30
curl -I http://localhost:5678 && docker compose ps

# Node.js validation
node -e "const puppeteer = require('puppeteer'); console.log('Puppeteer loaded');"
node -e "const { Octokit } = require('@octokit/rest'); console.log('Octokit loaded');"

# Development workflow restart
docker compose restart && sleep 30
```

### Common File Locations
- Main workflows: `workflows/email/email_automation.json`, `workflows/api/weather_notification.json`
- Sample data: `data/input/sample_transactions.csv`
- Configuration: `.env`, `docker-compose.yml`, `package.json`
- Python scripts: `mini_chat.py`, `gpt2_test.py`

## CRITICAL Reminders
- **NEVER CANCEL** Docker operations - they may take 45+ seconds initially
- **NEVER CANCEL** Python installations - they take 3+ minutes  
- **ALWAYS** wait 30 seconds after starting n8n before testing
- **ALWAYS** test complete workflows, not just individual components
- **ALWAYS** validate through the web interface at http://localhost:5678
- **SET TIMEOUTS**: 90+ seconds for Docker, 300+ seconds for Python, 30+ seconds for other operations
- **VALIDATE CHANGES**: Always import and test workflow files after modifications