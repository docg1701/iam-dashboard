#!/bin/bash

# IAM Dashboard - Production Deployment Script
# SAFE deployment script with proper error handling and health checks
#
# Environment Variables:
# - SKIP_ALEMBIC_CHECK=true    Skip Alembic migration validation (useful for initial setup)
# - BACKUP_VOLUMES=true        Create backup before deployment
# - DEPLOYMENT_TIMEOUT=600     Max deployment time in seconds (60-1800)
# - HEALTH_CHECK_RETRIES=30    Health check attempts (5-100)
# - ALLOW_ROOT_DEPLOYMENT=true Allow running as root user

# Don't exit on error immediately - we need controlled error handling
# set -e  # REMOVED for safe deployment with rollback capability

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Deployment configuration with validation
validate_numeric_param() {
    local param_name="$1"
    local param_value="$2"
    local min_value="$3"
    local max_value="$4"
    
    if ! [[ "$param_value" =~ ^[0-9]+$ ]]; then
        log "❌ Invalid $param_name: must be numeric"
        exit 1
    fi
    
    if [ "$param_value" -lt "$min_value" ] || [ "$param_value" -gt "$max_value" ]; then
        log "❌ Invalid $param_name: must be between $min_value and $max_value"
        exit 1
    fi
}

DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-300}"
validate_numeric_param "DEPLOYMENT_TIMEOUT" "$DEPLOYMENT_TIMEOUT" 60 1800

HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-30}"
validate_numeric_param "HEALTH_CHECK_RETRIES" "$HEALTH_CHECK_RETRIES" 5 100

HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"
validate_numeric_param "HEALTH_CHECK_INTERVAL" "$HEALTH_CHECK_INTERVAL" 1 60

# Validate boolean parameters
BACKUP_VOLUMES="${BACKUP_VOLUMES:-false}"
if [[ "$BACKUP_VOLUMES" != "true" && "$BACKUP_VOLUMES" != "false" ]]; then
    log "❌ Invalid BACKUP_VOLUMES: must be 'true' or 'false'"
    exit 1
fi

SKIP_ALEMBIC_CHECK="${SKIP_ALEMBIC_CHECK:-false}"
if [[ "$SKIP_ALEMBIC_CHECK" != "true" && "$SKIP_ALEMBIC_CHECK" != "false" ]]; then
    log "❌ Invalid SKIP_ALEMBIC_CHECK: must be 'true' or 'false'"
    exit 1
fi

echo "🚀 IAM Dashboard Production Deployment"
echo "======================================"
echo "⚠️  PRODUCTION DEPLOYMENT - Proceed with caution!"
echo ""

# Function to log with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a service is healthy
check_service_health() {
    local service_name="$1"
    local health_url="$2"
    local max_retries="$3"
    local interval="$4"
    
    log "🏥 Checking $service_name health..."
    
    for i in $(seq 1 "$max_retries"); do
        if curl -f --max-time 10 --silent "$health_url" >/dev/null 2>&1; then
            log "✅ $service_name is healthy (attempt $i/$max_retries)"
            return 0
        else
            log "⏳ $service_name not ready yet (attempt $i/$max_retries)"
            if [ "$i" -lt "$max_retries" ]; then
                sleep "$interval"
            fi
        fi
    done
    
    log "❌ $service_name health check failed after $max_retries attempts"
    return 1
}

# Function to check if docker compose is working and validate privileges
check_docker_compose() {
    log "🐳 Checking Docker Compose availability..."
    
    if ! command -v docker >/dev/null 2>&1; then
        log "❌ Docker not found - required for deployment"
        return 1
    fi
    
    if ! docker compose version >/dev/null 2>&1; then
        log "❌ Docker Compose not available"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log "❌ Docker daemon not running"
        return 1
    fi
    
    # Check if user has Docker privileges (critical security check)
    if ! docker ps >/dev/null 2>&1; then
        log "❌ Current user does not have Docker privileges"
        log "💡 Try: sudo usermod -aG docker \$USER (then logout/login)"
        return 1
    fi
    
    # Check if running as root (security warning)
    if [ "$EUID" -eq 0 ]; then
        log "⚠️ WARNING: Running as root - consider using non-root user with Docker group"
        if [[ "${ALLOW_ROOT_DEPLOYMENT:-false}" != "true" ]]; then
            log "❌ Root deployment blocked. Set ALLOW_ROOT_DEPLOYMENT=true to override"
            return 1
        fi
    fi
    
    log "✅ Docker environment ready"
    return 0
}

