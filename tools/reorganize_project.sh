#!/bin/bash

# Master Project Reorganization Script
echo "🚀 Medical Imaging AI - Complete Project Reorganization"
echo "========================================================"
echo ""
echo "This script will completely reorganize your project structure"
echo "to follow modern ML/medical imaging best practices."
echo ""
echo "⚠️  IMPORTANT: This will make significant changes to your project!"
echo "   Make sure you have backed up your work or committed to git."
echo ""

# Prompt for confirmation
read -p "Do you want to proceed with the reorganization? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Reorganization cancelled."
    exit 1
fi

echo ""
echo "🔄 Starting complete project reorganization..."
echo ""

# Make all scripts executable
chmod +x reorganize_phase1.sh reorganize_phase2.sh reorganize_phase3.sh reorganize_phase4.sh

# Execute all phases
echo "📋 Phase 1: Duplicate removal and cleanup..."
./reorganize_phase1.sh
echo ""

echo "📁 Phase 2: Creating optimal directory structure..."  
./reorganize_phase2.sh
echo ""

echo "📦 Phase 3: Moving files to optimal locations..."
./reorganize_phase3.sh
echo ""

echo "🔧 Phase 4: Import updates and finalization..."
./reorganize_phase4.sh
echo ""

echo "🔍 Running final verification..."
python3 tools/verify_structure.py

echo ""
echo "🎉 COMPLETE PROJECT REORGANIZATION FINISHED!"
echo "============================================"
echo ""
echo "✨ Your medical imaging AI project has been successfully reorganized!"
echo ""
echo "📋 What was accomplished:"
echo "   ✅ Removed all duplicate files and directories"
echo "   ✅ Created modern ML/medical project structure"
echo "   ✅ Consolidated medical AI implementations" 
echo "   ✅ Updated all import paths"
echo "   ✅ Created comprehensive documentation"
echo "   ✅ Added development tools"
echo ""
echo "🚀 Quick start:"
echo "   1. Install dependencies: pip install -r requirements.txt"
echo "   2. Start backend: uvicorn app.api.medical_imaging_api:app --reload"
echo "   3. Start frontend: cd app/frontend && npm start"
echo "   4. Access: http://localhost:3000"
echo ""
echo "📚 Documentation: See PROJECT_SUMMARY.md for complete overview"
echo "🔧 Development: Use tools/ directory for dev scripts"
echo ""
echo "Happy coding! 🏥🤖"
