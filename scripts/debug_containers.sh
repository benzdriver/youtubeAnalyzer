#!/bin/bash


set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        print_error "Neither docker-compose nor 'docker compose' is available"
        exit 1
    fi
    print_success "Using: $DOCKER_COMPOSE_CMD"
}

check_container_status() {
    print_status "Checking container status..."
    echo "=================================="
    
    $DOCKER_COMPOSE_CMD ps
    
    echo ""
    print_status "Container health status:"
    
    containers=("youtubeanalyzer-backend-1" "youtubeanalyzer-frontend-1" "youtubeanalyzer-postgres-1" "youtubeanalyzer-redis-1" "youtubeanalyzer-celery_worker-1" "youtubeanalyzer-celery_beat-1")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container" 2>/dev/null || echo "not-found")
            status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not-found")
            
            if [ "$status" = "running" ]; then
                if [ "$health" = "healthy" ]; then
                    print_success "$container: $status ($health)"
                elif [ "$health" = "no-healthcheck" ]; then
                    print_warning "$container: $status (no health check)"
                else
                    print_warning "$container: $status ($health)"
                fi
            else
                print_error "$container: $status"
            fi
        else
            print_error "$container: not found"
        fi
    done
}

show_recent_logs() {
    local service=$1
    local lines=${2:-50}
    
    print_status "Recent logs for $service (last $lines lines):"
    echo "=================================="
    
    if docker ps --format "table {{.Names}}" | grep -q "youtubeanalyzer-${service}-1"; then
        docker logs --tail "$lines" "youtubeanalyzer-${service}-1" 2>&1 | head -50
    else
        print_error "Container youtubeanalyzer-${service}-1 not found"
    fi
    echo ""
}

check_network_connectivity() {
    print_status "Checking network connectivity..."
    echo "=================================="
    
    if docker exec youtubeanalyzer-backend-1 ping -c 1 postgres &>/dev/null; then
        print_success "Backend -> Postgres: OK"
    else
        print_error "Backend -> Postgres: FAILED"
    fi
    
    if docker exec youtubeanalyzer-backend-1 ping -c 1 redis &>/dev/null; then
        print_success "Backend -> Redis: OK"
    else
        print_error "Backend -> Redis: FAILED"
    fi
    
    if docker exec youtubeanalyzer-redis-1 redis-cli ping &>/dev/null; then
        print_success "Redis ping: OK"
    else
        print_error "Redis ping: FAILED"
    fi
    
    if docker exec youtubeanalyzer-postgres-1 pg_isready -U user -d youtube_analyzer &>/dev/null; then
        print_success "PostgreSQL ready: OK"
    else
        print_error "PostgreSQL ready: FAILED"
    fi
    
    echo ""
}

check_api_endpoints() {
    print_status "Checking API endpoints..."
    echo "=================================="
    
    sleep 2
    
    if curl -f -s http://localhost:8000/health &>/dev/null; then
        print_success "Health endpoint: OK"
        curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
    else
        print_error "Health endpoint: FAILED"
    fi
    
    if curl -f -s http://localhost:8000/docs &>/dev/null; then
        print_success "Docs endpoint: OK"
    else
        print_error "Docs endpoint: FAILED"
    fi
    
    if curl -f -s http://localhost:8000/api/v1/analysis/tasks &>/dev/null; then
        print_success "Analysis tasks endpoint: OK"
    else
        print_error "Analysis tasks endpoint: FAILED"
    fi
    
    echo ""
}

check_resource_usage() {
    print_status "Checking resource usage..."
    echo "=================================="
    
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    echo ""
}

check_file_permissions() {
    print_status "Checking file permissions..."
    echo "=================================="
    
    print_status "Frontend .next directory:"
    docker exec youtubeanalyzer-frontend-1 ls -la /app/.next 2>/dev/null || print_warning "Frontend .next directory not accessible"
    
    print_status "Celery beat schedule file:"
    docker exec youtubeanalyzer-celery_beat-1 ls -la /tmp/celerybeat-schedule* 2>/dev/null || print_warning "Celery beat schedule file not found"
    
    echo ""
}

export_logs() {
    local output_dir="debug_logs_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$output_dir"
    
    print_status "Exporting logs to $output_dir..."
    
    services=("backend" "frontend" "postgres" "redis" "celery_worker" "celery_beat")
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "youtubeanalyzer-${service}-1"; then
            print_status "Exporting logs for $service..."
            docker logs "youtubeanalyzer-${service}-1" > "$output_dir/${service}.log" 2>&1
        else
            print_warning "Container youtubeanalyzer-${service}-1 not found, skipping..."
        fi
    done
    
    $DOCKER_COMPOSE_CMD ps > "$output_dir/container_status.txt"
    
    docker stats --no-stream > "$output_dir/resource_usage.txt"
    
    print_success "Logs exported to $output_dir/"
}

show_menu() {
    echo ""
    echo "YouTube Analyzer Container Debugging Tool"
    echo "========================================"
    echo "1. Check container status"
    echo "2. Show recent logs (all services)"
    echo "3. Show logs for specific service"
    echo "4. Check network connectivity"
    echo "5. Check API endpoints"
    echo "6. Check resource usage"
    echo "7. Check file permissions"
    echo "8. Export all logs"
    echo "9. Full diagnostic report"
    echo "0. Exit"
    echo ""
}

run_full_diagnostic() {
    print_status "Running full diagnostic report..."
    echo "=================================="
    
    check_container_status
    check_network_connectivity
    check_api_endpoints
    check_resource_usage
    check_file_permissions
    
    print_status "Recent logs from all services:"
    services=("backend" "frontend" "postgres" "redis" "celery_worker" "celery_beat")
    for service in "${services[@]}"; do
        show_recent_logs "$service" 20
    done
}

main() {
    check_docker_compose
    
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Select an option (0-9): " choice
            
            case $choice in
                1)
                    check_container_status
                    ;;
                2)
                    services=("backend" "frontend" "postgres" "redis" "celery_worker" "celery_beat")
                    for service in "${services[@]}"; do
                        show_recent_logs "$service" 20
                    done
                    ;;
                3)
                    echo "Available services: backend, frontend, postgres, redis, celery_worker, celery_beat"
                    read -p "Enter service name: " service
                    read -p "Number of lines (default 50): " lines
                    lines=${lines:-50}
                    show_recent_logs "$service" "$lines"
                    ;;
                4)
                    check_network_connectivity
                    ;;
                5)
                    check_api_endpoints
                    ;;
                6)
                    check_resource_usage
                    ;;
                7)
                    check_file_permissions
                    ;;
                8)
                    export_logs
                    ;;
                9)
                    run_full_diagnostic
                    ;;
                0)
                    print_success "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option. Please try again."
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        case $1 in
            "status")
                check_container_status
                ;;
            "logs")
                if [ -n "$2" ]; then
                    show_recent_logs "$2" "${3:-50}"
                else
                    services=("backend" "frontend" "postgres" "redis" "celery_worker" "celery_beat")
                    for service in "${services[@]}"; do
                        show_recent_logs "$service" 20
                    done
                fi
                ;;
            "network")
                check_network_connectivity
                ;;
            "api")
                check_api_endpoints
                ;;
            "resources")
                check_resource_usage
                ;;
            "permissions")
                check_file_permissions
                ;;
            "export")
                export_logs
                ;;
            "full")
                run_full_diagnostic
                ;;
            *)
                echo "Usage: $0 [status|logs [service] [lines]|network|api|resources|permissions|export|full]"
                echo "Run without arguments for interactive mode"
                exit 1
                ;;
        esac
    fi
}

main "$@"
