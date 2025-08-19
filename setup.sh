#!/bin/bash

# n8n Automation Setup Script
echo "🚀 Setting up n8n Automation Environment..."

# Security check: Ensure .env file exists and has secure password
if [ -f ".env" ]; then
    if grep -q "CHANGE_THIS_TO_SECURE_PASSWORD_NOW" .env; then
        echo "⚠️  SECURITY WARNING: Please update the password in .env file before proceeding!"
        echo "   Edit .env and change N8N_BASIC_AUTH_PASSWORD to a strong password"
        echo ""
    fi
else
    echo "⚠️  SECURITY WARNING: .env file not found!"
    echo "   Copy .env.example to .env and configure with secure credentials"
    echo ""
fi

# Create necessary directories
echo "📁 Creating workflow directories..."
mkdir -p workflows/{email,api,data-processing,notifications,integrations}
mkdir -p data/{input,output,processed}
mkdir -p logs

# Set proper permissions (security: restrict access to workflow files)
echo "🔐 Setting secure permissions..."
chmod 750 workflows/
chmod 750 data/
chmod 640 workflows/*/*.json
chmod 600 .env

# Check if n8n is running
echo "🔍 Checking n8n status..."
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ n8n is running on http://localhost:5678"
else
    echo "⚠️  n8n is not running. Starting it now..."
    docker-compose up -d
    echo "⏳ Waiting for n8n to start..."
    sleep 10
fi

# Create sample data files for testing
echo "📄 Creating sample data files..."
cat > data/input/sample_transactions.csv << EOF
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
echo "2. Login with credentials from your .env file"
echo "3. Import workflows from the workflows/ directory"
echo "4. Configure your API keys and credentials"
echo "5. Test each workflow individually"
echo ""
echo "📚 Check README.md and SECURITY.md for detailed instructions" 