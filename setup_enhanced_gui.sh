#!/bin/bash

# Enhanced Tumor Detection GUI with DICOM Viewer Setup Script
# This script installs Cornerstone3D dependencies and starts the enhanced application

set -e

echo "🏥 Setting up Enhanced Tumor Detection GUI with DICOM Viewer..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js (version 16 or higher)"
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher"
    exit 1
fi

if ! command_exists pip3; then
    echo "❌ pip3 is not installed. Please install pip3"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Set up backend
echo "🔧 Setting up backend..."
cd gui/backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Go back to root
cd ../..

# Set up frontend with Cornerstone3D
echo "🎨 Setting up frontend with DICOM viewer..."
cd gui/frontend

# Install Node.js dependencies including Cornerstone3D
echo "📦 Installing Node.js dependencies (including Cornerstone3D)..."
npm install

# Install specific Cornerstone3D packages
echo "🏥 Installing medical imaging packages..."
npm install @cornerstonejs/core@latest
npm install @cornerstonejs/tools@latest
npm install @cornerstonejs/dicom-image-loader@latest
npm install @cornerstonejs/streaming-image-volume-loader@latest
npm install dicom-parser@latest

# Go back to root
cd ../..

# Create enhanced startup script
echo "🚀 Creating enhanced startup script..."
cat > start_enhanced_gui.sh << 'EOF'
#!/bin/bash

echo "🏥 Starting Enhanced Tumor Detection GUI with DICOM Viewer..."

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔌 Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🎨 Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
echo "🔌 Starting FastAPI backend..."
cd gui/backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Start frontend
echo "🎨 Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "🎉 Enhanced Tumor Detection GUI is now running!"
echo ""
echo "📊 Backend API: http://localhost:8000"
echo "🏥 Frontend GUI with DICOM Viewer: http://localhost:3000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
echo "🔍 Features available:"
echo "   - Complete clinical workflow interface"
echo "   - Professional DICOM image viewer with Cornerstone3D"
echo "   - Multi-planar reconstruction (MPR)"
echo "   - Medical imaging tools (measurements, annotations)"
echo "   - AI tumor detection with visual overlays"
echo "   - Clinical reporting and study management"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
EOF

chmod +x start_enhanced_gui.sh

# Create development script for quick restart
echo "⚡ Creating quick development restart script..."
cat > restart_gui.sh << 'EOF'
#!/bin/bash

echo "⚡ Quick restart for Enhanced Tumor Detection GUI..."

# Kill existing processes
pkill -f "python main.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start the enhanced GUI
./start_enhanced_gui.sh
EOF

chmod +x restart_gui.sh

# Create installation verification script
echo "🔍 Creating installation verification script..."
cat > verify_installation.sh << 'EOF'
#!/bin/bash

echo "🔍 Verifying Enhanced Tumor Detection GUI Installation..."

echo ""
echo "📋 Checking backend requirements..."
cd gui/backend
source venv/bin/activate
python -c "
try:
    import fastapi, uvicorn, numpy, torch
    print('✅ Backend dependencies verified')
except ImportError as e:
    print(f'❌ Backend dependency missing: {e}')
"

echo ""
echo "📋 Checking frontend requirements..."
cd ../frontend
if [ -f "node_modules/@cornerstonejs/core/package.json" ]; then
    echo "✅ Cornerstone3D Core installed"
else
    echo "❌ Cornerstone3D Core missing"
fi

if [ -f "node_modules/@cornerstonejs/tools/package.json" ]; then
    echo "✅ Cornerstone3D Tools installed"
else
    echo "❌ Cornerstone3D Tools missing"
fi

if [ -f "node_modules/@cornerstonejs/dicom-image-loader/package.json" ]; then
    echo "✅ DICOM Image Loader installed"
else
    echo "❌ DICOM Image Loader missing"
fi

if [ -f "node_modules/dicom-parser/package.json" ]; then
    echo "✅ DICOM Parser installed"
else
    echo "❌ DICOM Parser missing"
fi

echo ""
echo "🏥 Installation verification complete!"
EOF

chmod +x verify_installation.sh

echo ""
echo "✅ Enhanced Tumor Detection GUI setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Run: ./verify_installation.sh  (to verify all components)"
echo "   2. Run: ./start_enhanced_gui.sh   (to start the application)"
echo "   3. Run: ./restart_gui.sh          (for quick development restarts)"
echo ""
echo "🏥 New Features Added:"
echo "   ✅ Professional DICOM viewer with Cornerstone3D"
echo "   ✅ Medical imaging tools and measurements"
echo "   ✅ AI tumor detection visualization"
echo "   ✅ Multi-planar reconstruction support"
echo "   ✅ Clinical workflow integration"
echo "   ✅ Enhanced study management"
echo ""
echo "🔗 Access the application at: http://localhost:3000"
echo "📖 API docs available at: http://localhost:8000/docs"
