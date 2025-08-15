#!/bin/bash

# Medical Imaging AI Platform - Docker Run Script
# This script manages the complete Docker deployment and GUI display

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="config/docker/docker-compose.yml"
PROJECT_NAME="medical-ai-platform"

# URLs for services
WEB_URL="http://localhost:8000"
MLFLOW_URL="http://localhost:5001"
MONAI_LABEL_URL="http://localhost:8001"
GUI_URL="http://localhost:8000/gui"

print_banner() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "🧠 Medical Imaging AI Platform - Docker Deployment"
    echo "=================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}Advanced tumor detection and segmentation platform${NC}"
    echo -e "${CYAN}with MONAI Label integration and MLflow tracking${NC}"
    echo ""
}

print_services() {
    echo -e "${BLUE}📋 Available Services:${NC}"
    echo -e "  🌐 Main Application:    ${GREEN}${WEB_URL}${NC}"
    echo -e "  🎨 Web GUI:             ${GREEN}${GUI_URL}${NC}"
    echo -e "  📊 MLflow UI:           ${GREEN}${MLFLOW_URL}${NC}"
    echo -e "  🎯 MONAI Label Server:  ${GREEN}${MONAI_LABEL_URL}${NC}"
    echo ""
}

check_docker() {
    echo -e "${YELLOW}🐳 Checking Docker installation...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon is not running. Please start Docker first.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker is ready${NC}"
}

check_nvidia_docker() {
    echo -e "${YELLOW}🎮 Checking NVIDIA Docker support...${NC}"

    if command -v nvidia-docker &> /dev/null || docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✅ NVIDIA Docker support detected${NC}"
        export DOCKER_GPU_SUPPORT=true
    else
        echo -e "${YELLOW}⚠️  NVIDIA Docker support not detected. Using CPU-only mode.${NC}"
        export DOCKER_GPU_SUPPORT=false
    fi
}

create_directories() {
    echo -e "${YELLOW}📁 Creating necessary directories...${NC}"

    mkdir -p data/monai_label
    mkdir -p models
    mkdir -p logs
    mkdir -p uploads
    mkdir -p temp

    echo -e "${GREEN}✅ Directories created${NC}"
}

build_images() {
    echo -e "${YELLOW}🔨 Building Docker images...${NC}"

    if [ "$DOCKER_GPU_SUPPORT" = true ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" build
    else
        echo -e "${YELLOW}⚠️  Building without GPU support${NC}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" build
    fi

    echo -e "${GREEN}✅ Docker images built successfully${NC}"
}

start_services() {
    echo -e "${YELLOW}🚀 Starting services...${NC}"

    # Start services in detached mode
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" up -d

    echo -e "${GREEN}✅ Services started successfully${NC}"
    echo ""

    # Wait for services to be ready
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 10

    # Check service health
    check_service_health
}

check_service_health() {
    echo -e "${YELLOW}🏥 Checking service health...${NC}"

    # Check web service
    if curl -f -s "$WEB_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Web service: Running${NC}"
    else
        echo -e "${YELLOW}⏳ Web service: Starting...${NC}"
    fi

    # Check MLflow service
    if curl -f -s "$MLFLOW_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ MLflow service: Running${NC}"
    else
        echo -e "${YELLOW}⏳ MLflow service: Starting...${NC}"
    fi

    # Check MONAI Label service
    if curl -f -s "$MONAI_LABEL_URL/info/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ MONAI Label service: Running${NC}"
    else
        echo -e "${YELLOW}⏳ MONAI Label service: Starting...${NC}"
    fi

    echo ""
}

show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" ps
    echo ""
}

open_gui() {
    echo -e "${YELLOW}🌐 Opening web GUI...${NC}"

    # Try to open the GUI in the default browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "$GUI_URL" 2>/dev/null &
    elif command -v open &> /dev/null; then
        open "$GUI_URL" 2>/dev/null &
    elif command -v start &> /dev/null; then
        start "$GUI_URL" 2>/dev/null &
    else
        echo -e "${YELLOW}⚠️  Could not auto-open browser. Please manually open: ${GREEN}${GUI_URL}${NC}"
    fi
}

show_logs() {
    echo -e "${YELLOW}📜 Showing service logs...${NC}"
    echo -e "${BLUE}Use Ctrl+C to exit log view${NC}"
    echo ""

    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
}

stop_services() {
    echo -e "${YELLOW}🛑 Stopping services...${NC}"

    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" down

    echo -e "${GREEN}✅ Services stopped${NC}"
}

cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"

    # Stop and remove containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$PROJECT_NAME" down -v --remove-orphans

    # Remove unused images (optional)
    read -p "Remove unused Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -f
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    fi
}

show_help() {
    echo -e "${CYAN}Usage: $0 [COMMAND]${NC}"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  start       Start all services and open GUI"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show service status"
    echo "  logs        Show service logs"
    echo "  build       Build Docker images"
    echo "  gui         Open web GUI in browser"
    echo "  cleanup     Stop services and clean up Docker resources"
    echo "  help        Show this help message"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 start    # Start all services"
    echo "  $0 logs     # View logs"
    echo "  $0 cleanup  # Clean up everything"
}

# Main script logic
case "${1:-start}" in
    "start")
        print_banner
        check_docker
        check_nvidia_docker
        create_directories
        build_images
        start_services
        print_services
        show_status
        open_gui
        echo -e "${GREEN}🎉 Medical Imaging AI Platform is running!${NC}"
        echo -e "${CYAN}Use '$0 logs' to view logs or '$0 stop' to shut down${NC}"
        ;;
    "stop")
        print_banner
        stop_services
        ;;
    "restart")
        print_banner
        stop_services
        sleep 2
        start_services
        print_services
        open_gui
        ;;
    "status")
        print_banner
        show_status
        check_service_health
        print_services
        ;;
    "logs")
        show_logs
        ;;
    "build")
        print_banner
        check_docker
        create_directories
        build_images
        ;;
    "gui")
        open_gui
        echo -e "${GREEN}✅ Opening GUI at: ${GUI_URL}${NC}"
        ;;
    "cleanup")
        print_banner
        cleanup
        ;;
    "help"|"-h"|"--help")
        print_banner
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
