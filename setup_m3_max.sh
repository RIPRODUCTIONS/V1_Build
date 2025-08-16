#!/bin/bash
# M3 Max macOS Development Environment Setup
# Optimized for MacBook Pro M3 Max with 48GB RAM

set -e  # Exit on any error

echo "🚀 Setting up AI Framework for M3 Max MacBook Pro"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on Apple Silicon
check_apple_silicon() {
    if [[ $(uname -m) != "arm64" ]]; then
        print_error "This script is optimized for Apple Silicon (M3 Max). Detected: $(uname -m)"
        exit 1
    fi
    print_status "Confirmed running on Apple Silicon"
}

# Check macOS version
check_macos_version() {
    local version=$(sw_vers -productVersion)
    local major=$(echo $version | cut -d. -f1)

    if [[ $major -lt 13 ]]; then
        print_warning "macOS 13+ recommended for best M3 Max performance. Current: $version"
    else
        print_status "macOS version: $version"
    fi
}

# Install or update Homebrew
setup_homebrew() {
    print_info "Setting up Homebrew for M3 Max..."

    if ! command -v brew &> /dev/null; then
        print_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for M1/M2/M3 Macs
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        print_status "Homebrew already installed"
        brew update
    fi
}

# Install development tools optimized for M3 Max
install_dev_tools() {
    print_info "Installing development tools optimized for M3 Max..."

    # Essential development tools
    brew install --quiet \
        git \
        curl \
        wget \
        tree \
        htop \
        jq \
        yq \
        bat \
        fd \
        ripgrep \
        tldr

    print_status "Development tools installed"
}

# Install Python with optimizations
setup_python() {
    print_info "Setting up Python for M3 Max performance..."

    # Install Python via Homebrew (optimized for Apple Silicon)
    brew install python@3.11

    # Create symbolic links
    ln -sf /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3
    ln -sf /opt/homebrew/bin/pip3.11 /opt/homebrew/bin/pip3

    # Upgrade pip
    python3 -m pip install --upgrade pip

    # Install Poetry for dependency management
    curl -sSL https://install.python-poetry.org | python3 -
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile

    print_status "Python 3.11 installed and configured"
}

# Install Docker Desktop for Mac
setup_docker() {
    print_info "Setting up Docker Desktop for M3 Max..."

    if ! command -v docker &> /dev/null; then
        print_info "Installing Docker Desktop..."
        brew install --cask docker

        # Wait for Docker to start
        print_info "Starting Docker Desktop..."
        open /Applications/Docker.app

        # Wait for Docker daemon to be ready
        print_info "Waiting for Docker daemon..."
        while ! docker info &> /dev/null; do
            sleep 2
        done

        print_status "Docker Desktop installed and running"
    else
        print_status "Docker already installed"
        docker --version
    fi
}

# Install Node.js and npm
setup_nodejs() {
    print_info "Setting up Node.js for M3 Max..."

    if ! command -v node &> /dev/null; then
        brew install node@18

        # Create symbolic links
        ln -sf /opt/homebrew/bin/node18 /opt/homebrew/bin/node
        ln -sf /opt/homebrew/bin/npm18 /opt/homebrew/bin/npm

        print_status "Node.js 18 installed"
    else
        print_status "Node.js already installed"
        node --version
    fi
}

# Install Redis
setup_redis() {
    print_info "Setting up Redis for M3 Max..."

    if ! command -v redis-server &> /dev/null; then
        brew install redis

        # Start Redis service
        brew services start redis

        print_status "Redis installed and started"
    else
        print_status "Redis already installed"
        brew services restart redis
    fi
}

