#!/bin/bash

# LMA Platform Deployment Script
# This script automates the deployment of the Lead Management Automation platform

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-development}"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
LMA Platform Deployment Script

Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    development    Deploy for development (default)
    staging        Deploy for staging environment
    production     Deploy for production environment

OPTIONS:
    --build        Force rebuild of Docker images
    --pull         Pull latest images before deployment
    --backup       Create database backup before deployment
    --rollback     Rollback to previous deployment
    --health-check Perform health check after deployment
    --help         Show this help message

Examples:
    $0 development
    $0 production --build --backup --health-check
    $0 staging --pull

EOF
}

# Parse command line arguments
BUILD_FLAG=""
PULL_FLAG=""
BACKUP_FLAG=""
ROLLBACK_FLAG=""
HEALTH_CHECK_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --pull)
            PULL_FLAG="true"
            shift
            ;;
        --backup)
            BACKUP_FLAG="true"
            shift
            ;;
        --rollback)
            ROLLBACK_FLAG="true"
            shift
            ;;
        --health-check)
            HEALTH_CHECK_FLAG="true"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        development|staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set compose file based on environment
case $ENVIRONMENT in
    production)
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.staging"
        ;;
    development)
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        exit 1
        ;;
esac

log_info "Deploying LMA Platform for $ENVIRONMENT environment"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    log_error "Docker compose file $COMPOSE_FILE not found"
    exit 1
fi

# Create environment file if it doesn't exist
if [[ ! -f ".env" && "$ENVIRONMENT" == "development" ]]; then
    log_warning "Environment file not found. Creating from example..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        log_info "Created .env from .env.example"
    else
        log_error "No .env.example file found. Please create .env manually."
        exit 1
    fi
fi

# Backup database if requested
if [[ "$BACKUP_FLAG" == "true" ]]; then
    log_info "Creating database backup..."
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Create PostgreSQL backup
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U lma_user lma_db > "$BACKUP_DIR/lma_db_backup.sql"
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U lma_user n8n_db > "$BACKUP_DIR/n8n_db_backup.sql"
    
    log_success "Database backup created in $BACKUP_DIR"
fi

# Rollback if requested
if [[ "$ROLLBACK_FLAG" == "true" ]]; then
    log_info "Rolling back to previous deployment..."
    
    # Stop current containers
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from latest backup
    LATEST_BACKUP=$(ls -1t backups/ | head -n 1)
    if [[ -n "$LATEST_BACKUP" ]]; then
        log_info "Restoring from backup: $LATEST_BACKUP"
        
        # Start database containers
        docker-compose -f "$COMPOSE_FILE" up -d postgres redis
        sleep 10
        
        # Restore databases
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U lma_user -d lma_db < "backups/$LATEST_BACKUP/lma_db_backup.sql"
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U lma_user -d n8n_db < "backups/$LATEST_BACKUP/n8n_db_backup.sql"
        
        log_success "Rollback completed"
    else
        log_error "No backup found for rollback"
        exit 1
    fi
    exit 0
fi

# Pull latest images if requested
if [[ "$PULL_FLAG" == "true" ]]; then
    log_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
fi

# Stop existing containers gracefully
log_info "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans

# Build and start containers
log_info "Starting LMA Platform containers..."
if [[ -n "$BUILD_FLAG" ]]; then
    log_info "Building images..."
    docker-compose -f "$COMPOSE_FILE" up -d $BUILD_FLAG
else
    docker-compose -f "$COMPOSE_FILE" up -d
fi

# Wait for services to be ready
log_info "Waiting for services to start..."
sleep 30

# Health check if requested
if [[ "$HEALTH_CHECK_FLAG" == "true" ]]; then
    log_info "Performing health checks..."
    
    # Check PostgreSQL
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U lma_user -d lma_db >/dev/null 2>&1; then
        log_success "PostgreSQL is healthy"
    else
        log_error "PostgreSQL health check failed"
        exit 1
    fi
    
    # Check Redis
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_error "Redis health check failed"
        exit 1
    fi
    
    # Check backend API
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend API is healthy"
    else
        log_error "Backend API health check failed"
        exit 1
    fi
    
    # Check frontend
    if curl -I http://localhost:5173 >/dev/null 2>&1; then
        log_success "Frontend is accessible"
    else
        log_warning "Frontend health check failed (may still be starting)"
    fi
    
    # Check n8n
    if curl -f http://localhost:5678 >/dev/null 2>&1; then
        log_success "n8n workflow engine is accessible"
    else
        log_warning "n8n health check failed (may still be starting)"
    fi
fi

# Show container status
log_info "Container status:"
docker-compose -f "$COMPOSE_FILE" ps

# Show access URLs
echo ""
log_success "LMA Platform deployed successfully!"
echo ""
echo "Access URLs:"
echo "  Frontend:    http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  n8n:         http://localhost:5678"
echo "  API Docs:    http://localhost:8000/docs"
echo ""

# Show useful commands
echo "Useful commands:"
echo "  View logs:     docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop all:      docker-compose -f $COMPOSE_FILE down"
echo "  Restart:       docker-compose -f $COMPOSE_FILE restart"
echo "  Shell access:  docker-compose -f $COMPOSE_FILE exec [service] bash"
echo ""

log_success "Deployment completed!" 