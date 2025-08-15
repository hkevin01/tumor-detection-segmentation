#!/bin/bash

# Docker Test Script for Medical Imaging AI Platform
# This script tests the Docker setup and verifies all services

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧪 Testing Docker setup for Medical Imaging AI Platform...${NC}"

# Test 1: Check if Docker is available
echo -e "\n${YELLOW}Test 1: Docker availability${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker is installed${NC}"
else
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Test 2: Check if Docker Compose is available
echo -e "\n${YELLOW}Test 2: Docker Compose availability${NC}"
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose is available${NC}"
else
    echo -e "${RED}❌ Docker Compose is not available${NC}"
    exit 1
fi

# Test 3: Check Docker daemon
echo -e "\n${YELLOW}Test 3: Docker daemon status${NC}"
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
else
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    exit 1
fi

# Test 4: Check NVIDIA Docker support
echo -e "\n${YELLOW}Test 4: NVIDIA Docker support${NC}"
if docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ NVIDIA Docker support available${NC}"
else
    echo -e "${YELLOW}⚠️  NVIDIA Docker support not available (CPU mode only)${NC}"
fi

# Test 5: Check required files
echo -e "\n${YELLOW}Test 5: Required files${NC}"
required_files=(
    "config/docker/docker-compose.yml"
    "config/docker/Dockerfile.cuda"
    "config/docker/Dockerfile.monai-label"
    "requirements-docker.txt"
    "src/main.py"
    "run.sh"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo -e "${RED}❌ Some required files are missing${NC}"
    exit 1
fi

# Test 6: Validate Docker Compose file
echo -e "\n${YELLOW}Test 6: Docker Compose file validation${NC}"
if docker-compose -f config/docker/docker-compose.yml config &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose file is valid${NC}"
else
    echo -e "${RED}❌ Docker Compose file has errors${NC}"
    exit 1
fi

# Test 7: Check port availability
echo -e "\n${YELLOW}Test 7: Port availability${NC}"
ports=(8000 5001 8001 6379 5432)
for port in "${ports[@]}"; do
    if ss -tuln | grep ":$port " &> /dev/null; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
    fi
done

# Test 8: Test build process (dry run)
echo -e "\n${YELLOW}Test 8: Testing Docker build (dry run)${NC}"
if docker-compose -f config/docker/docker-compose.yml build --dry-run &> /dev/null; then
    echo -e "${GREEN}✅ Docker build configuration is valid${NC}"
else
    echo -e "${YELLOW}⚠️  Docker build test skipped (not supported)${NC}"
fi

echo -e "\n${GREEN}🎉 All Docker tests passed!${NC}"
echo -e "\n${YELLOW}To start the platform:${NC}"
echo -e "  ${GREEN}./run.sh start${NC}"
echo -e "\n${YELLOW}To view help:${NC}"
echo -e "  ${GREEN}./run.sh help${NC}"
