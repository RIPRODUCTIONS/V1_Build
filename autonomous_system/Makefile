# Autonomous Task Solver System - Makefile
# Common operations and shortcuts

.PHONY: help install install-dev test lint format clean build run demo docker-build docker-up docker-down docker-logs docker-shell docker-clean deploy-staging deploy-production

# Default target
help:
	@echo "🤖 Autonomous Task Solver System - Available Commands"
	@echo "=================================================="
	@echo ""
	@echo "📦 Installation:"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "🧪 Development:"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linting and code quality checks"
	@echo "  format         - Format code with black and isort"
	@echo "  clean          - Clean generated files and caches"
	@echo ""
	@echo "🚀 Running:"
	@echo "  run            - Start the system locally"
	@echo "  demo           - Run the quick start demo"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build   - Build Docker images"
	@echo "  docker-up      - Start Docker services"
	@echo "  docker-down    - Stop Docker services"
	@echo "  docker-logs    - View Docker logs"
	@echo "  docker-shell   - Open shell in running container"
	@echo "  docker-clean   - Clean Docker resources"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  deploy-staging    - Deploy to staging environment"
	@echo "  deploy-production - Deploy to production environment"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  status         - Check system status"
	@echo "  health         - Run health checks"
	@echo "  logs           - View system logs"
	@echo ""
	@echo "🔧 Utilities:"
	@echo "  setup          - Initial setup and configuration"
	@echo "  backup         - Backup system data"
	@echo "  restore        - Restore system data"

# Installation
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-dev: install
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements-dev.txt

# Development
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=autonomous_system --cov-report=html

lint:
	@echo "🔍 Running linting and code quality checks..."
	flake8 autonomous_system/
	mypy autonomous_system/
	bandit -r autonomous_system/
	safety check

format:
	@echo "✨ Formatting code..."
	black autonomous_system/
	isort autonomous_system/

clean:
	@echo "🧹 Cleaning generated files and caches..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "*.log" -delete

# Running
run:
	@echo "🚀 Starting Autonomous Task Solver System..."
	python -m autonomous_system.autonomous_orchestrator

demo:
	@echo "🎬 Running Quick Start Demo..."
	python quick_start.py

# Docker operations
docker-build:
	@echo "🐳 Building Docker images..."
	docker build -f docker/Dockerfile -t autonomous-system:latest .
	docker build -f docker/Dockerfile -t autonomous-system:dev --target development .

docker-up:
	@echo "🚀 Starting Docker services..."
	docker-compose -f docker/docker-compose.yml up -d

docker-up-dev:
	@echo "🚀 Starting development services..."
	docker-compose -f docker/docker-compose.yml --profile dev up -d

docker-up-prod:
	@echo "🚀 Starting production services..."
	docker-compose -f docker/docker-compose.yml --profile production up -d

docker-up-monitoring:
	@echo "📊 Starting monitoring services..."
	docker-compose -f docker/docker-compose.yml --profile monitoring up -d

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose -f docker/docker-compose.yml logs -f

docker-logs-system:
	@echo "📋 Viewing system logs..."
	docker-compose -f docker/docker-compose.yml logs -f autonomous-system

docker-shell:
	@echo "🐚 Opening shell in running container..."
	docker-compose -f docker/docker-compose.yml exec autonomous-system /bin/bash

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose -f docker/docker-compose.yml down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

# Deployment
deploy-staging:
	@echo "🚀 Deploying to staging environment..."
	@echo "This would deploy to staging - implement as needed"
	# Add your staging deployment logic here

deploy-production:
	@echo "🚀 Deploying to production environment..."
	@echo "This would deploy to production - implement as needed"
	# Add your production deployment logic here

# Monitoring
status:
	@echo "📊 Checking system status..."
	@if [ -f "scripts/start.sh" ]; then \
		./scripts/start.sh status; \
	else \
		echo "Status script not found"; \
	fi

health:
	@echo "🏥 Running health checks..."
	@if [ -f "scripts/healthcheck.sh" ]; then \
		./scripts/healthcheck.sh check; \
	else \
		echo "Health check script not found"; \
	fi

