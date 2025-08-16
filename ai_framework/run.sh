#!/bin/bash

# AI Framework Startup Script
# This script starts the complete AI agent system

echo "🤖 Starting AI Framework System..."
echo "=================================="

# Check if we're in the right directory
if [ ! -d "core" ] || [ ! -d "agents" ]; then
    echo "❌ Error: Please run this script from the ai_framework directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected structure: ai_framework/core/, ai_framework/agents/"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.11+ is required, found $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn" &> /dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Test the system first
echo "🧪 Running system tests..."
python3 test_system.py
if [ $? -ne 0 ]; then
    echo "❌ System tests failed. Please check the errors above."
    echo "   You can still try to start the system, but it may not work correctly."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ System tests passed"
fi

# Start the system
echo "🚀 Starting AI Framework..."
echo "   Dashboard will be available at: http://localhost:8000/frontend/"
echo "   API docs will be available at: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop the system"
echo "=================================="

python3 start_system.py






