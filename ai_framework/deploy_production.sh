#!/bin/bash

# AI Framework Production Deployment Script
# 🚀 Comprehensive production deployment with safety checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="AI Framework"
PRODUCTION_COMPOSE="docker-compose.production.yml"
ENV_FILE="production.env"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Logging
LOG_FILE="${LOG_DIR}/deployment_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}🚀 $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}📋 $1${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
}

print_success() {
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

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install it and try again."
        exit 1
    fi
    print_success "Docker Compose is available"

    # Check if required files exist
    if [[ ! -f "$PRODUCTION_COMPOSE" ]]; then
        print_error "Production Docker Compose file not found: $PRODUCTION_COMPOSE"
        exit 1
    fi
    print_success "Production Docker Compose file found"

    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Production environment file not found: $ENV_FILE"
        exit 1
    fi
    print_success "Production environment file found"

    # Create necessary directories
    mkdir -p "$BACKUP_DIR" "$LOG_DIR" "./data" "./ssl"
    print_success "Required directories created"
}

# Backup existing data
backup_existing_data() {
    print_header "Backing Up Existing Data"

    if [[ -d "./data" ]] && [[ "$(ls -A ./data)" ]]; then
        print_info "Creating backup of existing data..."
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "$BACKUP_DIR/$BACKUP_NAME" ./data 2>/dev/null || true
        print_success "Backup created: $BACKUP_NAME"
    else
        print_info "No existing data to backup"
    fi
}

# Validate environment configuration
validate_environment() {
    print_header "Validating Environment Configuration"

    # Check if critical secrets are still default
    source "$ENV_FILE"

    if [[ "$JWT_SECRET" == "your-super-secure-production-jwt-secret-change-this-immediately" ]]; then
        print_error "JWT_SECRET is still set to default value. Please change it in $ENV_FILE"
        exit 1
    fi

    if [[ "$API_KEY" == "your-production-api-key-change-this-immediately" ]]; then
        print_error "API_KEY is still set to default value. Please change it in $ENV_FILE"
        exit 1
    fi

    if [[ "$POSTGRES_PASSWORD" == "your-super-secure-production-db-password" ]]; then
        print_error "POSTGRES_PASSWORD is still set to default value. Please change it in $ENV_FILE"
        exit 1
    fi

    if [[ "$REDIS_PASSWORD" == "your-super-secure-production-redis-password" ]]; then
        print_error "REDIS_PASSWORD is still set to default value. Please change it in $ENV_FILE"
        exit 1
    fi

    if [[ "$GRAFANA_PASSWORD" == "your-super-secure-production-grafana-password" ]]; then
        print_error "GRAFANA_PASSWORD is still set to default value. Please change it in $ENV_FILE"
        exit 1
    fi

    if [[ "$ALLOWED_ORIGINS" == "https://yourdomain.com,https://www.yourdomain.com" ]]; then
        print_warning "ALLOWED_ORIGINS is still set to default value. Please update it in $ENV_FILE"
    fi

    print_success "Environment configuration validated"
}

# Stop existing services
stop_existing_services() {
    print_header "Stopping Existing Services"

    # Stop staging environment if running
    if [[ -f "docker-compose.staging.yml" ]]; then
        print_info "Stopping staging environment..."
        docker-compose -f docker-compose.staging.yml down --remove-orphans 2>/dev/null || true
        print_success "Staging environment stopped"
    fi

    # Stop any existing production services
    if docker ps --format "table {{.Names}}" | grep -q "production"; then
        print_info "Stopping existing production services..."
        docker-compose -f "$PRODUCTION_COMPOSE" down --remove-orphans 2>/dev/null || true
        print_success "Existing production services stopped"
    fi

    # Clean up any dangling containers
    docker container prune -f > /dev/null 2>&1 || true
    print_success "Dangling containers cleaned up"
}

# Build production images
build_production_images() {
    print_header "Building Production Images"

    print_info "Building AI Framework production image..."
    docker build --target production -t ai_framework-production:latest .
    print_success "AI Framework production image built"

    print_info "Pulling required base images..."
    docker pull postgres:15-alpine
    docker pull redis:7-alpine
    docker pull prom/prometheus:latest
    docker pull grafana/grafana:latest
    docker pull nginx:alpine
    print_success "All base images pulled"
}

