#!/bin/bash


set -e

HEALTH_URL="${HEALTH_URL:-http://localhost/health}"
API_HEALTH_URL="${API_HEALTH_URL:-http://localhost/api/v1/health}"
TIMEOUT="${TIMEOUT:-10}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_main_health() {
    log "Checking main health endpoint..."
    
    if curl -f --max-time "$TIMEOUT" "$HEALTH_URL" >/dev/null 2>&1; then
        log "✅ Main health check passed"
        return 0
    else
        error "❌ Main health check failed"
        return 1
    fi
}

check_api_health() {
    log "Checking API health endpoint..."
    
    if curl -f --max-time "$TIMEOUT" "$API_HEALTH_URL" >/dev/null 2>&1; then
        log "✅ API health check passed"
        return 0
    else
        error "❌ API health check failed"
        return 1
    fi
}

check_database() {
    log "Checking database connectivity..."
    
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
        log "✅ Database check passed"
        return 0
    else
        error "❌ Database check failed"
        return 1
    fi
}

check_redis() {
    log "Checking Redis connectivity..."
    
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli --pass "$REDIS_PASSWORD" ping >/dev/null 2>&1; then
        log "✅ Redis check passed"
        return 0
    else
        error "❌ Redis check failed"
        return 1
    fi
}

check_celery_workers() {
    log "Checking Celery workers..."
    
    worker_count=$(docker-compose -f docker-compose.prod.yml ps celery_worker | grep -c "Up" || echo "0")
    
    if [ "$worker_count" -gt 0 ]; then
        log "✅ Celery workers check passed ($worker_count workers running)"
        return 0
    else
        error "❌ Celery workers check failed (no workers running)"
        return 1
    fi
}

check_disk_space() {
    log "Checking disk space..."
    
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -lt 90 ]; then
        log "✅ Disk space check passed (${disk_usage}% used)"
        return 0
    else
        warning "⚠️ Disk space warning (${disk_usage}% used)"
        return 1
    fi
}

check_memory_usage() {
    log "Checking memory usage..."
    
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$memory_usage" -lt 90 ]; then
        log "✅ Memory usage check passed (${memory_usage}% used)"
        return 0
    else
        warning "⚠️ Memory usage warning (${memory_usage}% used)"
        return 1
    fi
}

send_slack_notification() {
    local message="$1"
    local color="$2"
    
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\", \"color\":\"$color\"}" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1
    fi
}

send_email_notification() {
    local subject="$1"
    local message="$2"
    
    if [ -n "$EMAIL_RECIPIENT" ] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "$subject" "$EMAIL_RECIPIENT"
    fi
}

run_health_checks() {
    local failed_checks=()
    local warning_checks=()
    
    check_main_health || failed_checks+=("Main Health")
    check_api_health || failed_checks+=("API Health")
    check_database || failed_checks+=("Database")
    check_redis || failed_checks+=("Redis")
    check_celery_workers || failed_checks+=("Celery Workers")
    check_disk_space || warning_checks+=("Disk Space")
    check_memory_usage || warning_checks+=("Memory Usage")
    
    if [ ${#failed_checks[@]} -eq 0 ] && [ ${#warning_checks[@]} -eq 0 ]; then
        log "🎉 All health checks passed!"
        send_slack_notification "✅ YouTube Analyzer: All health checks passed" "good"
        return 0
    elif [ ${#failed_checks[@]} -eq 0 ]; then
        warning "⚠️ Health checks passed with warnings: ${warning_checks[*]}"
        send_slack_notification "⚠️ YouTube Analyzer: Health checks passed with warnings: ${warning_checks[*]}" "warning"
        return 0
    else
        error "❌ Health checks failed: ${failed_checks[*]}"
        
        local message="🚨 YouTube Analyzer health check failed!\nFailed checks: ${failed_checks[*]}"
        if [ ${#warning_checks[@]} -gt 0 ]; then
            message="$message\nWarnings: ${warning_checks[*]}"
        fi
        
        send_slack_notification "$message" "danger"
        send_email_notification "YouTube Analyzer Health Check Failed" "$message"
        
        return 1
    fi
}

restart_failed_services() {
    log "Attempting to restart failed services..."
    
    docker-compose -f docker-compose.prod.yml restart
    
    sleep 30
    
    if run_health_checks; then
        log "✅ Services restarted successfully"
        send_slack_notification "✅ YouTube Analyzer: Services restarted successfully after failure" "good"
        return 0
    else
        error "❌ Services still failing after restart"
        send_slack_notification "🚨 YouTube Analyzer: Services still failing after restart - manual intervention required" "danger"
        return 1
    fi
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -q, --quiet         Quiet mode (only errors)"
    echo "  -r, --restart       Restart services if health checks fail"
    echo "  --url URL           Override health check URL"
    echo "  --timeout SECONDS   Override timeout (default: 10)"
}

QUIET=false
AUTO_RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -r|--restart)
            AUTO_RESTART=true
            shift
            ;;
        --url)
            HEALTH_URL="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

if [ "$QUIET" = true ]; then
    exec 1>/dev/null
fi

main() {
    log "Starting YouTube Analyzer health check..."
    
    if [ -f .env.prod ]; then
        source .env.prod
    fi
    
    if run_health_checks; then
        exit 0
    else
        if [ "$AUTO_RESTART" = true ]; then
            restart_failed_services
            exit $?
        else
            exit 1
        fi
    fi
}

main "$@"
