#!/bin/bash

# Validation Script for n8n Automation Project
echo "🔍 Validating n8n Automation Project Setup..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

# Function to print status
print_status() {
    if [ "$1" = "OK" ]; then
        echo -e "${GREEN}✅ $2${NC}"
    elif [ "$1" = "WARNING" ]; then
        echo -e "${YELLOW}⚠️  $2${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${RED}❌ $2${NC}"
        ERRORS=$((ERRORS + 1))
    fi
}

# Check prerequisites
echo "📋 Checking Prerequisites..."

# Docker
if command -v docker >/dev/null 2>&1; then
    print_status "OK" "Docker is installed"
else
    print_status "ERROR" "Docker is not installed"
fi

# Docker Compose
if command -v docker-compose >/dev/null 2>&1; then
    print_status "OK" "Docker Compose is installed"
else
    print_status "ERROR" "Docker Compose is not installed"
fi

# Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    print_status "OK" "Python is installed: $PYTHON_VERSION"
else
    print_status "WARNING" "Python3 is not installed (Python scripts won't work)"
fi

# Node.js/npm
if command -v npm >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    print_status "OK" "Node.js/npm is installed: Node $NODE_VERSION, npm $NPM_VERSION"
else
    print_status "WARNING" "Node.js/npm is not installed (Node.js project won't work)"
fi

echo ""
echo "📁 Checking Project Structure..."

# Check required files
required_files=(
    "docker-compose.yml"
    "setup.sh"
    "README.md"
    "requirements.txt"
    ".env.template"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "OK" "Found: $file"
    else
        print_status "ERROR" "Missing: $file"
    fi
done

# Check directories
required_dirs=(
    "workflows"
    "workflows/email"
    "workflows/api"
    "workflows/data-processing"
    "workflows/integrations"
    "data"
    "data/input"
    "my-project"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_status "OK" "Found directory: $dir"
    else
        print_status "ERROR" "Missing directory: $dir"
    fi
done

echo ""
echo "📄 Checking Workflow Files..."

# Check workflow JSON files
workflow_files=(
    "workflows/email/email_automation.json"
    "workflows/api/weather_notification.json"
    "workflows/data-processing/csv_processor.json"
    "workflows/integrations/slack_notifications.json"
    "workflows/integrations/database_sync.json"
)

for file in "${workflow_files[@]}"; do
    if [ -f "$file" ]; then
        # Check JSON syntax
        if python3 -m json.tool "$file" >/dev/null 2>&1; then
            print_status "OK" "Valid JSON: $file"
        else
            print_status "ERROR" "Invalid JSON: $file"
        fi
    else
        print_status "WARNING" "Missing workflow file: $file"
    fi
done

echo ""
echo "🐍 Checking Python Scripts..."

python_files=(
    "gpt2_test.py"
    "mini_chat.py"
)

for file in "${python_files[@]}"; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            print_status "OK" "Valid Python syntax: $file"
        else
            print_status "ERROR" "Python syntax error: $file"
        fi
    else
        print_status "WARNING" "Missing Python file: $file"
    fi
done

# Check Python dependencies
if [ -f "requirements.txt" ] && command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "📦 Checking Python Dependencies..."
    
    while IFS= read -r package; do
        # Skip empty lines and comments
        if [[ -n "$package" && ! "$package" =~ ^# ]]; then
            package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'<' -f1)
            if python3 -c "import $package_name" 2>/dev/null; then
                print_status "OK" "Python package available: $package_name"
            else
                print_status "WARNING" "Python package missing: $package_name (run: pip install $package)"
            fi
        fi
    done < requirements.txt
fi

echo ""
echo "📦 Checking Node.js Project..."

if [ -d "my-project" ]; then
    cd my-project
    
    if [ -f "package.json" ]; then
        print_status "OK" "Found package.json"
        
        if [ -f "index.js" ]; then
            if node -c index.js 2>/dev/null; then
                print_status "OK" "Valid Node.js syntax: index.js"
            else
                print_status "ERROR" "Node.js syntax error: index.js"
            fi
        else
            print_status "ERROR" "Missing index.js"
        fi
        
        # Check if node_modules exists
        if [ -d "node_modules" ]; then
            print_status "OK" "Node.js dependencies installed"
        else
            print_status "WARNING" "Node.js dependencies not installed (run: npm install)"
        fi
    else
        print_status "ERROR" "Missing package.json in my-project"
    fi
    
    cd ..
fi

echo ""
echo "🔧 Checking Configuration..."

# Check .env file
if [ -f ".env" ]; then
    print_status "OK" "Environment file exists: .env"
    
    # Check for placeholder values
    if grep -q "YOUR_API_KEY\|your_.*_here\|OWNER/REPO" .env 2>/dev/null; then
        print_status "WARNING" "Environment file contains placeholder values"
    fi
else
    print_status "WARNING" "No .env file found (copy from .env.template)"
fi

# Check if n8n is running
echo ""
echo "🚀 Checking n8n Service..."

if curl -s --max-time 5 http://localhost:5678 >/dev/null 2>&1; then
    print_status "OK" "n8n is running on http://localhost:5678"
else
    print_status "WARNING" "n8n is not running (run: ./setup.sh)"
fi

# Check Docker containers
if command -v docker >/dev/null 2>&1; then
    if docker ps | grep -q n8n; then
        print_status "OK" "n8n Docker container is running"
    else
        print_status "WARNING" "n8n Docker container is not running"
    fi
fi

echo ""
echo "📊 Validation Summary:"
echo "===================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 Perfect! No issues found.${NC}"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}✨ Good! $WARNINGS warning(s) found, but no critical errors.${NC}"
else
    echo -e "${RED}⚠️  Found $ERRORS error(s) and $WARNINGS warning(s) that need attention.${NC}"
fi

echo ""
echo "📚 Next Steps:"
if [ $ERRORS -gt 0 ]; then
    echo "1. Fix the errors listed above"
    echo "2. Run this validation script again"
    echo "3. Check TROUBLESHOOTING.md for solutions"
fi

if [ $WARNINGS -gt 0 ]; then
    echo "- Address warnings for full functionality"
    echo "- Update .env file with real API keys"
    echo "- Install missing dependencies"
fi

echo "- Run: ./setup.sh to start n8n"
echo "- Import workflows from workflows/ directory"
echo "- Check README.md for detailed instructions"

echo ""
exit $ERRORS