# Function to validate required files
validate_deployment_files() {
    log "📋 Validating deployment requirements..."
    
    local missing_files=()
    
    if [ ! -f "docker-compose.yml" ]; then
        missing_files+=("docker-compose.yml")
    fi
    
    # Alembic validation - can be skipped for initial setup
    if [ "$SKIP_ALEMBIC_CHECK" = "false" ]; then
        if [ ! -d "apps/api/alembic/versions" ] || [ -z "$(ls -A apps/api/alembic/versions/*.py 2>/dev/null)" ]; then
            missing_files+=("Alembic migrations")
        fi
    else
        log "⚠️ Skipping Alembic migration validation (SKIP_ALEMBIC_CHECK=true)"
    fi
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log "❌ Missing required files/directories:"
        for file in "${missing_files[@]}"; do
            log "   - $file"
        done
        return 1
    fi
    
    log "✅ All deployment files present"
    return 0
}

# Function to backup current state (if requested)
backup_current_state() {
    if [ "$BACKUP_VOLUMES" = "true" ]; then
        log "💾 Creating backup of current state..."
        
        # Sanitize timestamp to prevent injection
        local backup_timestamp=$(date +"%Y%m%d_%H%M%S" | tr -cd '0-9_')
        
        # Validate and create backup directory safely
        local backup_dir="backups"
        if ! mkdir -p "$backup_dir" 2>/dev/null; then
            log "❌ Cannot create backup directory"
            return 1
        fi
        
        # Get absolute path to prevent path traversal
        local safe_backup_path="$(cd "$backup_dir" && pwd)"
        local safe_working_path="$(pwd)"
        
        # Backup volumes (if they exist)
        if docker volume ls | grep -q "iam-dashboard_postgres_data"; then
            log "📦 Backing up postgres data..."
            
            # Use array for safe command construction
            local docker_cmd=(
                docker run --rm
                -v iam-dashboard_postgres_data:/data
                -v "$safe_backup_path:/backup"
                alpine tar czf 
                "/backup/postgres_backup_${backup_timestamp}.tar.gz"
                /data
            )
            
            if "${docker_cmd[@]}"; then
                log "✅ Postgres backup created: postgres_backup_${backup_timestamp}.tar.gz"
            else
                log "⚠️ Postgres backup failed - continuing anyway"
            fi
        fi
        
        log "✅ Backup completed: $safe_backup_path/"
    else
        log "ℹ️ Skipping backup (BACKUP_VOLUMES=false)"
    fi
}

# Function for safe service shutdown
safe_shutdown() {
    log "🛑 Safely stopping existing services..."
    
    # Give services time to shut down gracefully
    if docker compose ps --quiet | grep -q .; then
        docker compose stop --timeout 30
        
        # If services don't stop gracefully, force them
        if docker compose ps --quiet | grep -q .; then
            log "⚠️ Some services didn't stop gracefully, forcing shutdown..."
            docker compose down --timeout 10
        fi
    else
        log "ℹ️ No services were running"
    fi
}

# Function to rollback on failure
rollback_deployment() {
    log "🔄 Rolling back deployment..."
    
    # Stop failed services
    docker compose down --timeout 30 2>/dev/null || true
    
    # If backup was created, suggest restore
    if [ "$BACKUP_VOLUMES" = "true" ] && [ -d "backups" ]; then
        log "💡 To restore from backup:"
        log "   docker volume rm iam-dashboard_postgres_data"
        log "   docker run --rm -v iam-dashboard_postgres_data:/data -v \$PWD/backups:/backup alpine tar xzf /backup/postgres_backup_*.tar.gz -C /"
    fi
    
    log "❌ Deployment failed and rolled back"
    exit 1
}