# Install PostgreSQL
setup_postgresql() {
    print_info "Setting up PostgreSQL for M3 Max..."

    if ! command -v psql &> /dev/null; then
        brew install postgresql@15

        # Start PostgreSQL service
        brew services start postgresql@15

        # Create symbolic links
        ln -sf /opt/homebrew/opt/postgresql@15/bin/psql /opt/homebrew/bin/psql
        ln -sf /opt/homebrew/opt/postgresql@15/bin/pg_ctl /opt/homebrew/bin/pg_ctl

        print_status "PostgreSQL 15 installed and started"
    else
        print_status "PostgreSQL already installed"
        brew services restart postgresql@15
    fi
}

# Install monitoring tools
setup_monitoring() {
    print_info "Setting up monitoring tools for M3 Max..."

    # Install Prometheus
    brew install prometheus

    # Install Grafana
    brew install grafana

    # Start services
    brew services start prometheus
    brew services start grafana

    print_status "Monitoring tools installed and started"
}

# Setup AI Framework environment
setup_ai_framework() {
    print_info "Setting up AI Framework environment..."

    # Navigate to AI framework directory
    cd ai_framework

    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    print_info "Installing AI Framework dependencies..."
    pip install -r requirements.txt

    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi

    # Install additional M3 Max optimized packages
    pip install \
        numpy \
        pandas \
        scikit-learn \
        matplotlib \
        seaborn \
        jupyter \
        ipykernel

    # Register kernel for Jupyter
    python -m ipykernel install --user --name=ai_framework --display-name="AI Framework (M3 Max)"

    print_status "AI Framework environment setup complete"
}

# Setup development tools
setup_dev_tools() {
    print_info "Setting up development tools..."

    # Install pre-commit hooks
    if command -v pre-commit &> /dev/null; then
        cd ai_framework
        pre-commit install
        print_status "Pre-commit hooks installed"
    fi

    # Install VS Code extensions (if VS Code is installed)
    if command -v code &> /dev/null; then
        print_info "Installing VS Code extensions..."
        code --install-extension ms-python.python
        code --install-extension ms-python.black-formatter
        code --install-extension ms-python.isort
        code --install-extension ms-python.flake8
        code --install-extension ms-python.mypy-type-checker
        code --install-extension ms-vscode.vscode-json
        code --install-extension redhat.vscode-yaml
        code --install-extension ms-vscode.vscode-docker
        print_status "VS Code extensions installed"
    fi
}

# Setup environment variables
setup_env() {
    print_info "Setting up environment variables..."

    # Create .env file if it doesn't exist
    if [ ! -f "ai_framework/.env" ]; then
        cat > ai_framework/.env << EOF
# AI Framework Environment Configuration
# Optimized for M3 Max MacBook Pro

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=ai_framework.db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# PostgreSQL Configuration (if using)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_framework
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Development
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# M3 Max Optimizations
PYTHONOPTIMIZE=1
PYTHONUNBUFFERED=1
EOF
        print_status "Environment file created"
    else
        print_status "Environment file already exists"
    fi
}

# Setup database
setup_database() {
    print_info "Setting up database..."

    cd ai_framework

    # Activate virtual environment
    source venv/bin/activate

    # Initialize database
    if [ -f "migrations/env.py" ]; then
        print_info "Initializing database with Alembic..."
        alembic upgrade head
        print_status "Database initialized"
    else
        print_info "Creating initial database..."
        python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Database tables created')
"
        print_status "Database tables created"
    fi
}

