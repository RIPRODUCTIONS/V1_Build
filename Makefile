# Kali Linux Complete Tools Automation Platform
# Comprehensive Makefile for platform management

.PHONY: help build start stop restart status logs clean test deploy update backup restore health-check monitor scale security-audit

# Default target
help:
	@echo "🚀 Kali Linux Complete Tools Automation Platform"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  build          - Build all Docker images"
	@echo "  start          - Start all services"
	@echo "  stop           - Stop all services"
	@echo "  restart        - Restart all services"
	@echo "  status         - Show service status"
	@echo "  logs           - Show service logs"
	@echo "  clean          - Clean up containers and volumes"
	@echo "  test           - Run tests"
	@echo "  deploy         - Deploy to production"
	@echo "  update         - Update platform and tools"
	@echo "  backup         - Backup data and configurations"
	@echo "  restore        - Restore from backup"
	@echo "  health-check   - Check system health"
	@echo "  monitor        - Start monitoring dashboard"
	@echo "  scale          - Scale services"
	@echo "  security-audit - Run security audit"
	@echo "  help           - Show this help message"
	@echo ""

# Build all Docker images
build:
	@echo "🔨 Building Kali Linux automation platform..."
	docker-compose -f docker-compose.kali.yml build --no-cache
	@echo "✅ Build completed successfully!"

# Start all services
start:
	@echo "🚀 Starting Kali Linux automation platform..."
	docker-compose -f docker-compose.kali.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 30
	@echo "✅ Platform started successfully!"
	@echo "🌐 Access points:"
	@echo "   Main API: http://localhost:8000"
	@echo "   Web UI: http://localhost:8001"
	@echo "   Grafana: http://localhost:3000 (admin/kali_admin)"
	@echo "   Kibana: http://localhost:5601"
	@echo "   Prometheus: http://localhost:9090"

# Stop all services
stop:
	@echo "🛑 Stopping Kali Linux automation platform..."
	docker-compose -f docker-compose.kali.yml down
	@echo "✅ Platform stopped successfully!"

# Restart all services
restart: stop start

# Show service status
status:
	@echo "📊 Kali Linux automation platform status:"
	docker-compose -f docker-compose.kali.yml ps
	@echo ""
	@echo "🔍 Resource usage:"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Show service logs
logs:
	@echo "📝 Showing service logs (Ctrl+C to exit):"
	docker-compose -f docker-compose.kali.yml logs -f

# Show logs for specific service
logs-%:
	@echo "📝 Showing logs for $*:"
	docker-compose -f docker-compose.kali.yml logs -f $*

# Clean up containers and volumes
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose -f docker-compose.kali.yml down -v
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed successfully!"

# Run tests
test:
	@echo "🧪 Running tests..."
	@if [ -d "tests" ]; then \
		python -m pytest tests/ -v --cov=kali_automation --cov-report=html; \
	else \
		echo "⚠️  No tests directory found. Creating basic test structure..."; \
		mkdir -p tests/{unit,integration,performance}; \
		echo "✅ Test structure created!"; \
	fi

# Deploy to production
deploy:
	@echo "🚀 Deploying to production..."
	@if [ -f "docker-compose.kali.prod.yml" ]; then \
		docker-compose -f docker-compose.kali.prod.yml up -d; \
	else \
		echo "⚠️  Production compose file not found. Using development configuration..."; \
		docker-compose -f docker-compose.kali.yml up -d; \
	fi
	@echo "✅ Deployment completed!"

# Update platform and tools
update:
	@echo "🔄 Updating Kali Linux automation platform..."
	git pull origin main
	docker-compose -f docker-compose.kali.yml pull
	docker-compose -f docker-compose.kali.yml build --no-cache
	docker-compose -f docker-compose.kali.yml up -d
	@echo "✅ Update completed successfully!"

# Backup data and configurations
backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@tar -czf backups/$(shell date +%Y%m%d_%H%M%S)/kali_automation_backup.tar.gz \
		--exclude=backups \
		--exclude=node_modules \
		--exclude=.git \
		--exclude=*.pyc \
		--exclude=__pycache__ \
		.
	@echo "✅ Backup created: backups/$(shell date +%Y%m%d_%H%M%S)/kali_automation_backup.tar.gz"

