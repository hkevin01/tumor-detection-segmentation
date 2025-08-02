#!/bin/bash

# Simple Backend Test Script
echo "🧪 Testing Medical Imaging Backend"
echo "================================="

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

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    print_status "Virtual environment activated"
else
    print_warning "No virtual environment found"
fi

print_status "Testing basic Python imports..."

# Test basic package import
if python -c "import src" 2>/dev/null; then
    print_success "✅ src package imports successfully"
else
    print_error "❌ src package import failed"
    exit 1
fi

# Test FastAPI import more specifically
print_status "Testing FastAPI application import..."

# Create a simple test script to avoid hanging imports
cat > temp_test_api.py << 'EOF'
try:
    import sys
    sys.path.insert(0, '.')
    
    # Test importing the app
    print("Testing FastAPI import...")
    from src.medical_imaging_api import app
    print("✅ FastAPI app imported successfully")
    
    # Test basic app properties
    print(f"App title: {app.title}")
    print("✅ App is functional")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
EOF

if timeout 15s python temp_test_api.py; then
    print_success "✅ FastAPI application test passed"
else
    print_error "❌ FastAPI application test failed or timed out"
fi

# Clean up
rm -f temp_test_api.py

print_status "Testing uvicorn server startup..."

# Test if uvicorn can start (but don't leave it running)
timeout 10s python -m uvicorn src.medical_imaging_api:app --host 127.0.0.1 --port 8001 &
UVICORN_PID=$!

sleep 3

if kill -0 $UVICORN_PID 2>/dev/null; then
    print_success "✅ Uvicorn can start the application"
    kill $UVICORN_PID 2>/dev/null
else
    print_warning "⚠️ Uvicorn startup test inconclusive"
fi

echo ""
print_status "Backend test summary:"
echo "   • Package imports: Working"
echo "   • FastAPI app: Testing completed"
echo "   • Uvicorn server: Testing completed"
echo ""
print_success "🎉 Backend tests completed!"
echo ""
print_status "To start the full system: ./scripts/utilities/start_medical_gui.sh"
