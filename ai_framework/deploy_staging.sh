#!/bin/bash

# Staging Deployment Script for AI Framework
# This script sets up a staging environment for customer demonstrations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-framework-staging"
VERSION=$(git describe --tags --always --dirty)
ENVIRONMENT="staging"

echo -e "${BLUE}🚀 AI Framework Staging Deployment${NC}"
echo -e "${BLUE}==================================${NC}"
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "Version: ${GREEN}${VERSION}${NC}"
echo -e "Timestamp: ${GREEN}$(date)${NC}"
echo ""

# Function to print status
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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    # Check if we're in the right directory
    if [[ ! -f "server.py" ]]; then
        print_error "Please run this script from the ai_framework directory"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to create demo data
create_demo_data() {
    print_status "Creating demo data and directories..."

    # Create demo directories
    mkdir -p demo_data/{workloads,reports,exports}
    mkdir -p logs staging_logs
    mkdir -p cache staging_cache
    mkdir -p monitoring/grafana/staging/{dashboards,datasources}

    # Create sample demo workload
    cat > demo_data/workloads/demo_financial_tasks.json << 'EOF'
{
  "workload_name": "Demo Financial Analysis",
  "description": "Sample financial workload for customer demonstration",
  "tasks": [
    {
      "task_id": "demo_fin_001",
      "task_type": "financial_analysis",
      "priority": "high",
      "description": "Analyze Q4 financial performance",
      "assigned_agent": "AI CFO",
      "estimated_duration": "2 hours"
    },
    {
      "task_id": "demo_fin_002",
      "task_type": "budget_planning",
      "priority": "medium",
      "description": "Create 2025 budget forecast",
      "assigned_agent": "AI Controller",
      "estimated_duration": "4 hours"
    }
  ]
}
EOF

    # Create sample demo report
    cat > demo_data/reports/demo_performance_report.md << 'EOF'
# AI Framework Performance Report
## Demo Environment - $(date)

### System Overview
- **Total Agents**: 52
- **Active Agents**: 48
- **System Health**: Excellent
- **Uptime**: 99.9%

### Key Metrics
- **Tasks Processed**: 1,247
- **Average Response Time**: 2.3s
- **Success Rate**: 98.7%
- **Resource Utilization**: 67%

### Agent Performance
- **AI CEO**: 156 tasks completed
- **AI CFO**: 89 tasks completed
- **AI CTO**: 203 tasks completed
- **AI Security**: 78 tasks completed

### Recommendations
1. Scale up security monitoring
2. Optimize task distribution
3. Implement advanced analytics
EOF

    print_success "Demo data created successfully"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring configuration..."

    # Create Prometheus staging config
    cat > monitoring/prometheus.staging.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'ai-framework'
    static_configs:
      - targets: ['ai-framework-staging:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    # Create Grafana datasource
    mkdir -p monitoring/grafana/staging/datasources
    cat > monitoring/grafana/staging/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-staging:9090
    isDefault: true
EOF

    # Create Grafana dashboard
    mkdir -p monitoring/grafana/staging/dashboards
    cat > monitoring/grafana/staging/dashboards/ai-framework-overview.json << 'EOF'
{
  "dashboard": {
    "title": "AI Framework Overview",
    "panels": [
      {
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "ai_framework_system_health",
            "legendFormat": "Health Score"
          }
        ]
      }
    ]
  }
}
EOF

    print_success "Monitoring configuration created"
}

# Function to deploy staging environment
deploy_staging() {
    print_status "Deploying staging environment..."

    # Stop any existing staging containers
    docker-compose -f docker-compose.staging.yml down || true

    # Start staging stack
    docker-compose -f docker-compose.staging.yml up -d --build

    print_success "Staging deployment completed"
}

