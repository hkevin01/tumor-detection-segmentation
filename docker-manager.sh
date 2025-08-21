#!/bin/bash
# Docker Management Script for Tumor Detection Project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="tumor-detection"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to check Docker and Docker Compose
check_dependencies() {
    print_header "Checking Dependencies"

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    print_status "Docker and Docker Compose are available"
}

# Function to build Docker images
build() {
    print_header "Building Docker Images"

    # Build all stages
    docker-compose build tumor-detection-dev
    docker-compose build tumor-detection-prod
    docker-compose build tumor-detection-test

    print_status "All images built successfully"
}

# Function to start development environment
dev() {
    print_header "Starting Development Environment"

    # Remove virtual environment if it exists
    if [ -d "venv" ]; then
        print_warning "Removing existing virtual environment..."
        rm -rf venv
    fi

    docker-compose up -d tumor-detection-dev

    print_status "Development environment started"
    print_status "Access the container: docker-compose exec tumor-detection-dev bash"
    print_status "FastAPI will be available at: http://localhost:8000"
    print_status "Jupyter Lab will be available at: http://localhost:8888"
    print_status "TensorBoard will be available at: http://localhost:6006"
}

# Function to start development with Jupyter
jupyter() {
    print_header "Starting Jupyter Lab Environment"

    docker-compose --profile jupyter up -d

    print_status "Jupyter Lab started"
    print_status "Access Jupyter at: http://localhost:8889"
}

# Function to run tests
test() {
    print_header "Running Tests in Docker Container"

    # Build test image if it doesn't exist
    docker-compose build tumor-detection-test

    # Run tests
    docker-compose --profile testing run --rm tumor-detection-test

    print_status "Tests completed"
}

# Function to start production environment
prod() {
    print_header "Starting Production Environment"

    docker-compose --profile production up -d

    print_status "Production environment started"
    print_status "API available at: http://localhost:8080"
}

# Function to start full stack (with database and cache)
stack() {
    print_header "Starting Full Stack"

    docker-compose --profile database --profile cache --profile mlops up -d

    print_status "Full stack started"
    print_status "PostgreSQL available at: localhost:5432"
    print_status "Redis available at: localhost:6379"
    print_status "MLFlow available at: http://localhost:5000"
}

# Function to stop all services
stop() {
    print_header "Stopping All Services"

    docker-compose down

    print_status "All services stopped"
}

# Function to clean up
clean() {
    print_header "Cleaning Up Docker Resources"

    # Stop all services
    docker-compose down -v

    # Remove images
    docker-compose down --rmi all

    # Clean up Docker system
    docker system prune -f

    print_status "Cleanup completed"
}

# Function to show logs
logs() {
    service=${1:-tumor-detection-dev}
    print_header "Showing logs for $service"

    docker-compose logs -f "$service"
}

# Function to execute command in container
exec() {
    service=${1:-tumor-detection-dev}
    shift
    command=${*:-bash}

    print_header "Executing command in $service"

    docker-compose exec "$service" $command
}

# Function to show status
status() {
    print_header "Docker Services Status"

    docker-compose ps

    echo ""
    print_header "Docker Images"
    docker images | grep tumor-detection

    echo ""
    print_header "Docker Volumes"
    docker volume ls | grep tumor
}

# Function to backup data
backup() {
    print_header "Backing Up Data Volumes"

    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="./backups/$timestamp"
    mkdir -p "$backup_dir"

    # Backup volumes
    docker run --rm -v tumor_data:/data -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/data.tar.gz -C /data .
    docker run --rm -v tumor_models:/models -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/models.tar.gz -C /models .
    docker run --rm -v tumor_logs:/logs -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/logs.tar.gz -C /logs .

    print_status "Backup completed: $backup_dir"
}

# Function to restore data
restore() {
    backup_path=${1}

    if [ -z "$backup_path" ]; then
        print_error "Please specify backup path"
        exit 1
    fi

    print_header "Restoring Data from $backup_path"

    # Restore volumes
    docker run --rm -v tumor_data:/data -v "$backup_path":/backup alpine tar xzf /backup/data.tar.gz -C /data
    docker run --rm -v tumor_models:/models -v "$backup_path":/backup alpine tar xzf /backup/models.tar.gz -C /models
    docker run --rm -v tumor_logs:/logs -v "$backup_path":/backup alpine tar xzf /backup/logs.tar.gz -C /logs

    print_status "Restore completed"
}

# Function to show help
help() {
    print_header "Docker Management Script - Tumor Detection Project"

    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build           Build all Docker images"
    echo "  dev             Start development environment"
    echo "  jupyter         Start Jupyter Lab environment"
    echo "  test            Run tests in container"
    echo "  prod            Start production environment"
    echo "  stack           Start full stack (DB, Cache, MLOps)"
    echo "  stop            Stop all services"
    echo "  clean           Clean up Docker resources"
    echo "  logs [service]  Show logs for service (default: tumor-detection-dev)"
    echo "  exec [service] [cmd]  Execute command in service"
    echo "  status          Show services and images status"
    echo "  backup          Backup data volumes"
    echo "  restore [path]  Restore data from backup"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                          # Start development environment"
    echo "  $0 test                         # Run all tests"
    echo "  $0 logs tumor-detection-dev     # Show dev logs"
    echo "  $0 exec tumor-detection-dev     # Open bash in dev container"
    echo "  $0 backup                       # Backup all data"
}

# Main script logic
case "${1:-help}" in
    build)
        check_dependencies
        build
        ;;
    dev)
        check_dependencies
        dev
        ;;
    jupyter)
        check_dependencies
        jupyter
        ;;
    test)
        check_dependencies
        test
        ;;
    prod)
        check_dependencies
        prod
        ;;
    stack)
        check_dependencies
        stack
        ;;
    stop)
        stop
        ;;
    clean)
        clean
        ;;
    logs)
        logs "${2}"
        ;;
    exec)
        exec "${2}" "${@:3}"
        ;;
    status)
        status
        ;;
    backup)
        backup
        ;;
    restore)
        restore "${2}"
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
