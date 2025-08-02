#!/bin/bash

# Test Runner Script for Medical Imaging Project
echo "🧪 Running Medical Imaging Test Suite"
echo "==================================="

# Colors for output
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

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Create necessary directories
mkdir -p logs/test_logs
mkdir -p reports/coverage
mkdir -p reports/junit

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    print_error "No virtual environment found!"
    exit 1
fi

# Run different test suites
run_tests() {
    local test_type=$1
    local pytest_args=$2
    
    echo ""
    print_status "Running $test_type tests..."
    
    pytest $pytest_args \
        --junitxml="reports/junit/${test_type}_results.xml" \
        --log-file="logs/test_logs/${test_type}_tests.log" \
        -v "$@"
    
    if [ $? -eq 0 ]; then
        print_success "$test_type tests completed successfully"
    else
        print_error "$test_type tests failed"
        return 1
    fi
}

# Clean previous test artifacts
print_status "Cleaning previous test artifacts..."
rm -rf reports/* logs/test_logs/*

# Run unit tests
run_tests "unit" "-m unit"

# Run integration tests
run_tests "integration" "-m integration"

# Run performance tests (if GPU available)
if python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null; then
    run_tests "performance" "-m performance"
else
    print_warning "Skipping performance tests - No GPU available"
fi

# Generate coverage report
print_status "Generating coverage report..."
coverage html -d reports/coverage

# Print test summary
echo ""
print_status "Test Summary:"
echo "• Test reports: ${PROJECT_ROOT}/reports/junit/"
echo "• Coverage report: ${PROJECT_ROOT}/reports/coverage/index.html"
echo "• Test logs: ${PROJECT_ROOT}/logs/test_logs/"
echo ""

# Check for critical failures
if [ -f "logs/test_logs/critical_failures.log" ]; then
    print_error "Critical failures detected! Check logs/test_logs/critical_failures.log"
    exit 1
fi

print_success "All test suites completed!"
