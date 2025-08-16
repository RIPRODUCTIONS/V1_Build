#!/bin/bash
# Quick Start Script for M3 Max AI Framework
# Run this script to get started immediately

set -e

echo "🚀 Quick Start: M3 Max AI Framework"
echo "===================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -d "ai_framework" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   (where the 'ai_framework' folder is located)"
    exit 1
fi

# Quick setup function
quick_setup() {
    print_info "Starting quick setup for M3 Max..."

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        print_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    # Install essential tools
    print_info "Installing essential tools..."
    brew install --quiet python@3.11 redis postgresql@15

    # Start services
    print_info "Starting services..."
    brew services start redis
    brew services start postgresql@15

    # Setup AI Framework
    print_info "Setting up AI Framework..."
    cd ai_framework

    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Create basic .env file
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# AI Framework Environment Configuration
# Quick Setup for M3 Max

DATABASE_TYPE=sqlite
DATABASE_PATH=ai_framework.db
REDIS_HOST=localhost
REDIS_PORT=6379
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# M3 Max Optimizations
PYTHONOPTIMIZE=1
PYTHONUNBUFFERED=1
EOF
        print_status "Environment file created"
    fi

    # Create scripts directory if it doesn't exist
    mkdir -p scripts

    # Create optimization script
    cat > scripts/optimize_m3_max.py << 'EOF'
#!/usr/bin/env python3
"""
Quick M3 Max Optimization Script
"""

import os
import multiprocessing

def main():
    print("🚀 Applying M3 Max Quick Optimizations")
    print("=" * 40)

    # Set optimizations
    optimizations = {
        'PYTHONOPTIMIZE': '1',
        'PYTHONUNBUFFERED': '1',
        'OMP_NUM_THREADS': str(multiprocessing.cpu_count()),
        'MKL_NUM_THREADS': str(multiprocessing.cpu_count()),
        'OPENBLAS_NUM_THREADS': str(multiprocessing.cpu_count()),
    }

    for key, value in optimizations.items():
        os.environ[key] = value
        print(f"Set {key}={value}")

    print(f"\n✅ Optimized for {multiprocessing.cpu_count()} CPU cores")
    print("Ready to run!")

if __name__ == "__main__":
    main()
EOF

    chmod +x scripts/optimize_m3_max.py

    print_status "Quick setup complete!"

    # Return to root directory
    cd ..
}

# Start the AI Framework
start_framework() {
    print_info "Starting AI Framework..."

    cd ai_framework
    source venv/bin/activate

    # Run optimization
    python scripts/optimize_m3_max.py

    # Start the framework
    print_info "Starting AI Framework on http://localhost:8000"
    print_info "Press Ctrl+C to stop"

    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Main menu
show_menu() {
    echo ""
    echo "🎯 What would you like to do?"
    echo "1. Quick Setup (install dependencies and setup environment)"
    echo "2. Start AI Framework (after setup is complete)"
    echo "3. Full Setup (run complete setup script)"
    echo "4. Exit"
    echo ""
    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            quick_setup
            show_menu
            ;;
        2)
            start_framework
            ;;
        3)
            if [ -f "setup_m3_max.sh" ]; then
                chmod +x setup_m3_max.sh
                ./setup_m3_max.sh
            else
                echo "❌ Full setup script not found. Run quick setup first."
                show_menu
            fi
            ;;
        4)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please try again."
            show_menu
            ;;
    esac
}

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Check if we're on Apple Silicon
    if [[ $(uname -m) != "arm64" ]]; then
        echo "⚠️  Warning: This script is optimized for Apple Silicon (M3 Max)"
        echo "   Detected: $(uname -m)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    show_menu
fi
