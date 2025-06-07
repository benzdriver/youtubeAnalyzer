#!/bin/bash


set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKUP_DIR="/opt/youtube-analyzer/backups"
LOG_FILE="/opt/youtube-analyzer/deploy.log"
MAX_BACKUPS=5

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

validate_environment() {
    log "Validating deployment environment..."
    
    if [ ! -f .env.prod ]; then
        error ".env.prod file not found. Please create it from .env.prod.example"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "docker-compose is not installed"
        exit 1
    fi
    
    source .env.prod
    required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY" "OPENAI_API_KEY" "YOUTUBE_API_KEY")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Required environment variable $var is not set in .env.prod"
            exit 1
        fi
    done
    
    success "Environment validation passed"
}

create_backup() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    docker-compose -f docker-compose.prod.yml down || true
    
    if docker ps -a --format "table {{.Names}}" | grep -q postgres; then
        log "Backing up database..."
        docker-compose -f docker-compose.prod.yml up -d postgres
        sleep 10
        
        docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
            -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_PATH.sql" || {
            warning "Database backup failed, continuing with deployment"
        }
        
        docker-compose -f docker-compose.prod.yml down
    fi
    
    log "Backing up Docker images..."
    docker save youtubeanalyzer_backend:latest > "$BACKUP_PATH_backend.tar" 2>/dev/null || true
    docker save youtubeanalyzer_frontend:latest > "$BACKUP_PATH_frontend.tar" 2>/dev/null || true
    
    cleanup_old_backups
    
    success "Backup created: $BACKUP_PATH"
}

cleanup_old_backups() {
    log "Cleaning up old backups (keeping last $MAX_BACKUPS)..."
    
    cd "$BACKUP_DIR"
    ls -t backup_*.sql 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f || true
    ls -t backup_*.tar 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f || true
}

update_code() {
    log "Pulling latest code from repository..."
    
    git stash push -m "Auto-stash before deployment $(date)" || true
    
    git fetch origin
    git reset --hard origin/main
    
    success "Code updated successfully"
}

deploy_services() {
    log "Building and starting services..."
    
    log "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    log "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    success "Services started successfully"
}

run_migrations() {
    log "Running database migrations..."
    
    log "Waiting for database to be ready..."
    sleep 30
    
    docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || {
        error "Database migration failed"
        return 1
    }
    
    success "Database migrations completed"
}

health_check() {
    log "Performing health checks..."
    
    local max_attempts=20
    local attempt=1
    local health_url="http://localhost/health"
    
    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts"
        
        if curl -f --max-time 10 "$health_url" >/dev/null 2>&1; then
            success "Health check passed"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "Health check failed after $max_attempts attempts"
            return 1
        fi
        
        log "Health check failed, retrying in 15 seconds..."
        sleep 15
        attempt=$((attempt + 1))
    done
}

rollback() {
    error "Deployment failed, initiating rollback..."
    
    docker-compose -f docker-compose.prod.yml down || true
    
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_BASE=$(basename "$LATEST_BACKUP" .sql)
        
        if [ -f "$BACKUP_DIR/${BACKUP_BASE}_backend.tar" ]; then
            log "Restoring backend image..."
            docker load < "$BACKUP_DIR/${BACKUP_BASE}_backend.tar"
        fi
        
        if [ -f "$BACKUP_DIR/${BACKUP_BASE}_frontend.tar" ]; then
            log "Restoring frontend image..."
            docker load < "$BACKUP_DIR/${BACKUP_BASE}_frontend.tar"
        fi
        
        docker-compose -f docker-compose.prod.yml up -d
        sleep 30
        
        log "Restoring database..."
        docker-compose -f docker-compose.prod.yml exec -T postgres psql \
            -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$LATEST_BACKUP"
        
        success "Rollback completed"
    else
        error "No backup found for rollback"
    fi
}

cleanup() {
    log "Cleaning up Docker resources..."
    
    docker image prune -f
    
    
    docker network prune -f
    
    success "Cleanup completed"
}

main() {
    log "🚀 Starting YouTube Analyzer deployment..."
    
    trap 'rollback; exit 1' ERR
    
    check_permissions
    validate_environment
    create_backup
    update_code
    deploy_services
    run_migrations
    
    if health_check; then
        cleanup
        success "🎉 Deployment completed successfully!"
        
        log "Service status:"
        docker-compose -f docker-compose.prod.yml ps
        
        log "Resource usage:"
        docker stats --no-stream
        
    else
        error "Deployment failed health check"
        exit 1
    fi
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --no-backup    Skip backup creation"
    echo "  --rollback     Rollback to previous deployment"
    echo "  --status       Show current deployment status"
    echo "  --logs         Show service logs"
}

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    --no-backup)
        log "Skipping backup as requested"
        create_backup() { log "Backup skipped"; }
        main
        ;;
    --rollback)
        rollback
        exit 0
        ;;
    --status)
        docker-compose -f docker-compose.prod.yml ps
        exit 0
        ;;
    --logs)
        docker-compose -f docker-compose.prod.yml logs -f
        exit 0
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
esac
