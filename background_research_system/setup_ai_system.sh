#!/bin/bash

# AI-Enhanced Background Research System Setup Script
# This script automates the installation and configuration of the enhanced system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    # Check if version is 3.8 or higher
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python $PYTHON_VERSION found, but Python 3.8 or higher is required."
        exit 1
    fi
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."

    # Check Python
    check_python_version

    # Check pip
    if ! command_exists pip3 && ! command_exists pip; then
        print_error "pip is not installed. Please install pip."
        exit 1
    fi

    # Check git
    if ! command_exists git; then
        print_warning "git is not installed. Some features may not work properly."
    else
        print_success "git found"
    fi

    # Check Chrome/Chromium
    if ! command_exists google-chrome && ! command_exists chromium-browser && ! command_exists chrome; then
        print_warning "Chrome/Chromium is not installed. Web scraping features may not work."
    else
        print_success "Chrome/Chromium found"
    fi
}

# Function to create virtual environment
create_virtual_environment() {
    print_status "Creating virtual environment..."

    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi

    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Function to install Ollama
install_ollama() {
    print_status "Installing Ollama..."

    if command_exists ollama; then
        print_success "Ollama is already installed"
    else
        print_status "Installing Ollama from official installer..."
        curl -fsSL https://ollama.ai/install.sh | sh

        # Add Ollama to PATH if not already there
        if ! grep -q "ollama" ~/.bashrc 2>/dev/null; then
            echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
            export PATH="$PATH:$HOME/.local/bin"
        fi

        print_success "Ollama installed successfully"
    fi

    # Start Ollama service
    print_status "Starting Ollama service..."
    ollama serve &
    sleep 5

    # Pull recommended models
    print_status "Pulling recommended Ollama models..."
    models=("llama3.1:8b" "llama3.1:70b" "codellama:13b" "mistral:7b")

    for model in "${models[@]}"; do
        print_status "Pulling $model..."
        if ollama pull "$model"; then
            print_success "$model pulled successfully"
        else
            print_warning "Failed to pull $model"
        fi
    done

    # List available models
    print_status "Available Ollama models:"
    ollama list
}

# Function to setup configuration
setup_configuration() {
    print_status "Setting up configuration..."

    if [ ! -f "config.json" ]; then
        if [ -f "config.example.json" ]; then
            cp config.example.json config.json
            print_success "Configuration file created from example"
        else
            print_warning "No example configuration found. You'll need to create config.json manually."
        fi
    else
        print_warning "Configuration file already exists"
    fi

    # Create enhanced configuration if it doesn't exist
    if [ ! -f "enhanced_config.json" ]; then
        print_status "Creating enhanced configuration template..."
        $PYTHON_CMD -c "
from enhanced_research_engine import ConfigurationManager
ConfigurationManager.create_enhanced_config_template()
print('Enhanced configuration template created')
"
    fi
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."

    # Test database setup
    $PYTHON_CMD -c "
try:
    from enhanced_research_engine import EnhancedLegitimateResearchEngine
    engine = EnhancedLegitimateResearchEngine()
    print('Database setup completed successfully')
except Exception as e:
    print(f'Database setup failed: {e}')
    exit(1)
"
}

# Function to run tests
run_tests() {
    print_status "Running system tests..."

    if [ -f "test_ai_system.py" ]; then
        print_status "Running AI system tests..."
        $PYTHON_CMD test_ai_system.py
    else
        print_warning "Test file not found. Skipping tests."
    fi
}

# Function to show usage information
show_usage() {
    echo
    echo "AI-Enhanced Background Research System Setup Complete!"
    echo "=================================================="
    echo
    echo "Next steps:"
    echo "1. Edit config.json with your API keys"
    echo "2. Activate the virtual environment: source venv/bin/activate"
    echo "3. Run the enhanced system: python enhanced_main.py --help"
    echo "4. Test the AI capabilities: python test_ai_system.py"
    echo
    echo "Available commands:"
    echo "  python enhanced_main.py --list-workflows"
    echo "  python enhanced_main.py --show-metrics"
    echo "  python enhanced_main.py --run-examples"
    echo
    echo "Documentation:"
    echo "  - README_AI_ENHANCED.md - Complete AI system documentation"
    echo "  - README.md - Original system documentation"
    echo
}

# Function to check API keys
check_api_keys() {
    print_status "Checking API key configuration..."

    if [ -f "config.json" ]; then
        # Check for placeholder API keys
        if grep -q "YOUR_.*_API_KEY" config.json; then
            print_warning "Some API keys are still using placeholder values:"
            grep "YOUR_.*_API_KEY" config.json | sed 's/.*"\(YOUR_.*_API_KEY\)".*/- \1/'
            echo
            print_status "Please edit config.json and add your actual API keys:"
            echo "  - OpenAI API key: https://platform.openai.com/"
            echo "  - Anthropic API key: https://console.anthropic.com/"
            echo "  - Other service API keys as needed"
        else
            print_success "API keys appear to be configured"
        fi
    fi
}

# Main setup function
main() {
    echo "AI-Enhanced Background Research System Setup"
    echo "=========================================="
    echo

    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        print_error "Please run this script from the background_research_system directory"
        exit 1
    fi

    # Check system requirements
    check_system_requirements

    # Create virtual environment
    create_virtual_environment

    # Install Python dependencies
    install_python_dependencies

    # Install Ollama
    install_ollama

    # Setup configuration
    setup_configuration

    # Setup database
    setup_database

    # Check API keys
    check_api_keys

    # Run tests (optional)
    read -p "Would you like to run the system tests now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi

    # Show usage information
    show_usage

    print_success "Setup completed successfully!"
}

# Function to cleanup on exit
cleanup() {
    # Stop Ollama service if it was started by this script
    if pgrep -f "ollama serve" > /dev/null; then
        print_status "Stopping Ollama service..."
        pkill -f "ollama serve"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"
