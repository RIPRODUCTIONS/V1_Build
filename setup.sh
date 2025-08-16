#!/bin/bash

# n8n Automation Setup Script
echo "🚀 Setting up n8n Automation Environment..."

# Create necessary directories
echo "📁 Creating workflow directories..."
mkdir -p workflows/{email,api,data-processing,notifications,integrations}
mkdir -p data/{input,output,processed}
mkdir -p logs

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 workflows/
chmod 755 data/
chmod 644 workflows/*/*.json

# Check if n8n is running
echo "🔍 Checking n8n status..."
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ n8n is running on http://localhost:5678"
else
    echo "⚠️  n8n is not running. Starting it now..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose up -d
    else
        echo "❌ Docker or Docker Compose not found. Please install Docker to run n8n."
        echo "   You can still use the workflows by importing them manually."
    fi
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
echo "2. Login with: admin / yourSecurePassword123"
echo "3. Import workflows from the workflows/ directory"
echo "4. Configure your API keys and credentials"
echo "5. Test each workflow individually"
echo ""
echo "📚 Check README.md for detailed instructions" 