# Navigate to project root safely
cd "$PROJECT_ROOT" || {
    log "❌ Cannot access project root: $PROJECT_ROOT"
    exit 1
}

# Main deployment workflow with error handling
main_deployment() {
    # Pre-deployment checks
    check_docker_compose || exit 1
    validate_deployment_files || exit 1
    backup_current_state
    
    # Safe shutdown of existing services
    safe_shutdown
    
    # Start database services first
    log "🔄 Starting database services..."
    if ! docker compose up -d postgres redis; then
        log "❌ Failed to start database services"
        rollback_deployment
    fi
    
    # Wait for database to be ready with proper health checking
    log "⏳ Waiting for database to initialize..."
    
    # Check postgres health with docker health check if available
    local db_ready=false
    for i in $(seq 1 30); do
        if docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            log "✅ PostgreSQL is ready (attempt $i/30)"
            db_ready=true
            break
        else
            log "⏳ PostgreSQL not ready yet (attempt $i/30)"
            sleep 5
        fi
    done
    
    if [ "$db_ready" = false ]; then
        log "❌ PostgreSQL failed to become ready"
        log "📋 PostgreSQL logs:"
        docker compose logs postgres --tail=20
        rollback_deployment
    fi
    
    # Start backend with proper health checking
    log "🚀 Starting backend service..."
    if ! docker compose up -d api; then
        log "❌ Failed to start backend service"
        rollback_deployment
    fi
    
    # Health check api service with retries
    if ! check_service_health "Backend" "http://localhost:8000/health" "$HEALTH_CHECK_RETRIES" "$HEALTH_CHECK_INTERVAL"; then
        log "📋 Backend logs:"
        docker compose logs api --tail=30
        rollback_deployment
    fi
    
    # Start frontend if configured
    if docker compose config --services | grep -q "frontend"; then
        log "🌐 Starting frontend service..."
        if ! docker compose up -d frontend; then
            log "⚠️ Failed to start frontend service - continuing with backend only"
        else
            # Optional frontend health check
            if ! check_service_health "Frontend" "http://localhost:3000" 10 5; then
                log "⚠️ Frontend health check failed - may still be starting"
            fi
        fi
    else
        log "ℹ️ No frontend service configured"
    fi
    
    # Final verification
    log "🔍 Final deployment verification..."
    if ! docker compose ps | grep -q "Up"; then
        log "❌ No services are running after deployment"
        rollback_deployment
    fi
    
    # Success!
    log "✅ Deployment completed successfully!"
    
    echo ""
    echo "✅ Deployment Complete!"
    echo "========================"
    echo "🕐 Completed at: $(date)"
    echo ""
    echo "🌐 Service URLs:"
    echo "   Backend API: http://localhost:8000"
    echo "   Health Check: http://localhost:8000/health" 
    echo "   API Documentation: http://localhost:8000/docs"
    
    if docker compose config --services | grep -q "frontend"; then
        echo "   Frontend: http://localhost:3000"
    fi
    
    echo ""
    echo "📊 Service Status:"
    docker compose ps
    
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker compose logs [service]"
    echo "   Stop services: docker compose down"
    echo "   Restart service: docker compose restart [service]"
    echo ""
    echo "💡 Initial Setup Tips:"
    echo "   For first-time setup without Alembic: SKIP_ALEMBIC_CHECK=true ./scripts/deploy-production.sh"
    echo ""
    
    # Environment-specific instructions
    if [ "${BACKUP_VOLUMES}" = "true" ]; then
        echo "💾 Backup created in: ./backups/"
    fi
    
    log "🎉 Production deployment successful!"
}

# Trap to handle interruption
trap 'log "🛑 Deployment interrupted"; rollback_deployment' INT TERM

# Run the main deployment
main_deployment

# Exit with success
exit 0