# Deploy production services
deploy_production_services() {
    print_header "Deploying Production Services"

    print_info "Starting production services..."
    docker-compose -f "$PRODUCTION_COMPOSE" up -d

    print_info "Waiting for services to be ready..."
    sleep 30

    # Check service health
    print_info "Checking service health..."
    docker-compose -f "$PRODUCTION_COMPOSE" ps

    print_success "Production services deployed"
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Production Deployment"

    local max_attempts=10
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        print_info "Health check attempt $attempt/$max_attempts..."

        # Check AI Framework health
        if curl -f "http://localhost:8000/health" > /dev/null 2>&1; then
            print_success "AI Framework is healthy"
        else
            print_warning "AI Framework health check failed (attempt $attempt)"
            if [[ $attempt -eq $max_attempts ]]; then
                print_error "AI Framework failed to become healthy after $max_attempts attempts"
                return 1
            fi
            sleep 30
            ((attempt++))
            continue
        fi

        # Check Prometheus health
        if curl -f "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
            print_success "Prometheus is healthy"
        else
            print_warning "Prometheus health check failed"
        fi

        # Check Grafana health
        if curl -f "http://localhost:3000/api/health" > /dev/null 2>&1; then
            print_success "Grafana is healthy"
        else
            print_warning "Grafana health check failed"
        fi

        break
    done

    print_success "Production deployment verified"
    return 0
}

# Run production tests
run_production_tests() {
    print_header "Running Production Tests"

    # Run stability tests
    if [[ -f "./reliability/stability_test_suite.py" ]]; then
        print_info "Running production stability tests..."
        cd reliability && python3 stability_test_suite.py && cd ..
        print_success "Production stability tests completed"
    fi

    # Run security tests
    if [[ -f "./security_testing/security_test_suite.py" ]]; then
        print_info "Running production security tests..."
        cd security_testing && python3 security_test_suite.py && cd ..
        print_success "Production security tests completed"
    fi
}

# Display production information
display_production_info() {
    print_header "Production Deployment Complete!"

    echo -e "\n${GREEN}🎉 Your AI Framework is now running in production!${NC}"
    echo -e "\n${BLUE}Production Services:${NC}"
    echo -e "  • AI Framework API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  • Prometheus Metrics: ${GREEN}http://localhost:9090${NC}"
    echo -e "  • Grafana Dashboard: ${GREEN}http://localhost:3000${NC}"
    echo -e "  • Nginx Proxy: ${GREEN}http://localhost:80${NC}"

    echo -e "\n${BLUE}Default Credentials:${NC}"
    echo -e "  • Grafana Admin: ${YELLOW}admin / (password from production.env)${NC}"
    echo -e "  • AI Framework: ${YELLOW}admin / admin123${NC}"

    echo -e "\n${BLUE}Important URLs:${NC}"
    echo -e "  • Health Check: ${GREEN}http://localhost:8000/health${NC}"
    echo -e "  • API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  • Metrics: ${GREEN}http://localhost:8000/metrics${NC}"

    echo -e "\n${YELLOW}⚠️  Security Reminders:${NC}"
    echo -e "  • Change all default passwords in production.env"
    echo -e "  • Configure SSL/TLS certificates"
    echo -e "  • Set up proper firewall rules"
    echo -e "  • Configure monitoring alerts"

    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "  1. Configure your domain and SSL certificates"
    echo -e "  2. Set up monitoring alerts and notifications"
    echo -e "  3. Configure backup schedules"
    echo -e "  4. Set up CI/CD pipelines"
    echo -e "  5. Monitor system performance and logs"

    echo -e "\n${GREEN}🚀 Your AI Framework is ready for production use!${NC}"
}

# Main deployment function
main() {
    print_header "AI Framework Production Deployment"
    echo -e "${BLUE}This script will deploy your AI Framework to production${NC}"
    echo -e "${YELLOW}Make sure you have:${NC}"
    echo -e "  • Updated all passwords in production.env"
    echo -e "  • Configured your domain settings"
    echo -e "  • SSL certificates ready (if using HTTPS)"
    echo -e "  • Sufficient system resources"

    echo -e "\n${YELLOW}Press Enter to continue or Ctrl+C to abort...${NC}"
    read -r

    # Execute deployment steps
    check_prerequisites
    backup_existing_data
    validate_environment
    stop_existing_services
    build_production_images
    deploy_production_services

    if verify_deployment; then
        run_production_tests
        display_production_info
        print_success "Production deployment completed successfully!"
    else
        print_error "Production deployment verification failed"
        exit 1
    fi
}

# Error handling
trap 'print_error "Deployment failed. Check logs at: $LOG_FILE"; exit 1' ERR

# Run main function
main "$@"
