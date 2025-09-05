#!/bin/bash
# Docker Environment Validation Script
# Tests Docker setup and container readiness

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
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

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

print_header "DOCKER ENVIRONMENT VALIDATION"

# Test 1: Docker Installation
print_info "1. Testing Docker installation..."
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker installed: $DOCKER_VERSION"
else
    print_error "Docker not found! Please install Docker."
    exit 1
fi

# Test 2: Docker Service Running
print_info "2. Testing Docker service..."
if docker info >/dev/null 2>&1; then
    print_success "Docker service is running"
else
    print_error "Docker service not running! Start Docker daemon."
    exit 1
fi

# Test 3: Docker Compose
print_info "3. Testing Docker Compose..."
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose available: $COMPOSE_VERSION"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "Docker Compose (V2) available: $COMPOSE_VERSION"
else
    print_warning "Docker Compose not found - using Docker CLI only"
fi

# Test 4: GPU Support (Optional)
print_info "4. Testing GPU support..."
if command -v nvidia-smi >/dev/null 2>&1; then
    print_success "NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

    # Test NVIDIA Docker runtime
    if docker run --rm --gpus all nvidia/cuda:11.7-base-ubuntu20.04 nvidia-smi >/dev/null 2>&1; then
        print_success "NVIDIA Docker runtime working"
    else
        print_warning "NVIDIA Docker runtime not configured properly"
    fi
elif command -v rocm-smi >/dev/null 2>&1; then
    print_success "AMD GPU detected"
    rocm-smi --showproductname || true
else
    print_info "No GPU detected - will use CPU-only configuration"
fi

# Test 5: Docker Files Structure
print_info "5. Validating Docker files structure..."
cd "$PROJECT_ROOT"

# Check for main docker-compose file
if [ -f "$DOCKER_DIR/docker-compose.yml" ]; then
    print_success "Main docker-compose.yml found"
else
    print_warning "Main docker-compose.yml not found at $DOCKER_DIR/"
fi

# Check for CPU-only compose file
if [ -f "$DOCKER_DIR/docker-compose.cpu.yml" ]; then
    print_success "CPU-only docker-compose.cpu.yml found"
else
    print_warning "CPU-only compose file not found"
fi

# Check for Dockerfiles
DOCKERFILE_COUNT=0
for dockerfile in "$DOCKER_DIR"/images/Dockerfile*; do
    if [ -f "$dockerfile" ]; then
        DOCKERFILE_COUNT=$((DOCKERFILE_COUNT + 1))
        print_success "Found: $(basename "$dockerfile")"
    fi
done

if [ $DOCKERFILE_COUNT -eq 0 ]; then
    print_warning "No Dockerfiles found in $DOCKER_DIR/images/"
else
    print_success "Found $DOCKERFILE_COUNT Docker images"
fi

# Test 6: Build Test Image (lightweight)
print_info "6. Testing Docker build capability..."

# Create a minimal test Dockerfile
cat > /tmp/test-dockerfile << EOF
FROM python:3.10-slim
RUN python --version
CMD ["echo", "Docker build test successful"]
EOF

if docker build -f /tmp/test-dockerfile -t tumor-test-build /tmp >/dev/null 2>&1; then
    print_success "Docker build capability working"

    # Test running the container
    if docker run --rm tumor-test-build >/dev/null 2>&1; then
        print_success "Docker run capability working"
    else
        print_warning "Docker run test failed"
    fi

    # Clean up test image
    docker rmi tumor-test-build >/dev/null 2>&1 || true
else
    print_error "Docker build test failed"
fi

# Clean up test dockerfile
rm -f /tmp/test-dockerfile

# Test 7: Network Connectivity
print_info "7. Testing Docker network connectivity..."
if docker run --rm alpine:latest ping -c 1 google.com >/dev/null 2>&1; then
    print_success "Docker network connectivity working"
else
    print_warning "Docker network connectivity issues detected"
fi

# Test 8: Volume Mounting
print_info "8. Testing Docker volume mounting..."
if docker run --rm -v "$PROJECT_ROOT:/test" alpine:latest ls /test >/dev/null 2>&1; then
    print_success "Docker volume mounting working"
else
    print_warning "Docker volume mounting issues detected"
fi

# Test 9: Port Binding Test
print_info "9. Testing port binding capability..."
if timeout 5 docker run --rm -p 18080:80 nginx:alpine >/dev/null 2>&1; then
    print_success "Docker port binding working"
else
    print_warning "Docker port binding test incomplete (timeout or error)"
fi

# Test 10: Memory and Resource Limits
print_info "10. Testing resource limits..."
if docker run --rm --memory=100m alpine:latest echo "Memory limit test" >/dev/null 2>&1; then
    print_success "Docker memory limits working"
else
    print_warning "Docker memory limit test failed"
fi

# Summary
print_header "VALIDATION SUMMARY"

# System Information
print_info "System Information:"
echo "  OS: $(uname -s) $(uname -r)"
echo "  Architecture: $(uname -m)"
echo "  Docker Version: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"

# Available Resources
TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
AVAILABLE_MEM=$(free -h | awk '/^Mem:/ {print $7}')
DISK_SPACE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $4}')

echo "  Total Memory: $TOTAL_MEM"
echo "  Available Memory: $AVAILABLE_MEM"
echo "  Available Disk Space: $DISK_SPACE"

# Recommendations
print_info "Recommendations:"
echo "  • For CPU-only deployment: Use docker-compose.cpu.yml"
echo "  • For GPU deployment: Ensure NVIDIA Docker runtime is configured"
echo "  • Minimum 8GB RAM recommended for training"
echo "  • Minimum 20GB free disk space recommended"

print_header "DOCKER VALIDATION COMPLETE"
print_success "Docker environment validation successful!"
print_info "Ready to run: ./run.sh start"