# Restore from backup
restore:
	@echo "📥 Restoring from backup..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify backup file: make restore BACKUP_FILE=backups/YYYYMMDD_HHMMSS/kali_automation_backup.tar.gz"; \
		exit 1; \
	fi
	@if [ ! -f "$(BACKUP_FILE)" ]; then \
		echo "❌ Backup file not found: $(BACKUP_FILE)"; \
		exit 1; \
	fi
	@echo "🔄 Stopping services..."
	docker-compose -f docker-compose.kali.yml down
	@echo "📥 Extracting backup..."
	tar -xzf $(BACKUP_FILE)
	@echo "🚀 Starting services..."
	docker-compose -f docker-compose.kali.yml up -d
	@echo "✅ Restore completed successfully!"

# Check system health
health-check:
	@echo "🏥 Checking system health..."
	@echo "🔍 Checking Docker services..."
	@docker-compose -f docker-compose.kali.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "🔍 Checking service health endpoints..."
	@curl -s http://localhost:8005/health || echo "❌ Main API health check failed"
	@curl -s http://localhost:8001/health || echo "❌ Web UI health check failed"
	@curl -s http://localhost:3000/api/health || echo "❌ Grafana health check failed"
	@curl -s http://localhost:5601/api/status || echo "❌ Kibana health check failed"
	@curl -s http://localhost:9090/-/healthy || echo "❌ Prometheus health check failed"
	@echo ""
	@echo "🔍 Checking resource usage..."
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Start monitoring dashboard
monitor:
	@echo "📊 Opening monitoring dashboards..."
	@echo "🌐 Opening Grafana dashboard..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:3000; \
	elif command -v open > /dev/null; then \
		open http://localhost:3000; \
	else \
		echo "🌐 Grafana: http://localhost:3000 (admin/kali_admin)"; \
	fi
	@echo "🌐 Opening Kibana dashboard..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:5601; \
	elif command -v open > /dev/null; then \
		open http://localhost:5601; \
	else \
		echo "🌐 Kibana: http://localhost:5601"; \
	fi
	@echo "🌐 Opening Prometheus dashboard..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:9090; \
	elif command -v open > /dev/null; then \
		open http://localhost:9090; \
	else \
		echo "🌐 Prometheus: http://localhost:9090"; \
	fi

# Scale services
scale:
	@echo "📈 Scaling services..."
	@if [ -z "$(SERVICE)" ] || [ -z "$(REPLICAS)" ]; then \
		echo "❌ Please specify service and replicas: make scale SERVICE=kali-worker REPLICAS=3"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.kali.yml up -d --scale $(SERVICE)=$(REPLICAS)
	@echo "✅ Scaled $(SERVICE) to $(REPLICAS) replicas!"

# Run security audit
security-audit:
	@echo "🔒 Running security audit..."
	@echo "🔍 Checking for security vulnerabilities in dependencies..."
	@if command -v safety > /dev/null; then \
		safety check; \
	else \
		echo "⚠️  Safety not installed. Installing..."; \
		pip install safety; \
		safety check; \
	fi
	@echo ""
	@echo "🔍 Checking Docker images for vulnerabilities..."
	@if command -v trivy > /dev/null; then \
		echo "🔍 Scanning main image..."; \
		trivy image kali-automation:latest; \
	else \
		echo "⚠️  Trivy not installed. Install for vulnerability scanning."; \
	fi
	@echo ""
	@echo "🔍 Checking file permissions..."
	@find . -type f -executable -exec ls -la {} \;
	@echo ""
	@echo "🔍 Checking for sensitive files..."
	@find . -name "*.key" -o -name "*.pem" -o -name "*.p12" -o -name "*.pfx" -o -name "*.crt" -o -name "*.env" -o -name "config.ini" -o -name "secrets.yml" 2>/dev/null || echo "✅ No sensitive files found in current directory"

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-dev.txt || echo "⚠️  requirements-dev.txt not found, installing basic dev packages..."
	pip install pytest pytest-cov pytest-asyncio black flake8 isort mypy pre-commit
	@echo "✅ Development dependencies installed!"

# Setup development environment
setup-dev: install-dev
	@echo "🔧 Setting up development environment..."
	@if [ ! -f ".pre-commit-config.yaml" ]; then \
		echo "📝 Creating pre-commit configuration..."; \
		echo "repos:" > .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/pre-commit/pre-commit-hooks" >> .pre-commit-config.yaml; \
		echo "    rev: v4.4.0" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: trailing-whitespace" >> .pre-commit-config.yaml; \
		echo "      - id: end-of-file-fixer" >> .pre-commit-config.yaml; \
		echo "      - id: check-yaml" >> .pre-commit-config.yaml; \
		echo "      - id: check-added-large-files" >> .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/psf/black" >> .pre-commit-config.yaml; \
		echo "    rev: 23.3.0" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: black" >> .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/pycqa/isort" >> .pre-commit-config.yaml; \
		echo "    rev: 5.12.0" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: isort" >> .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/pycqa/flake8" >> .pre-commit-config.yaml; \
		echo "    rev: 6.0.0" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: flake8" >> .pre-commit-config.yaml; \
	fi
	pre-commit install
	@echo "✅ Development environment setup completed!"

