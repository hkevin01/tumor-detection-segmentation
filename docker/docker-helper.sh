#!/bin/bash
# Docker Helper Script
# Simplifies common Docker operations for the tumor detection project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
    echo "Docker Helper Script for Tumor Detection Project"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build [target]     Build Docker images (default: all)"
    echo "  up [service]       Start services (default: development)"
    echo "  down               Stop all services"
    echo "  logs [service]     Show logs for service"
    echo "  shell [service]    Open shell in running container"
    echo "  test               Run tests in container"
    echo "  clean              Remove containers and images"
    echo "  status             Show status of services"
    echo ""
    echo "Targets:"
    echo "  dev                Development environment"
    echo "  prod               Production environment"
    echo "  test               Testing environment"
    echo "  cpu                CPU-only environment"
    echo "  phase4             Phase 4 advanced environment"
    echo ""
    echo "Examples:"
    echo "  $0 build dev       # Build development image"
    echo "  $0 up              # Start development environment"
    echo "  $0 logs api        # Show API service logs"
    echo "  $0 shell dev       # Open shell in dev container"
}

# Function to build images
build_image() {
    local target=$1
    check_docker

    case $target in
        "dev")
            print_info "Building development image..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" build tumor-detection-dev
            ;;
        "prod")
            print_info "Building production image..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" build tumor-detection-prod
            ;;
        "test")
            print_info "Building test image..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" build tumor-detection-test
            ;;
        "cpu")
            print_info "Building CPU-only image..."
            docker-compose -f "$DOCKER_DIR/docker-compose.cpu.yml" build
            ;;
        "phase4")
            print_info "Building Phase 4 image..."
            docker-compose -f "$DOCKER_DIR/docker-compose.phase4.yml" build
            ;;
        *)
            print_info "Building all images..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" build
            ;;
    esac

    print_success "Build completed"
}

# Function to start services
start_services() {
    local service=$1
    check_docker

    case $service in
        "dev")
            print_info "Starting development environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" up -d tumor-detection-dev
            ;;
        "prod")
            print_info "Starting production environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" up -d tumor-detection-prod
            ;;
        "test")
            print_info "Starting test environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" up -d tumor-detection-test
            ;;
        "jupyter")
            print_info "Starting Jupyter environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" up -d jupyter
            ;;
        "cpu")
            print_info "Starting CPU-only environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.cpu.yml" up -d
            ;;
        "phase4")
            print_info "Starting Phase 4 environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.phase4.yml" up -d
            ;;
        *)
            print_info "Starting development environment..."
            docker-compose -f "$DOCKER_DIR/docker-compose.yml" up -d tumor-detection-dev
            ;;
    esac

    print_success "Services started"
}

# Function to stop services
stop_services() {
    check_docker
    print_info "Stopping all services..."
    docker-compose -f "$DOCKER_DIR/docker-compose.yml" down 2>/dev/null || true
    docker-compose -f "$DOCKER_DIR/docker-compose.cpu.yml" down 2>/dev/null || true
    docker-compose -f "$DOCKER_DIR/docker-compose.phase4.yml" down 2>/dev/null || true
    print_success "Services stopped"
}

# Function to show logs
show_logs() {
    local service=$1
    check_docker

    if [ -z "$service" ]; then
        docker-compose -f "$DOCKER_DIR/docker-compose.yml" logs -f
    else
        docker-compose -f "$DOCKER_DIR/docker-compose.yml" logs -f "$service"
    fi
}

# Function to open shell
open_shell() {
    local service=$1
    check_docker

    if [ -z "$service" ]; then
        service="tumor-detection-dev"
    fi

    print_info "Opening shell in $service container..."
    docker-compose -f "$DOCKER_DIR/docker-compose.yml" exec "$service" /bin/bash
}

# Function to run tests
run_tests() {
    check_docker
    print_info "Running tests..."
    docker-compose -f "$DOCKER_DIR/docker-compose.yml" up --abort-on-container-exit tumor-detection-test
}

# Function to clean up
cleanup() {
    check_docker
    print_warning "This will remove all containers and images. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Cleaning up Docker resources..."
        docker-compose -f "$DOCKER_DIR/docker-compose.yml" down -v --rmi all 2>/dev/null || true
        docker-compose -f "$DOCKER_DIR/docker-compose.cpu.yml" down -v --rmi all 2>/dev/null || true
        docker-compose -f "$DOCKER_DIR/docker-compose.phase4.yml" down -v --rmi all 2>/dev/null || true
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to show status
show_status() {
    check_docker
    print_info "Docker services status:"
    docker-compose -f "$DOCKER_DIR/docker-compose.yml" ps
    echo ""
    print_info "Docker images:"
    docker images | grep tumor-detection
}

# Main script logic
case "${1:-help}" in
    "build")
        build_image "$2"
        ;;
    "up")
        start_services "$2"
        ;;
    "down")
        stop_services
        ;;
    "logs")
        show_logs "$2"
        ;;
    "shell")
        open_shell "$2"
        ;;
    "test")
        run_tests
        ;;
    "clean")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_usage
        ;;
esac
