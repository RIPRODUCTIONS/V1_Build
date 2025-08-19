#!/bin/bash

# n8n Automation Setup Script
set -e  # Exit on any error

echo "🚀 Setting up n8n Automation Environment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create directory if it doesn't exist
safe_mkdir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "✅ Created directory: $1"
    else
        echo "📁 Directory already exists: $1"
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create necessary directories
echo "📁 Creating workflow directories..."
safe_mkdir "workflows/email"
safe_mkdir "workflows/api" 
safe_mkdir "workflows/data-processing"
safe_mkdir "workflows/notifications"
safe_mkdir "workflows/integrations"
safe_mkdir "data/input"
safe_mkdir "data/output"
safe_mkdir "data/processed"
safe_mkdir "logs"

# Set proper permissions
echo "🔐 Setting permissions..."
chmod -R 755 workflows/ 2>/dev/null || echo "⚠️  Could not set workflow permissions (may require sudo)"
chmod -R 755 data/ 2>/dev/null || echo "⚠️  Could not set data permissions (may require sudo)"

# Check for existing JSON files and set permissions
if find workflows/ -name "*.json" -type f 2>/dev/null | grep -q .; then
    chmod 644 workflows/*/*.json 2>/dev/null || echo "⚠️  Could not set JSON file permissions"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✅ .env file created from template"
        echo "⚠️  Please edit .env file with your actual credentials"
    else
        echo "⚠️  .env.template not found, using basic .env"
        cat > .env << 'EOF'
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=yourSecurePassword123
N8N_HOST=localhost
N8N_PORT=5678
EOF
    fi
fi

# Check if n8n is running
echo "🔍 Checking n8n status..."
if curl -s --max-time 5 http://localhost:5678 > /dev/null 2>&1; then
    echo "✅ n8n is running on http://localhost:5678"
else
    echo "⚠️  n8n is not running. Starting it now..."
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo "❌ docker-compose.yml not found!"
        exit 1
    fi
    
    # Start n8n
    echo "🚀 Starting n8n with Docker Compose..."
    if docker-compose up -d; then
        echo "⏳ Waiting for n8n to start..."
        
        # Wait for n8n to be ready (max 60 seconds)
        counter=0
        while [ $counter -lt 60 ]; do
            if curl -s --max-time 2 http://localhost:5678 > /dev/null 2>&1; then
                echo "✅ n8n is now running!"
                break
            fi
            echo "⏳ Waiting... (${counter}s)"
            sleep 2
            counter=$((counter + 2))
        done
        
        if [ $counter -ge 60 ]; then
            echo "⚠️  n8n took longer than expected to start. Please check manually."
        fi
    else
        echo "❌ Failed to start n8n with Docker Compose"
        exit 1
    fi
fi

# Create sample data files for testing
echo "📄 Creating sample data files..."
if [ ! -f "data/input/sample_transactions.csv" ]; then
    cat > data/input/sample_transactions.csv << 'EOF'
id,amount,customer,date,status
1,1500,John Doe,2024-01-15,completed
2,500,Jane Smith,2024-01-15,pending
3,2500,Bob Johnson,2024-01-15,completed
4,750,Alice Brown,2024-01-15,pending
EOF
    echo "✅ Created sample transactions CSV file"
else
    echo "📄 Sample transactions file already exists"
fi

# Check Python dependencies if Python scripts exist
if [ -f "gpt2_test.py" ] || [ -f "mini_chat.py" ]; then
    echo "🐍 Checking Python dependencies..."
    if command_exists python3; then
        if [ -f "requirements.txt" ]; then
            echo "📦 Installing Python dependencies..."
            python3 -m pip install -q -r requirements.txt || echo "⚠️  Could not install Python dependencies"
        else
            echo "⚠️  requirements.txt not found for Python scripts"
        fi
    else
        echo "⚠️  Python3 not found. Python scripts may not work."
    fi
fi

# Check Node.js project
if [ -d "my-project" ] && [ -f "my-project/package.json" ]; then
    echo "📦 Checking Node.js project..."
    if command_exists npm; then
        cd my-project
        echo "📦 Installing Node.js dependencies..."
        npm install --silent || echo "⚠️  Could not install Node.js dependencies"
        cd ..
    else
        echo "⚠️  npm not found. Node.js project may not work."
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Access n8n at: http://localhost:5678"
echo "2. Login with: admin / yourSecurePassword123"
echo "3. Edit .env file with your actual API keys and credentials"
echo "4. Import workflows from the workflows/ directory"
echo "5. Configure your API keys and credentials in n8n"
echo "6. Test each workflow individually"
echo ""
echo "📚 Check README.md for detailed instructions"
echo ""
echo "🔧 Important configuration files:"
echo "   - .env (n8n environment variables)"
echo "   - .env.template (configuration template)"
echo "   - requirements.txt (Python dependencies)"
echo ""
id,amount,customer,date,status
1,1500,John Doe,2024-01-15,completed
2,500,Jane Smith,2024-01-15,pending
3,2500,Bob Johnson,2024-01-15,completed
4,750,Alice Brown,2024-01-15,pending
EOF

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Access n8n at: http://localhost:5678"
echo "2. Login with: admin / yourSecurePassword123"
echo "3. Import workflows from the workflows/ directory"
echo "4. Configure your API keys and credentials"
echo "5. Test each workflow individually"
echo ""
echo "📚 Check README.md for detailed instructions" 