# Run linting and formatting
lint:
	@echo "🔍 Running code quality checks..."
	@echo "📝 Formatting code with Black..."
	black kali_automation/ --check || black kali_automation/
	@echo "🔍 Running isort..."
	isort kali_automation/ --check-only || isort kali_automation/
	@echo "🔍 Running flake8..."
	flake8 kali_automation/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "✅ Code quality checks completed!"

# Create new tool
new-tool:
	@echo "🛠️  Creating new tool..."
	@if [ -z "$(TOOL_NAME)" ] || [ -z "$(CATEGORY)" ]; then \
		echo "❌ Please specify tool name and category: make new-tool TOOL_NAME=my_tool CATEGORY=information_gathering"; \
		exit 1; \
	fi
	@mkdir -p kali_automation/tools/$(CATEGORY)
	@echo "📝 Creating tool file: kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py"
	@echo "#!/usr/bin/env python3" > kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo '"""$(TOOL_NAME): Tool description."""' >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "from kali_automation.tools.base import BaseKaliTool" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "class $(shell echo $(TOOL_NAME) | sed 's/_\([a-z]\)/\U\1/g' | sed 's/^\([a-z]\)/\U\1/')Tool(BaseKaliTool):" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo '    """$(TOOL_NAME) tool implementation."""' >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "    def __init__(self):" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "        super().__init__(" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo '            name="$(TOOL_NAME)",' >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo '            description="$(TOOL_NAME) tool description",' >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo '            category="$(CATEGORY)"' >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "        )" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "        self.required_packages = []" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "    async def execute(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo '        """Execute $(TOOL_NAME) tool."""' >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "        # TODO: Implement tool execution" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "        pass" >> kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py
	@echo "✅ Tool created: kali_automation/tools/$(CATEGORY)/$(TOOL_NAME).py"

# Show platform information
info:
	@echo "ℹ️  Kali Linux automation platform information:"
	@echo "================================================"
	@echo "🔧 Platform version: $(shell git describe --tags 2>/dev/null || echo 'Development version')"
	@echo "🐳 Docker version: $(shell docker --version)"
	@echo "🐳 Docker Compose version: $(shell docker-compose --version)"
	@echo "🐍 Python version: $(shell python3 --version 2>/dev/null || echo 'Python not found')"
	@echo ""
	@echo "📊 Service status:"
	@docker-compose -f docker-compose.kali.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "💾 Disk usage:"
	@df -h . | tail -1
	@echo ""
	@echo "🧠 Memory usage:"
	@free -h | grep "Mem:"

# Emergency stop (force kill all containers)
emergency-stop:
	@echo "🚨 EMERGENCY STOP - Force killing all containers..."
	docker kill $$(docker ps -q) 2>/dev/null || echo "No containers running"
	docker system prune -f
	@echo "✅ Emergency stop completed!"

# Show real-time monitoring
monitor-realtime:
	@echo "📊 Real-time monitoring (Ctrl+C to exit):"
	@echo "🔍 Container stats:"
	watch -n 2 'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"'

# Create production configuration
create-prod-config:
	@echo "🏭 Creating production configuration..."
	@if [ ! -f "docker-compose.kali.prod.yml" ]; then \
		cp docker-compose.kali.yml docker-compose.kali.prod.yml; \
		echo "✅ Production configuration created!"; \
		echo "⚠️  Please review and customize docker-compose.kali.prod.yml for production use"; \
	else \
		echo "⚠️  Production configuration already exists!"; \
	fi

# Show help for specific command
help-%:
	@echo "Help for command: $*"
	@echo "=================="
	@case $* in \
		build) echo "Build all Docker images for the platform"; \
		       echo "Usage: make build"; \
		       echo "This will build all services defined in docker-compose.kali.yml"; \
		       ;; \
		start) echo "Start all platform services"; \
		       echo "Usage: make start"; \
		       echo "This will start all services and show access URLs"; \
		       ;; \
		stop) echo "Stop all platform services"; \
		      echo "Usage: make stop"; \
		      echo "This will gracefully stop all services"; \
		      ;; \
		*) echo "No specific help available for $*"; \
		   echo "Run 'make help' for general help"; \
		   ;; \
	esac
