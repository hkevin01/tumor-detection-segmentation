#!/bin/bash

# Medical Imaging GUI Startup Script
# This script starts the complete medical imaging system with MONAI backend

set -e

echo "🏥 Medical Imaging AI - Tumor Detection & Segmentation System"
echo "============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the project root directory."
    exit 1
fi

print_status "Checking Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Additional medical imaging dependencies
print_status "Installing additional medical imaging dependencies..."
pip install SimpleITK pydicom

# Check GPU availability (CUDA/ROCm)
print_status "Checking GPU availability..."
python3 -c "
import torch
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA device count:', torch.cuda.device_count())
    print('CUDA device name:', torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'None')
else:
    print('CUDA device count: 0')

# Check for ROCm support
try:
    if hasattr(torch.version, 'hip') and torch.version.hip is not None:
        print('ROCm/HIP available: True')
        print('HIP version:', torch.version.hip)
    else:
        print('ROCm/HIP available: False')
except:
    print('ROCm/HIP available: Unknown')

# Check available device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Default device:', device)
"

print_status "Setting up frontend dependencies..."

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    print_warning "Frontend directory not found. Please ensure the React frontend is properly set up."
else
    cd frontend
    
    # Install Node.js dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
    else
        print_status "Node.js dependencies already installed."
    fi
    
    cd ..
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/{raw,processed,models,exports}
mkdir -p logs
mkdir -p temp

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
export MEDICAL_AI_DATA_DIR="${PWD}/data"
export MEDICAL_AI_LOG_DIR="${PWD}/logs"
export MEDICAL_AI_TEMP_DIR="${PWD}/temp"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment configuration file..."
    cat > .env << EOF
# Medical Imaging AI Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=3000

# Data directories
DATA_DIR=./data
LOG_DIR=./logs
TEMP_DIR=./temp

# AI Model settings
DEFAULT_MODEL=unet
INFERENCE_DEVICE=auto
FORCE_CPU=false
MAX_BATCH_SIZE=4
INFERENCE_TIMEOUT=300

# GPU settings (auto-detects CUDA/ROCm)
GPU_MEMORY_FRACTION=0.8
ENABLE_MIXED_PRECISION=true

# Security settings (change in production)
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# DICOM settings
DICOM_MAX_FILE_SIZE=100MB
ALLOWED_MODALITIES=MR,CT,PET

# Performance settings
ENABLE_CACHING=true
CACHE_SIZE=1000
WORKER_PROCESSES=4
EOF
    print_success "Created .env configuration file"
else
    print_status "Environment configuration file already exists"
fi

print_success "Setup completed successfully!"

# ROCm/AMD GPU specific information
print_status "GPU Configuration Notes:"
echo "   • Your system is configured for ROCm (AMD GPU support)"
echo "   • If you have an AMD GPU, ensure ROCm is properly installed"
echo "   • PyTorch ROCm installation: pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.6"
echo "   • For CPU-only usage: pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
echo "   • Device detection is automatic - system will use GPU if available, CPU otherwise"

echo ""
print_status "Starting Medical Imaging AI System..."
echo ""

# Function to start the backend
start_backend() {
    print_status "Starting FastAPI backend server..."
    cd src
    python3 medical_imaging_api.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to start with retries
    print_status "Waiting for backend to initialize..."
    for i in {1..10}; do
        if curl -s http://127.0.0.1:8000/ > /dev/null; then
            print_success "Backend server started successfully (PID: $BACKEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    print_error "Failed to start backend server after waiting"
    return 1
}

# Function to start the frontend
start_frontend() {
    if [ -d "frontend" ]; then
        print_status "Starting React frontend development server..."
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        
        # Wait for frontend to start
        print_status "Waiting for frontend to initialize..."
        sleep 10
        
        print_success "Frontend server started successfully (PID: $FRONTEND_PID)"
    else
        print_warning "Frontend directory not found, skipping frontend startup"
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    print_success "All services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services
start_backend
start_frontend

echo ""
print_success "🎉 Medical Imaging AI System is now running!"
echo ""
echo "📊 Backend API: http://localhost:8000"
echo "🔍 API Documentation: http://localhost:8000/docs"
if [ -d "frontend" ]; then
    echo "🖥️  Frontend GUI: http://localhost:3000"
fi
echo ""
echo "📋 Available Features:"
echo "   • DICOM Image Viewer with multi-planar reconstruction"
echo "   • AI-powered tumor detection and segmentation"
echo "   • Patient management and study comparison"
echo "   • Longitudinal analysis and reporting"
echo "   • Model control panel with performance monitoring"
echo "   • Batch processing capabilities"
echo ""
echo "🧠 Supported AI Models:"
echo "   • UNet - Fast and reliable segmentation"
echo "   • SegResNet - High accuracy with efficient inference"
echo "   • SwinUNETR - State-of-the-art transformer-based model"
echo ""
echo "💡 Usage Instructions:"
echo "   1. Upload DICOM files through the web interface"
echo "   2. Select an AI model for analysis"
echo "   3. Run tumor detection and segmentation"
echo "   4. Review results and export findings"
echo "   5. Compare studies for longitudinal analysis"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep the script running
while true; do
    sleep 1
done
