#!/bin/bash

# Project Reorganization - Phase 1: Remove Duplicates
echo "🔄 Starting Project Reorganization - Phase 1"
echo "============================================="

# Remove the duplicate nested directory
if [ -d "tumor-detection-segmentation" ]; then
    echo "🗑️  Removing duplicate nested directory..."
    rm -rf tumor-detection-segmentation/
    echo "   ✅ Duplicate directory removed"
else
    echo "   ℹ️  No duplicate directory found"
fi

# Remove duplicate GUI directory if it exists
if [ -d "gui" ]; then
    echo "🗑️  Checking GUI directory for duplicates..."
    # Check if content is duplicate of frontend
    if [ -d "frontend" ] && [ -d "gui/frontend" ]; then
        echo "   🗑️  Removing duplicate GUI frontend..."
        rm -rf gui/
        echo "   ✅ Duplicate GUI directory removed"
    fi
fi

echo ""
echo "✅ Phase 1 Complete: Duplicate removal finished"
