#!/bin/bash

# Simple GUI Runner
echo "🖥️  Medical Imaging GUI Runner"
echo "=============================="

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

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Activate virtual environment if available
if [ -d ".venv" ]; then
    print_status "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    print_status "Activating virtual environment (venv)..."
    source venv/bin/activate
else
    print_warning "No virtual environment found. Using system Python."
fi

# Try to run different GUI applications in order of preference
print_status "Looking for GUI applications..."

# 1. Try FastAPI backend with docs
if [ -f "src/medical_imaging_api.py" ]; then
    print_success "Found FastAPI medical imaging API"
    print_status "Starting API server with interactive documentation..."
    echo ""
    echo "📱 The GUI will be available at:"
    echo "   • API: http://localhost:8000"
    echo "   • Interactive Docs: http://localhost:8000/docs"
    echo "   • Alternative Docs: http://localhost:8000/redoc"
    echo ""
    python -m uvicorn src.medical_imaging_api:app --host 0.0.0.0 --port 8000 --reload
    
elif [ -f "src/medical_ai_backend.py" ]; then
    print_success "Found medical AI backend"
    print_status "Starting backend server..."
    python src/medical_ai_backend.py
    
elif [ -f "src/medical_imaging_ai.py" ]; then
    print_success "Found medical imaging AI application"
    print_status "Starting medical imaging application..."
    python src/medical_imaging_ai.py
    
# 2. Try Python GUI scripts
elif [ -f "scripts/utilities/start_gui.py" ]; then
    print_success "Found start_gui.py"
    python scripts/utilities/start_gui.py
    
elif [ -f "scripts/utilities/start_complete_gui.py" ]; then
    print_success "Found start_complete_gui.py"
    python scripts/utilities/start_complete_gui.py

# 3. Try to run a basic MONAI demo
else
    print_warning "No specific GUI found. Starting basic medical imaging demo..."
    
    # Create a simple demo if no GUI exists
    cat > temp_gui_demo.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Medical Imaging Demo
"""
import sys
import os
sys.path.append('src')

def main():
    print("🏥 Medical Imaging AI Demo")
    print("=" * 30)
    
    try:
        import torch
        import monai
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ MONAI: {monai.__version__}")
        
        if torch.cuda.is_available():
            print(f"🚀 GPU available: {torch.cuda.device_count()} devices")
        else:
            print("💻 Running on CPU")
            
        print("\n📋 Available modules:")
        
        # Check available source modules
        src_files = []
        if os.path.exists('src'):
            for file in os.listdir('src'):
                if file.endswith('.py') and not file.startswith('__'):
                    module_name = file[:-3]
                    src_files.append(module_name)
                    
        if src_files:
            for module in sorted(src_files):
                print(f"   • {module}")
        else:
            print("   • No source modules found")
            
        print("\n🌐 To start the full system:")
        print("   ./scripts/utilities/start_medical_gui.sh")
        print("\n📚 For API documentation:")
        print("   Start the API server and visit http://localhost:8000/docs")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n🔧 Run setup first:")
        print("   ./scripts/setup/quick_setup.sh")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

    python temp_gui_demo.py
    rm -f temp_gui_demo.py
fi
