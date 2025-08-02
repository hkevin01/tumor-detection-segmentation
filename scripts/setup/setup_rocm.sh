#!/bin/bash

# ROCm Setup Helper for Medical Imaging AI
echo "🚀 ROCm GPU Setup for Medical Imaging AI"
echo "========================================"

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

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "ROCm is only supported on Linux systems"
    exit 1
fi

# Check for AMD GPU
print_status "Checking for AMD GPU..."
if command -v lspci &> /dev/null; then
    AMD_GPU=$(lspci | grep -i "VGA.*AMD\|Display.*AMD" || true)
    if [ -n "$AMD_GPU" ]; then
        print_success "AMD GPU detected:"
        echo "$AMD_GPU"
    else
        print_warning "No AMD GPU detected. ROCm installation may not be necessary."
        echo "You can still proceed with CPU-only PyTorch installation."
    fi
else
    print_warning "Cannot detect GPU hardware (lspci not available)"
fi

echo ""
print_status "PyTorch Installation Options:"
echo ""

echo "1. 🔥 ROCm PyTorch (for AMD GPU):"
echo "   pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.7"
echo ""

echo "2. 💻 CPU-only PyTorch (recommended if no AMD GPU):"
echo "   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
echo ""

echo "3. 🧪 Current installation (check what you have):"
echo "   python -c \"import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('Device:', torch.device('cuda' if torch.cuda.is_available() else 'cpu'))\""
echo ""

# Interactive installation
read -p "Would you like to install ROCm PyTorch for AMD GPU support? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Installing PyTorch with ROCm support..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "Activated virtual environment"
    fi
    
    # Install ROCm PyTorch
    pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.7
    
    print_status "Testing ROCm PyTorch installation..."
    python3 -c "
import torch
print('✅ PyTorch version:', torch.__version__)
print('✅ CUDA available:', torch.cuda.is_available())
if hasattr(torch.version, 'hip') and torch.version.hip is not None:
    print('✅ ROCm/HIP version:', torch.version.hip)
    print('✅ ROCm available: True')
else:
    print('❌ ROCm/HIP: Not detected')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('✅ Default device:', device)

# Test basic tensor operations
try:
    x = torch.randn(3, 3)
    if torch.cuda.is_available():
        x = x.cuda()
        print('✅ GPU tensor test: Success')
    else:
        print('✅ CPU tensor test: Success')
except Exception as e:
    print('❌ Tensor test failed:', e)
"
    
    if [ $? -eq 0 ]; then
        print_success "ROCm PyTorch installation completed successfully!"
        
        # Update .env file for ROCm
        if [ -f ".env" ]; then
            sed -i 's/INFERENCE_DEVICE=.*/INFERENCE_DEVICE=auto/' .env
            print_status "Updated .env file for automatic device detection"
        fi
        
    else
        print_error "ROCm PyTorch installation failed. Falling back to CPU-only."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi
    
else
    print_status "Skipping ROCm installation. Using CPU-only PyTorch."
    read -p "Install CPU-only PyTorch? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
        print_success "CPU-only PyTorch installed"
    fi
fi

echo ""
print_status "Medical Imaging AI Device Configuration:"
echo "   • The system will automatically detect available devices"
echo "   • ROCm GPUs will be used if available and properly configured"
echo "   • CPU will be used as fallback for maximum compatibility"
echo "   • You can override device selection in config.json or .env"
echo ""
print_success "ROCm setup complete! You can now run the medical imaging system."
echo ""
echo "🚀 Next steps:"
echo "   1. Run: ./scripts/utilities/start_medical_gui.sh"
echo "   2. Check device detection in the startup output"
echo "   3. Monitor GPU usage: watch -n 1 rocm-smi (if ROCm tools installed)"
