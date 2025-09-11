#!/bin/bash
# Main Docker Orchestration Script for Tumor Detection Platform
# Provides easy access to all platform services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running or not accessible"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Tumor Detection Platform - Docker Orchestration"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start              Start all services with web GUI"
    echo "  stop               Stop all services gracefully"
    echo "  restart            Restart all services"
    echo "  status             Show service status"
    echo "  logs [service]     View logs (all or specific service)"
    echo "  build              Rebuild Docker images"
    echo "  cleanup            Clean up Docker resources"
    echo "  shell              Open interactive shell in main container"
    echo "  test               Run Docker-based tests"
    echo "  help               Show this help message"
    echo ""
    echo "Services:"
    echo "  - Web GUI: http://localhost:8000/gui"
    echo "  - API: http://localhost:8000"
    echo "  - MLflow: http://localhost:5001"
    echo "  - MONAI Label: http://localhost:8001"
    echo ""
}

# Function to start services
start_services() {
    print_info "Starting Tumor Detection Platform services..."

    check_docker

    # Change to docker directory
    cd "$DOCKER_DIR"

    # Use appropriate compose file based on system
    COMPOSE_FILE="docker-compose.yml"

    # Check for GPU support
    if command -v nvidia-smi >/dev/null 2>&1; then
        print_info "NVIDIA GPU detected, using GPU-enabled configuration"
    elif command -v rocm-smi >/dev/null 2>&1; then
        print_info "AMD GPU detected, consider using ROCm configuration"
    else
        print_info "No GPU detected, using CPU-only configuration"
        COMPOSE_FILE="docker-compose.cpu.yml"
    fi

    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d

    print_success "Services started successfully!"
    print_info "Access points:"
    echo "  🌐 Web GUI: http://localhost:8000/gui"
    echo "  🔌 API Health: http://localhost:8000/health"
    echo "  📊 MLflow UI: http://localhost:5001"
    echo "  🏷️  MONAI Label: http://localhost:8001/info/"

    # Try to open GUI automatically
    if command -v xdg-open >/dev/null 2>&1; then
        print_info "Opening web GUI..."
        xdg-open "http://localhost:8000/gui" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        print_info "Opening web GUI..."
        open "http://localhost:8000/gui" >/dev/null 2>&1 &
    fi
}

# Function to stop services
stop_services() {
    print_info "Stopping services..."
    check_docker
    cd "$DOCKER_DIR"
    docker-compose down
    print_success "Services stopped"
}

# Function to restart services
restart_services() {
    stop_services
    start_services
}

# Function to show status
show_status() {
    print_info "Service status:"
    check_docker
    cd "$DOCKER_DIR"
    docker-compose ps

    echo ""
    print_info "Health checks:"

    # Check API health
    if curl -sf "http://localhost:8000/health" >/dev/null 2>&1; then
        print_success "API: Running"
    else
        print_warning "API: Not responding"
    fi

    # Check MLflow
    if curl -sf "http://localhost:5001" >/dev/null 2>&1; then
        print_success "MLflow: Running"
    else
        print_warning "MLflow: Not responding"
    fi

    # Check MONAI Label
    if curl -sf "http://localhost:8001/info/" >/dev/null 2>&1; then
        print_success "MONAI Label: Running"
    else
        print_warning "MONAI Label: Not responding"
    fi
}

# Function to show logs
show_logs() {
    check_docker
    cd "$DOCKER_DIR"

    if [ -n "$1" ]; then
        print_info "Showing logs for service: $1"
        docker-compose logs -f "$1"
    else
        print_info "Showing logs for all services"
        docker-compose logs -f
    fi
}

# Function to build images
build_images() {
    print_info "Building Docker images..."
    check_docker
    cd "$DOCKER_DIR"
    docker-compose build
    print_success "Images built successfully"
}

# Function to cleanup
cleanup() {
    print_info "Cleaning up Docker resources..."
    check_docker
    cd "$DOCKER_DIR"

    # Stop and remove containers
    docker-compose down -v

    # Remove unused images (optional)
    docker image prune -f

    print_success "Cleanup completed"
}

# Function to open shell
open_shell() {
    check_docker
    cd "$DOCKER_DIR"

    # Find running container
    CONTAINER=$(docker-compose ps -q tumor-detection-dev 2>/dev/null || docker-compose ps -q tumor-detection-prod 2>/dev/null || echo "")

    if [ -n "$CONTAINER" ]; then
        print_info "Opening shell in container..."
        docker exec -it "$CONTAINER" /bin/bash
    else
        print_error "No running containers found. Start services first with: $0 start"
    fi
}

# Function to run tests
run_tests() {
    print_info "Running Docker-based tests..."
    check_docker
    cd "$DOCKER_DIR"

    # Run test-lite container
    if [ -f "docker-compose.test-lite.yml" ]; then
        docker-compose -f docker-compose.test-lite.yml up --build --exit-code-from tumor-test-lite
    else
        print_warning "Test configuration not found, running basic tests"
        docker build -f images/Dockerfile.test-lite -t tumor-test-lite "$PROJECT_ROOT"
        docker run --rm tumor-test-lite
    fi
}

# Main execution logic
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    build)
        build_images
        ;;
    cleanup)
        cleanup
        ;;
    shell)
        open_shell
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
