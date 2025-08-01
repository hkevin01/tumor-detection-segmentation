#!/bin/bash

# Tumor Detection GUI Demonstration Script
echo "==========================================="
echo "Tumor Detection GUI Application"
echo "==========================================="
echo ""

# Check if we're in the correct directory
if [ ! -f "gui/frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: A directory containing 'gui/frontend/package.json'"
    exit 1
fi

# Navigate to frontend directory
cd gui/frontend

echo "📦 Installing dependencies..."
echo "This may take a few minutes on first run..."
echo ""

# Install dependencies
npm install --silent

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Try running manually: cd gui/frontend && npm install"
    exit 1
fi

echo "✅ Dependencies installed successfully!"
echo ""

echo "🚀 Starting the GUI application..."
echo ""
echo "The application will open automatically in your browser."
echo "If it doesn't open automatically, visit: http://localhost:3000"
echo ""
echo "Available pages:"
echo "  📊 Dashboard        - http://localhost:3000/"
echo "  👥 Patients         - http://localhost:3000/patients"
echo "  🔬 Studies          - http://localhost:3000/studies"
echo "  📋 Reports          - http://localhost:3000/reports"
echo "  🤖 AI Models        - http://localhost:3000/models"
echo "  📁 File Management  - http://localhost:3000/files"
echo "  ⚙️  Settings         - http://localhost:3000/settings"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==========================================="
echo ""

# Start the development server
npm start
