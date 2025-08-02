#!/bin/bash

# Medical GUI Startup Script
echo "🏥 Starting Medical Imaging AI System"
echo "===================================="

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
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_status "Project root: $PROJECT_ROOT"
print_status "Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found! Please install Python 3.8+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ] && [ ! -d "$PROJECT_ROOT/venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    cd "$PROJECT_ROOT"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    print_status "Activating virtual environment..."
    if [ -d "$PROJECT_ROOT/.venv" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    else
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
fi

# Check GPU availability
print_status "Checking GPU availability..."

# ROCm/AMD GPU detection
if command -v rocm-smi &> /dev/null; then
    print_success "ROCm detected - AMD GPU support available"
    export HSA_OVERRIDE_GFX_VERSION=10.3.0
    export ROCM_HOME=/opt/rocm
elif nvidia-smi &> /dev/null 2>&1; then
    print_success "NVIDIA GPU detected - CUDA support available"
else
    print_warning "No GPU detected - using CPU mode"
fi

# Start the medical imaging backend
print_status "Starting Medical AI Backend..."
cd "$PROJECT_ROOT"

# Check if the main API file exists
if [ -f "src/medical_imaging_api.py" ]; then
    print_status "Starting FastAPI backend..."
    
    # Try to start the server and capture output
    python -m uvicorn src.medical_imaging_api:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 5
    
    # Check if the process is still running
    if kill -0 $BACKEND_PID 2>/dev/null; then
        # Check if it's responding to HTTP requests
        if curl -s -f http://localhost:8000 > /dev/null 2>&1 || curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
            print_success "Backend started successfully on http://localhost:8000"
        else
            print_warning "Backend process running but may still be starting up..."
            print_status "Check http://localhost:8000/docs in your browser"
        fi
    else
        print_error "Backend failed to start. Check the error messages above."
        BACKEND_PID=""
    fi
elif [ -f "src/medical_ai_backend.py" ]; then
    print_status "Starting alternative backend..."
    python src/medical_ai_backend.py &
    BACKEND_PID=$!
    sleep 2
else
    print_warning "No backend API found. Starting basic medical imaging system..."
    if [ -f "src/medical_imaging_ai.py" ]; then
        python src/medical_imaging_ai.py &
        BACKEND_PID=$!
    else
        print_error "No medical imaging application found in src/"
        exit 1
    fi
fi

# Start the GUI if available
print_status "Checking for GUI components..."

if [ -d "gui/frontend" ]; then
    print_status "Starting React frontend..."
    cd "$PROJECT_ROOT/gui/frontend"
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/react-scripts" ]; then
            print_status "Installing frontend dependencies with legacy peer deps..."
            npm install --legacy-peer-deps
            if [ $? -ne 0 ]; then
                print_warning "npm install failed, trying with --force..."
                npm install --force
            fi
        fi
        
        # Check if react-scripts is available before starting
        if [ -f "node_modules/.bin/react-scripts" ]; then
            print_status "Starting React development server..."
            npm start &
            FRONTEND_PID=$!
            print_success "Frontend starting on http://localhost:3000"
        else
            print_warning "React scripts not found, frontend may not start properly"
            print_status "Try manually running: cd gui/frontend && npm install --legacy-peer-deps"
        fi
    fi
elif [ -d "frontend" ]; then
    print_status "Starting alternative frontend..."
    cd "$PROJECT_ROOT/frontend"
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/react-scripts" ]; then
            print_status "Installing frontend dependencies with legacy peer deps..."
            npm install --legacy-peer-deps
            if [ $? -ne 0 ]; then
                print_warning "npm install failed, trying with --force..."
                npm install --force
            fi
        fi
        
        # Check if react-scripts is available before starting
        if [ -f "node_modules/.bin/react-scripts" ]; then
            print_status "Starting React development server..."
            npm start &
            FRONTEND_PID=$!
            print_success "Frontend starting on http://localhost:3000"
        else
            print_warning "React scripts not found, frontend may not start properly"
            print_status "Try manually running: cd frontend && npm install --legacy-peer-deps"
        fi
    fi
fi

# Wait a moment for services to start
sleep 5

print_success "🚀 Medical Imaging AI System Started!"
echo ""
print_status "Available services:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "   • Frontend GUI: http://localhost:3000"
    print_status "Note: Frontend may take 30-60 seconds to fully start"
else
    print_warning "Frontend not started due to dependency issues"
    print_status "To fix frontend: ./scripts/setup/fix_frontend.sh"
fi
echo ""
print_status "🔧 Troubleshooting:"
echo "   • Frontend issues: ./scripts/setup/fix_frontend.sh"
echo "   • Check logs: docker logs or terminal output above"
echo "   • Port conflicts: Check if services are already running"
echo ""
print_status "To stop all services, press Ctrl+C"

# Create cleanup function
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    print_success "Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running
wait