logs:
	@echo "📋 Viewing system logs..."
	@if [ -d "logs" ]; then \
		tail -f logs/*.log; \
	else \
		echo "Logs directory not found"; \
	fi

# Utilities
setup:
	@echo "🔧 Setting up Autonomous Task Solver System..."
	@echo "1. Installing dependencies..."
	$(MAKE) install-dev
	@echo "2. Creating configuration..."
	@if [ ! -f "config/config.yaml" ]; then \
		echo "Configuration file not found. Please create config/config.yaml"; \
	else \
		echo "Configuration file exists"; \
	fi
	@echo "3. Setting up directories..."
	mkdir -p data/databases data/logs data/cache data/models
	@echo "4. Setting permissions..."
	chmod +x scripts/*.sh
	@echo "✅ Setup completed!"

backup:
	@echo "💾 Creating backup..."
	@if [ -d "data" ]; then \
		tar -czf "backup_$(date +%Y%m%d_%H%M%S).tar.gz" data/; \
		echo "Backup created: backup_$(date +%Y%m%d_%H%M%S).tar.gz"; \
	else \
		echo "Data directory not found"; \
	fi

restore:
	@echo "📥 Restoring from backup..."
	@if [ -f "$(BACKUP_FILE)" ]; then \
		tar -xzf "$(BACKUP_FILE)"; \
		echo "Restore completed from $(BACKUP_FILE)"; \
	else \
		echo "Please specify BACKUP_FILE=<filename>"; \
		echo "Example: make restore BACKUP_FILE=backup_20241201_120000.tar.gz"; \
	fi

# Development workflow
dev-setup: install-dev setup
	@echo "🔧 Development environment setup completed!"

dev-test: format lint test
	@echo "✅ Development checks completed!"

dev-run: dev-test run
	@echo "🚀 Development system started!"

# Production workflow
prod-setup: install setup
	@echo "🔧 Production environment setup completed!"

prod-deploy: prod-setup docker-build docker-up-prod
	@echo "🚀 Production deployment completed!"

# Quick actions
quick-start: setup demo
	@echo "🎬 Quick start completed!"

full-deploy: clean install-dev docker-build docker-up-monitoring
	@echo "🚀 Full deployment with monitoring completed!"

# System management
start:
	@echo "🚀 Starting system..."
	@if [ -f "scripts/start.sh" ]; then \
		./scripts/start.sh start; \
	else \
		echo "Start script not found"; \
	fi

stop:
	@echo "🛑 Stopping system..."
	@if [ -f "scripts/start.sh" ]; then \
		./scripts/start.sh stop; \
	else \
		echo "Start script not found"; \
	fi

restart:
	@echo "🔄 Restarting system..."
	@if [ -f "scripts/start.sh" ]; then \
		./scripts/start.sh restart; \
	else \
		echo "Start script not found"; \
	fi

# Database operations
db-init:
	@echo "🗄️  Initializing database..."
	python -c "from autonomous_system.discovery.task_detector import TaskDetector; TaskDetector({})._init_database()"

db-reset:
	@echo "🗄️  Resetting database..."
	rm -f data/databases/*.db
	$(MAKE) db-init

# Performance testing
perf-test:
	@echo "⚡ Running performance tests..."
	pytest tests/ -m "performance" -v

load-test:
	@echo "📈 Running load tests..."
	python -m autonomous_system.tests.load_test

# Security checks
security-check:
	@echo "🔒 Running security checks..."
	bandit -r autonomous_system/
	safety check
	@echo "Security checks completed!"

# Documentation
docs:
	@echo "📚 Building documentation..."
	cd docs && make html
	@echo "Documentation built in docs/_build/html/"

docs-serve:
	@echo "📚 Serving documentation..."
	cd docs/_build/html && python -m http.server 8000

# Maintenance
maintenance:
	@echo "🔧 Running maintenance tasks..."
	$(MAKE) clean
	$(MAKE) docker-clean
	$(MAKE) install-dev
	@echo "Maintenance completed!"

# Show system info
info:
	@echo "🤖 Autonomous Task Solver System Information"
	@echo "=========================================="
	@echo "Python version: $(shell python --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Docker version: $(shell docker --version 2>/dev/null || echo 'Docker not installed')"
	@echo "Docker Compose version: $(shell docker-compose --version 2>/dev/null || echo 'Docker Compose not installed')"
	@echo "Current directory: $(PWD)"
	@echo "Available disk space: $(shell df -h . | tail -1 | awk '{print $$4}')"
	@echo "Memory usage: $(shell free -h | grep Mem | awk '{print $$3"/"$$2}')"

# Default target
.DEFAULT_GOAL := help