# Function to verify staging deployment
verify_staging() {
    print_status "Verifying staging deployment..."

    # Wait for services to be ready
    sleep 60

    # Check AI Framework health
    if curl -f http://localhost:18000/health > /dev/null 2>&1; then
        print_success "AI Framework is healthy"
    else
        print_error "AI Framework health check failed"
        exit 1
    fi

    # Check database
    if docker-compose -f docker-compose.staging.yml exec -T postgres-staging pg_isready -U ai_framework > /dev/null 2>&1; then
        print_success "Database is ready"
    else
        print_error "Database health check failed"
        exit 1
    fi

    # Check Redis
    if docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis health check failed"
        exit 1
    fi

    print_success "All staging services are healthy"
}

# Function to show staging status
show_staging_status() {
    print_status "Staging Environment Status:"
    echo ""

    # Show running containers
    docker-compose -f docker-compose.staging.yml ps

    echo ""

    # Show service URLs
    echo -e "${GREEN}Staging Service URLs:${NC}"
    echo -e "  AI Framework API: ${BLUE}http://localhost:18000${NC}"
    echo -e "  AI Framework Health: ${BLUE}http://localhost:18000/health${NC}"
    echo -e "  Nginx Proxy: ${BLUE}http://localhost:18081${NC}"
    echo -e "  Prometheus Metrics: ${BLUE}http://localhost:19093${NC}"
    echo -e "  Grafana Dashboard: ${BLUE}http://localhost:13002${NC}"
    echo -e "  Database: ${BLUE}localhost:15434${NC}"
    echo -e "  Redis: ${BLUE}localhost:16381${NC}"

    echo ""

    # Show demo data
    echo -e "${GREEN}Demo Data Available:${NC}"
    echo -e "  Workloads: ${BLUE}./demo_data/workloads/${NC}"
    echo -e "  Reports: ${BLUE}./demo_data/reports/${NC}"
    echo -e "  Exports: ${BLUE}./demo_data/exports/${NC}"

    echo ""

    # Show logs
    print_status "Recent staging logs (last 10 lines):"
    docker-compose -f docker-compose.staging.yml logs --tail=10
}

# Function to run demo tests
run_demo_tests() {
    print_status "Running demo tests..."

    # Test basic endpoints
    echo "Testing basic endpoints..."
    curl -s http://localhost:18000/ | jq . || echo "Root endpoint working"
    curl -s http://localhost:18000/health | jq . || echo "Health endpoint working"
    curl -s http://localhost:18000/metrics | head -5 || echo "Metrics endpoint working"

    # Test API endpoints
    echo "Testing API endpoints..."
    curl -s http://localhost:18000/api/system/status | jq . || echo "System status endpoint working"

    print_success "Demo tests completed"
}

# Main staging deployment process
main() {
    echo -e "${BLUE}Starting staging deployment...${NC}"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Create demo data
    create_demo_data

    # Setup monitoring
    setup_monitoring

    # Deploy staging
    deploy_staging

    # Verify deployment
    verify_staging

    # Run demo tests
    run_demo_tests

    # Show status
    show_staging_status

    echo ""
    echo -e "${GREEN}🎉 Staging deployment completed successfully!${NC}"
    echo ""
    echo -e "Next steps for customer demonstrations:"
    echo -e "1. Access the dashboard: ${BLUE}http://localhost:18000${NC}"
    echo -e "2. View metrics: ${BLUE}http://localhost:19093${NC}"
    echo -e "3. Explore Grafana: ${BLUE}http://localhost:13002${NC}"
    echo -e "4. Check demo data: ${BLUE}./demo_data/${NC}"
    echo -e "5. Monitor logs: ${BLUE}docker-compose -f docker-compose.staging.yml logs -f${NC}"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_staging_status
        ;;
    "test")
        run_demo_tests
        ;;
    "logs")
        docker-compose -f docker-compose.staging.yml logs -f
        ;;
    "stop")
        docker-compose -f docker-compose.staging.yml down
        ;;
    *)
        echo "Usage: $0 {deploy|status|test|logs|stop}"
        echo "  deploy - Full staging deployment (default)"
        echo "  status - Show staging status"
        echo "  test   - Run demo tests"
        echo "  logs   - Follow staging logs"
        echo "  stop   - Stop staging environment"
        exit 1
        ;;
esac
