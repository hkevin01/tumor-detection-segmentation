#!/bin/bash

# Medical GUI Startup Script with Enhanced Features
echo "🏥 Starting Enhanced Medical Imaging AI System"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_feature() {
    echo -e "${PURPLE}[FEATURE]${NC} $1"
}

print_ai() {
    echo -e "${CYAN}[AI]${NC} $1"
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_status "Project root: $PROJECT_ROOT"
print_status "Initializing Enhanced Medical AI System..."

# Check Python and dependencies
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found! Please install Python 3.8+"
    exit 1
fi

# Setup virtual environment
if [ ! -d "$PROJECT_ROOT/.venv" ] && [ ! -d "$PROJECT_ROOT/venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    cd "$PROJECT_ROOT"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Install additional ML/AI packages
    print_ai "Installing enhanced ML packages..."
    pip install mlflow optuna tensorboard wandb
    pip install monai-label
    pip install plotly dash
else
    print_status "Activating virtual environment..."
    if [ -d "$PROJECT_ROOT/.venv" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    else
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
fi

# Check GPU and AI accelerators
print_ai "Detecting AI hardware accelerators..."

# ROCm/AMD GPU detection
if command -v rocm-smi &> /dev/null; then
    print_success "🔥 ROCm detected - AMD GPU support available"
    export HSA_OVERRIDE_GFX_VERSION=10.3.0
    export ROCM_HOME=/opt/rocm
    GPU_TYPE="AMD"
elif nvidia-smi &> /dev/null 2>&1; then
    print_success "⚡ NVIDIA GPU detected - CUDA support available"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1
    GPU_TYPE="NVIDIA"
else
    print_warning "⚠️  No GPU detected - using CPU mode"
    GPU_TYPE="CPU"
fi

# Set environment variables for optimal performance
export MONAI_DATA_DIRECTORY="$PROJECT_ROOT/data"
export MLFLOW_TRACKING_URI="file://$PROJECT_ROOT/mlruns"
export OVERLAY_ARTIFACT_DIR="$PROJECT_ROOT/artifacts"
mkdir -p "$PROJECT_ROOT/mlruns" "$PROJECT_ROOT/artifacts"

# Initialize MLflow if available
if python -c "import mlflow" 2>/dev/null; then
    print_feature "📊 MLflow experiment tracking available"
    print_status "MLflow UI: http://localhost:5001"
fi

# Start enhanced services
cd "$PROJECT_ROOT"

print_ai "🧠 Starting Enhanced Medical AI Backend..."

# Check for different backend options
BACKEND_STARTED=false

if [ -f "src/medical_imaging_api.py" ]; then
    print_feature "🚀 Starting FastAPI backend with advanced features..."

    # Start main API server
    python -m uvicorn src.medical_imaging_api:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 5

    if kill -0 $BACKEND_PID 2>/dev/null; then
        if curl -s -f http://localhost:8000 > /dev/null 2>&1 || curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
            print_success "✅ FastAPI backend running on http://localhost:8000"
            print_feature "📖 API Documentation: http://localhost:8000/docs"
            BACKEND_STARTED=true
        else
            print_warning "Backend process running but may still be starting up..."
        fi
    else
        print_error "Backend failed to start. Check the error messages above."
    fi
fi

# Start MLflow UI if available
if command -v mlflow &> /dev/null && [ "$BACKEND_STARTED" = true ]; then
    print_feature "📊 Starting MLflow experiment tracking UI..."
    mlflow ui --host 0.0.0.0 --port 5001 --backend-store-uri "$MLFLOW_TRACKING_URI" &
    MLFLOW_PID=$!
    sleep 3
    if kill -0 $MLFLOW_PID 2>/dev/null; then
        print_success "✅ MLflow UI started on http://localhost:5001"
    fi
fi

# Check for MONAI Label setup
MONAI_LABEL_DIR="$PROJECT_ROOT/monai_label_app"
if [ -d "$MONAI_LABEL_DIR" ]; then
    print_feature "🏷️  MONAI Label server available"
    print_status "To start: ./scripts/utilities/run_monai_label.sh"
else
    print_warning "MONAI Label not set up. Run: ./scripts/setup/setup_monai_label.sh"
fi

# Start enhanced frontend
print_feature "🎨 Starting Enhanced Medical Imaging GUI..."

FRONTEND_STARTED=false

if [ -d "gui/frontend" ]; then
    print_status "Starting React frontend with enhanced features..."
    cd "$PROJECT_ROOT/gui/frontend"

    # Check and install dependencies
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/react-scripts" ]; then
            print_status "Installing frontend dependencies..."
            npm install --legacy-peer-deps
            if [ $? -ne 0 ]; then
                print_warning "npm install failed, trying with --force..."
                npm install --force
            fi
        fi

        if [ -f "node_modules/.bin/react-scripts" ]; then
            print_status "Starting enhanced React development server..."
            npm start &
            FRONTEND_PID=$!
            print_success "✅ Enhanced frontend starting on http://localhost:3000"
            FRONTEND_STARTED=true
        else
            print_warning "React scripts not found, frontend may not start properly"
        fi
    fi
elif [ -d "frontend" ]; then
    cd "$PROJECT_ROOT/frontend"
    # Similar frontend startup logic
fi

# Wait for services to initialize
sleep 5

# Display comprehensive system status
echo ""
print_success "🚀 Enhanced Medical Imaging AI System Started!"
echo ""
print_ai "═══════════════════════════════════════════════"
print_ai "           🏥 SYSTEM OVERVIEW 🏥"
print_ai "═══════════════════════════════════════════════"
echo ""

print_feature "🌐 Web Services:"
echo "   • Main API Backend: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Interactive Swagger: http://localhost:8000/redoc"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "   • Enhanced GUI: http://localhost:3000"
fi
if [ ! -z "$MLFLOW_PID" ]; then
    echo "   • MLflow Tracking: http://localhost:5001"
fi
echo ""

print_ai "🧠 AI/ML Features:"
echo "   • Multi-modal MRI processing (T1, T1c, T2, FLAIR)"
echo "   • Advanced UNETR/UNet architectures"
echo "   • Cross-attention fusion"
echo "   • Detection + Segmentation cascade"
echo "   • Uncertainty estimation"
echo "   • MLflow experiment tracking"
if [ -d "$MONAI_LABEL_DIR" ]; then
    echo "   • MONAI Label interactive annotation"
fi
echo ""

print_feature "⚡ Hardware:"
echo "   • GPU Type: $GPU_TYPE"
if [ "$GPU_TYPE" != "CPU" ]; then
    echo "   • AI Acceleration: Enabled"
else
    echo "   • AI Acceleration: CPU-only mode"
fi
echo ""

print_ai "📊 Data & Experiments:"
echo "   • Data Directory: $MONAI_DATA_DIRECTORY"
echo "   • MLflow Tracking: $MLFLOW_TRACKING_URI"
echo "   • Artifacts: $OVERLAY_ARTIFACT_DIR"
echo "   • Supported Formats: DICOM, NIfTI, NRRD"
echo ""

print_feature "🛠️  Advanced Features:"
echo "   • Modality-specific normalization"
echo "   • Curriculum augmentation"
echo "   • Test-time augmentation (TTA)"
echo "   • Sliding window inference"
echo "   • Real-time segmentation overlays"
if [ "$FRONTEND_STARTED" = true ]; then
    echo "   • Interactive 3D visualization"
    echo "   • DICOM viewer with MPR"
    echo "   • Clinical report generation"
fi
echo ""

print_status "🔧 Quick Commands:"
echo "   • Train model: python src/training/train.py --config config/recipes/unetr_multimodal.json"
echo "   • Run inference: python src/inference/inference.py --input <path>"
echo "   • Start MONAI Label: ./scripts/utilities/run_monai_label.sh"
echo "   • View experiments: mlflow ui --port 5001"
echo ""

if [ "$FRONTEND_STARTED" = false ]; then
    print_warning "Frontend not started due to dependency issues"
    print_status "To fix frontend: ./scripts/setup/fix_frontend.sh"
fi

print_status "� Documentation:"
echo "   • User Guide: docs/user-guide/"
echo "   • Developer Guide: docs/developer/"
echo "   • API Reference: docs/api/"
echo ""

print_ai "🎯 Ready for:"
echo "   ✓ Brain tumor segmentation"
echo "   ✓ Multi-modal MRI analysis"
echo "   ✓ Interactive annotation"
echo "   ✓ Experiment tracking"
echo "   ✓ Clinical report generation"
echo "   ✓ Research & development"
echo ""

print_success "🏥 System ready for medical imaging AI tasks!"
print_status "To stop all services, press Ctrl+C"

# Create enhanced cleanup function
cleanup() {
    echo ""
    print_status "🛑 Shutting down Enhanced Medical AI System..."

    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping API backend..."
        kill $BACKEND_PID 2>/dev/null
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend..."
        kill $FRONTEND_PID 2>/dev/null
    fi

    if [ ! -z "$MLFLOW_PID" ]; then
        print_status "Stopping MLflow UI..."
        kill $MLFLOW_PID 2>/dev/null
    fi

    # Kill any remaining processes
    pkill -f "uvicorn.*medical_imaging_api" 2>/dev/null
    pkill -f "mlflow.*ui" 2>/dev/null

    print_success "✅ All services stopped"
    print_ai "Thank you for using Enhanced Medical Imaging AI! 🏥"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running and monitor services
while true; do
    sleep 10

    # Check if critical services are still running
    if [ ! -z "$BACKEND_PID" ] && ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend service stopped unexpectedly"
        break
    fi

    # Optional: Add health checks here
done
