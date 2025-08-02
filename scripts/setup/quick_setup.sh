#!/bin/bash

# Quick Setup Script for Medical Imaging AI
echo "⚡ Quick Setup - Medical Imaging AI"
echo "=================================="

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

cd "$PROJECT_ROOT"

print_status "Setting up Medical Imaging AI project in: $PROJECT_ROOT"

# 1. Check Python version
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found! Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_success "Python $PYTHON_VERSION detected"

# 2. Create virtual environment if it doesn't exist
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# 3. Activate virtual environment
print_status "Activating virtual environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    source venv/bin/activate
fi

# 4. Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# 5. Install dependencies
print_status "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed from requirements.txt"
else
    print_warning "requirements.txt not found, installing basic dependencies..."
    pip install torch torchvision monai fastapi uvicorn numpy pandas matplotlib pillow
fi

# 6. Check GPU support
print_status "Checking GPU support..."
if command -v rocm-smi &> /dev/null; then
    print_success "ROCm detected - AMD GPU support available"
    print_status "Installing ROCm PyTorch..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.6
elif nvidia-smi &> /dev/null 2>&1; then
    print_success "NVIDIA GPU detected"
    print_status "Installing CUDA PyTorch..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
else
    print_warning "No GPU detected - CPU-only mode"
fi

# 7. Setup frontend if available
if [ -d "gui/frontend" ] || [ -d "frontend" ]; then
    print_status "Setting up frontend..."
    
    # Find frontend directory
    FRONTEND_DIR=""
    if [ -d "gui/frontend" ]; then
        FRONTEND_DIR="gui/frontend"
    elif [ -d "frontend" ]; then
        FRONTEND_DIR="frontend"
    fi
    
    if [ ! -z "$FRONTEND_DIR" ]; then
        cd "$FRONTEND_DIR"
        if [ -f "package.json" ]; then
            if command -v npm &> /dev/null; then
                print_status "Installing frontend dependencies..."
                npm install
                print_success "Frontend dependencies installed"
            else
                print_warning "npm not found - frontend setup skipped"
            fi
        fi
        cd "$PROJECT_ROOT"
    fi
fi

# 8. Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/{raw,processed,models}
mkdir -p models/checkpoints
mkdir -p logs
mkdir -p temp
print_success "Directory structure created"

# 9. Set up basic configuration
if [ ! -f "config.json" ]; then
    print_status "Creating basic configuration..."
    cat > config.json << 'EOF'
{
  "model": {
    "name": "tumor_detection",
    "input_size": [512, 512],
    "num_classes": 2,
    "device": "auto"
  },
  "training": {
    "batch_size": 4,
    "learning_rate": 0.001,
    "num_epochs": 100,
    "validation_split": 0.2
  },
  "data": {
    "raw_path": "data/raw",
    "processed_path": "data/processed",
    "model_path": "models"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
EOF
    print_success "Basic configuration created"
fi

# 10. Test installation
print_status "Testing installation..."
python -c "
import torch
import monai
print(f'PyTorch: {torch.__version__}')
print(f'MONAI: {monai.__version__}')
if torch.cuda.is_available():
    print(f'CUDA available: {torch.cuda.device_count()} devices')
else:
    print('CUDA not available - using CPU')
" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "Installation test passed!"
else
    print_warning "Some dependencies may have issues, but continuing..."
fi

echo ""
print_success "🎉 Quick Setup Complete!"
echo ""
print_status "Next steps:"
echo "   1. Start the system: ./scripts/utilities/start_medical_gui.sh"
echo "   2. Run tests: pytest tests/"
echo "   3. Check git status: ./scripts/utilities/git_status.sh"
echo "   4. View documentation: docs/"
echo ""
print_status "API will be available at: http://localhost:8000"
print_status "Documentation at: http://localhost:8000/docs"
echo ""
print_success "Happy coding! 🚀"
