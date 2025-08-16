# Makefile for Background Research System

.PHONY: help install test clean run-example setup-dev lint format

# Default target
help:
	@echo "Background Research System - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install      - Install dependencies"
	@echo "  setup-dev    - Setup development environment"
	@echo ""
	@echo "Testing:"
	@echo "  test         - Run all tests"
	@echo "  test-basic   - Run basic functionality tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo ""
	@echo "Usage:"
	@echo "  run-example  - Run example research"
	@echo "  list-purposes- Show available legitimate purposes"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        - Clean up generated files"
	@echo "  cleanup-data - Clean up old data based on retention policy"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip3 install -r requirements.txt
	@echo "Dependencies installed successfully!"

# Setup development environment
setup-dev:
	@echo "Setting up development environment..."
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt
	pre-commit install
	@echo "Development environment setup complete!"

# Run tests
test:
	@echo "Running all tests..."
	python3 test_system.py

test-basic:
	@echo "Running basic functionality tests..."
	python3 -c "from test_system import test_basic_functionality; test_basic_functionality()"

# Code quality checks
lint:
	@echo "Running linting checks..."
	flake8 .
	mypy .

format:
	@echo "Formatting code..."
	black .
	isort .

# Example usage
run-example:
	@echo "Running example research..."
	python3 main.py --name "John Doe" --location "New York, NY" --purpose employment_background_verification --user-id "test_user" --output example_report.json

list-purposes:
	@echo "Available legitimate purposes:"
	python3 main.py --list-purposes

# Cleanup
clean:
	@echo "Cleaning up generated files..."
	rm -f *.log
	rm -f *.db
	rm -f *.json
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	@echo "Cleanup complete!"

cleanup-data:
	@echo "Cleaning up old data based on retention policy..."
	python3 main.py --cleanup

# Database operations
init-db:
	@echo "Initializing database..."
	python3 -c "from core_system import DatabaseManager; db = DatabaseManager(); print('Database initialized')"

# System status
status:
	@echo "System Status:"
	@echo "Python version: $(shell python3 --version)"
	@echo "Pip version: $(shell pip3 --version)"
	@echo "Chrome available: $(shell which google-chrome || which chromium-browser || echo 'Not found')"
	@echo "Config file: $(shell if [ -f config.json ]; then echo 'Found'; else echo 'Not found'; fi)"

# Quick start
quick-start: install test
	@echo ""
	@echo "🎉 Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure your API keys in config.json"
	@echo "2. Review compliance requirements"
	@echo "3. Run: make run-example"
	@echo "4. Check: make status"

# Development workflow
dev: format lint test
	@echo "Development workflow complete!"

# Production preparation
prod-prep: clean install test lint
	@echo "Production preparation complete!"
	@echo "System is ready for production use!"

# Help for specific commands
help-install:
	@echo "Install Command Details:"
	@echo "  make install - Installs all required Python packages"
	@echo "  Requirements: Python 3.8+, pip, virtual environment recommended"
	@echo "  Files: requirements.txt"

help-test:
	@echo "Test Command Details:"
	@echo "  make test - Runs comprehensive system tests"
	@echo "  make test-basic - Runs basic functionality tests only"
	@echo "  Requirements: All dependencies must be installed"
	@echo "  Output: Test results displayed in terminal"

help-example:
	@echo "Example Usage Details:"
	@echo "  make run-example - Runs sample research for John Doe"
	@echo "  Output: example_report.json"
	@echo "  Purpose: employment_background_verification"
	@echo "  Note: Uses default configuration"

help-cleanup:
	@echo "Cleanup Command Details:"
	@echo "  make clean - Removes generated files and caches"
	@echo "  make cleanup-data - Removes old data based on retention policy"
	@echo "  Files removed: logs, databases, reports, Python caches"
	@echo "  Note: This is irreversible!"

# System information
info:
	@echo "Background Research System Information:"
	@echo "Version: 1.0.0"
	@echo "License: MIT"
	@echo "Author: AI Assistant"
	@echo ""
	@echo "Core Components:"
	@echo "- Public Records Search"
	@echo "- Commercial Data Aggregation"
	@echo "- Web Scraping (Public Only)"
	@echo "- Data Verification & Cross-Referencing"
	@echo "- Compliance & Audit Logging"
	@echo ""
	@echo "Legal Status: For legitimate business purposes only"
	@echo "Compliance: FCRA, GDPR, Privacy Laws"
