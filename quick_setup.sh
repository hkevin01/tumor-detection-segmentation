#!/bin/bash

# Quick Setup Script for Medical Imaging GUI
# This script prepares the system for the first run

echo "🏥 Medical Imaging AI - Quick Setup"
echo "=================================="

# Make the main startup script executable
chmod +x start_medical_gui.sh

# Create essential directories
mkdir -p data/{raw,processed,models,exports}
mkdir -p logs
mkdir -p temp
mkdir -p frontend/src/components

# Set up git hooks (if in a git repository)
if [ -d ".git" ]; then
    echo "Setting up git hooks..."
    # Add any git hooks here
fi

echo "✅ Quick setup completed!"
echo ""
echo "Next steps:"
echo "1. Run: ./start_medical_gui.sh"
echo "2. Open: http://localhost:3000"
echo "3. Upload DICOM files and start analyzing!"
echo ""
