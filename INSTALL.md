# n8n Automation Workflows - Installation Guide

## Quick Start

### 1. Install Dependencies

#### Node.js Dependencies
```bash
npm install
```

#### Python Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Start n8n Environment
```bash
# Using npm script
npm run setup

# Or directly
./setup.sh
```

### 3. Access n8n
- URL: http://localhost:5678
- Username: admin
- Password: yourSecurePassword123

## Available Scripts

- `npm start` - Start the n8n automation environment
- `npm run setup` - Run the setup script
- `npm run install-python-deps` - Install Python dependencies
- `npm run test-python` - Test Python GPT-2 script
- `npm run test-chat` - Test interactive chat script
- `npm run docker-up` - Start n8n with Docker
- `npm run docker-down` - Stop n8n Docker containers
- `npm run docker-logs` - View n8n logs

## Troubleshooting

### Python Dependencies
If you encounter issues with transformers library:
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### Docker Issues
If docker compose is not available:
```bash
# Install Docker Desktop or
# Use the legacy docker-compose command
```

### n8n Access
If n8n is not accessible:
```bash
docker compose logs n8n
```

## Offline Mode
The Python scripts are designed to work in offline environments with graceful fallbacks when models cannot be downloaded.