# Performance optimizations for M3 Max
optimize_performance() {
    print_info "Applying M3 Max performance optimizations..."

    # Create performance tuning script
    cat > ai_framework/scripts/optimize_m3_max.py << 'EOF'
#!/usr/bin/env python3
"""
M3 Max Performance Optimization Script
Optimizes Python and system settings for M3 Max MacBook Pro
"""

import os
import sys
import multiprocessing
import psutil

def optimize_python_settings():
    """Optimize Python settings for M3 Max."""
    optimizations = {
        'PYTHONOPTIMIZE': '1',
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONHASHSEED': 'random',
        'PYTHONPATH': os.getcwd(),
    }

    for key, value in optimizations.items():
        os.environ[key] = value
        print(f"Set {key}={value}")

def optimize_system_settings():
    """Optimize system settings for M3 Max."""
    # Get CPU count (M3 Max has 16 cores)
    cpu_count = multiprocessing.cpu_count()
    print(f"CPU cores detected: {cpu_count}")

    # Optimize for M3 Max
    if cpu_count >= 16:
        os.environ['OMP_NUM_THREADS'] = str(cpu_count)
        os.environ['MKL_NUM_THREADS'] = str(cpu_count)
        os.environ['OPENBLAS_NUM_THREADS'] = str(cpu_count)
        print("Applied multi-threading optimizations for M3 Max")

    # Memory optimization (48GB RAM)
    memory_gb = psutil.virtual_memory().total / (1024**3)
    if memory_gb >= 32:
        os.environ['PYTHONMALLOC'] = 'malloc'
        print(f"Applied memory optimizations for {memory_gb:.1f}GB RAM")

def main():
    """Main optimization function."""
    print("🚀 Applying M3 Max Performance Optimizations")
    print("=" * 50)

    optimize_python_settings()
    optimize_system_settings()

    print("\n✅ M3 Max optimizations applied successfully!")
    print("\nPerformance tips:")
    print("- Use async/await for I/O operations")
    print("- Leverage multiprocessing for CPU-intensive tasks")
    print("- Monitor memory usage with 48GB RAM")
    print("- Use vectorized operations with NumPy/Pandas")

if __name__ == "__main__":
    main()
EOF

    # Make script executable
    chmod +x ai_framework/scripts/optimize_m3_max.py

    print_status "Performance optimization script created"
}

# Run health checks
run_health_checks() {
    print_info "Running health checks..."

    # Check Python
    if command -v python3 &> /dev/null; then
        print_status "Python: $(python3 --version)"
    else
        print_error "Python not found"
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        print_status "Docker: $(docker --version)"
        if docker info &> /dev/null; then
            print_status "Docker daemon: Running"
        else
            print_error "Docker daemon: Not running"
        fi
    else
        print_error "Docker not found"
    fi

    # Check Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_status "Redis: Running"
        else
            print_error "Redis: Not running"
        fi
    else
        print_error "Redis not found"
    fi

    # Check PostgreSQL
    if command -v psql &> /dev/null; then
        if pg_isready -h localhost &> /dev/null; then
            print_status "PostgreSQL: Running"
        else
            print_error "PostgreSQL: Not running"
        fi
    else
        print_error "PostgreSQL not found"
    fi

    # Check Node.js
    if command -v node &> /dev/null; then
        print_status "Node.js: $(node --version)"
    else
        print_error "Node.js not found"
    fi
}

# Main setup function
main() {
    echo "🚀 Starting M3 Max AI Framework Setup"
    echo "====================================="

    # Check system requirements
    check_apple_silicon
    check_macos_version

    # Install core tools
    setup_homebrew
    install_dev_tools
    setup_python
    setup_docker
    setup_nodejs
    setup_redis
    setup_postgresql
    setup_monitoring

    # Setup AI Framework
    setup_ai_framework
    setup_env
    setup_database
    setup_dev_tools
    optimize_performance

    # Run health checks
    run_health_checks

    echo ""
    echo "🎉 M3 Max AI Framework Setup Complete!"
    echo "====================================="
    echo ""
    echo "Next steps:"
    echo "1. Navigate to ai_framework directory: cd ai_framework"
    echo "2. Activate virtual environment: source venv/bin/activate"
    echo "3. Run performance optimization: python scripts/optimize_m3_max.py"
    echo "4. Start the AI Framework: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    echo "Services running:"
    echo "- Redis: localhost:6379"
    echo "- PostgreSQL: localhost:5432"
    echo "- Prometheus: localhost:9090"
    echo "- Grafana: localhost:3000"
    echo ""
    echo "Happy coding on your M3 Max! 🚀"
}

# Run main function
main "$@"
