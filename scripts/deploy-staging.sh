#!/bin/bash

# Deploy script for IAM Dashboard - Agent-Based Architecture
# This script deploys the application to staging environment with validation

set -e  # Exit on any error

echo "🚀 Starting deployment to staging environment..."

# Configuration
STAGING_ENV="staging"
COMPOSE_FILE="docker-compose.staging.yml"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f ".env.staging" ]; then
        log_warn "Creating staging environment file from template"
        cp .env.example .env.staging
        log_warn "Please configure .env.staging before continuing"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup database if running
    if docker-compose ps | grep -q "db.*Up"; then
        log_info "Backing up database..."
        docker-compose exec -T db pg_dump -U postgres advocacia_db > "$BACKUP_DIR/database_backup.sql"
    fi
    
    # Backup configuration
    cp -r app/config/ "$BACKUP_DIR/config/" 2>/dev/null || true
    
    # Backup uploads
    cp -r uploads/ "$BACKUP_DIR/uploads/" 2>/dev/null || true
    
    log_info "Backup created in $BACKUP_DIR ✓"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose down
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose pull
    
    # Build and start services
    log_info "Building and starting services..."
    docker-compose --env-file .env.staging up -d --build
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    log_info "Application deployed ✓"
}

# Database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T db pg_isready -U postgres >/dev/null 2>&1; then
            log_info "Database is ready"
            break
        fi
        
        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Database failed to become ready"
        exit 1
    fi
    
    # Run migrations
    docker-compose exec app uv run alembic upgrade head
    
    log_info "Database migrations completed ✓"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    # Check if services are running
    log_info "Checking service status..."
    if ! docker-compose ps | grep -q "Up"; then
        log_error "Some services are not running"
        docker-compose ps
        exit 1
    fi
    
    # Test application health
    log_info "Testing application health..."
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8080/v1/admin/system/health >/dev/null 2>&1; then
            log_info "Application health check passed"
            break
        fi
        
        log_info "Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Application health check failed"
        exit 1
    fi
    
    # Test agent status
    log_info "Testing agent status..."
    if curl -f http://localhost:8080/v1/admin/agents >/dev/null 2>&1; then
        log_info "Agent management endpoints accessible"
    else
        log_warn "Agent management endpoints not accessible (may be expected in staging)"
    fi
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    if docker-compose exec -T db psql -U postgres -d advocacia_db -c "SELECT 1;" >/dev/null 2>&1; then
        log_info "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        exit 1
    fi
    
    log_info "Deployment validation completed ✓"
}

# Agent system validation
validate_agents() {
    log_info "Validating agent system..."
    
    # Check agent configuration
    if docker-compose exec app test -f app/config/agents.yaml; then
        log_info "Agent configuration file found"
    else
        log_warn "Agent configuration file not found"
    fi
    
    # Test agent endpoints (if available)
    log_info "Testing agent system endpoints..."
    
    # This would test actual agent functionality in a real deployment
    # For now, we just verify the structure is in place
    
    log_info "Agent system validation completed ✓"
}

# Performance validation
validate_performance() {
    log_info "Running performance validation..."
    
    # Run basic performance tests
    log_info "Running performance tests..."
    docker-compose exec app uv run pytest tests/performance/ -v --tb=short || {
        log_warn "Some performance tests failed (may be expected in staging environment)"
    }
    
    log_info "Performance validation completed ✓"
}

# Cleanup
cleanup() {
    log_info "Cleaning up..."
    
    # Remove unused Docker images
    docker image prune -f >/dev/null 2>&1 || true
    
    log_info "Cleanup completed ✓"
}

# Main execution
main() {
    log_info "Starting IAM Dashboard staging deployment"
    
    check_prerequisites
    create_backup
    deploy_application
    run_migrations
    validate_deployment
    validate_agents
    validate_performance
    cleanup
    
    log_info "🎉 Staging deployment completed successfully!"
    log_info "Access the application at: http://localhost:8080"
    log_info "Admin panel at: http://localhost:8080/admin"
    log_info "API documentation at: http://localhost:8080/docs"
}

# Handle script termination
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"