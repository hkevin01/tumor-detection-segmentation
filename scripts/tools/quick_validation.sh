#!/bin/bash
#
# Quick Validation Script for Immediate Next Steps
# Based on the deep search synthesis recommendations
#

set -e

PROJECT_ROOT="/home/kevin/Projects/tumor-detection-segmentation"
cd "$PROJECT_ROOT"

echo "🚀 TUMOR DETECTION PROJECT - IMMEDIATE VALIDATION"
echo "=================================================="

# Task 1: Docker Stack Validation
echo ""
echo "📦 TASK 1: Docker Stack Check"
echo "------------------------------"

if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker available: $(docker --version)"
else
    echo "❌ Docker not found"
    exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
    echo "✅ Docker Compose available: $(docker-compose --version)"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

# Check if we can build the test image
echo "🏗️ Testing Docker build capability..."
if docker build -f docker/Dockerfile.test-lite -t tumor-test-lite . >/dev/null 2>&1; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed"
    echo "   This may be due to missing dependencies or Docker permissions"
fi

# Task 2: Virtual Environment Check
echo ""
echo "🐍 TASK 2: Python Environment"
echo "------------------------------"

if [ -d ".venv" ]; then
    echo "✅ Virtual environment found"

    # Check if we can activate and import key packages
    if source .venv/bin/activate && python -c "import torch, monai; print('PyTorch:', torch.__version__); print('MONAI:', monai.__version__)" 2>/dev/null; then
        echo "✅ Key ML packages available"
    else
        echo "⚠️ Some ML packages may be missing"
    fi
else
    echo "❌ Virtual environment not found at .venv"
    echo "   Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# Task 3: Check Configuration Files
echo ""
echo "⚙️ TASK 3: Configuration Check"
echo "------------------------------"

config_files=(
    "config/recipes/unetr_multimodal.json"
    "config/datasets/msd_task01_brain.json"
    "config/datasets/msd_task03_liver.json"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
    fi
done

# Task 4: Check Key Scripts
echo ""
echo "📜 TASK 4: Essential Scripts"
echo "----------------------------"

key_scripts=(
    "src/training/train_enhanced.py"
    "src/inference/inference.py"
    "scripts/data/pull_monai_dataset.py"
)

for script in "${key_scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "✅ Found: $script"
    else
        echo "❌ Missing: $script"
    fi
done

# Task 5: Data Directory Structure
echo ""
echo "📁 TASK 5: Data Structure"
echo "-------------------------"

# Create data directories if they don't exist
mkdir -p data/msd
mkdir -p logs/immediate_validation
mkdir -p reports/immediate_validation

echo "✅ Data directories prepared"

# Check if brain dataset already exists
if [ -d "data/msd/Task01_BrainTumour" ]; then
    echo "✅ Brain dataset (Task01) already downloaded"
    file_count=$(find data/msd/Task01_BrainTumour -name "*.nii.gz" | wc -l)
    echo "   Found $file_count NIfTI files"
else
    echo "⚠️ Brain dataset not found - will need to download"
fi

# Task 6: System Resources
echo ""
echo "💻 TASK 6: System Resources"
echo "---------------------------"

# Memory check
memory_gb=$(free -g | grep Mem | awk '{print $2}')
memory_avail_gb=$(free -g | grep Mem | awk '{print $7}')
echo "✅ Total memory: ${memory_gb}GB (${memory_avail_gb}GB available)"

# CPU check
cpu_count=$(nproc)
echo "✅ CPU cores: $cpu_count"

# Disk space check
disk_avail=$(df -h . | tail -1 | awk '{print $4}')
echo "✅ Available disk space: $disk_avail"

# GPU check
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "✅ NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1
else
    echo "⚠️ No NVIDIA GPU detected (CPU-only mode)"
fi

# Task 7: Quick Smoke Test
echo ""
echo "🧪 TASK 7: Quick Smoke Test"
echo "---------------------------"

if [ -d ".venv" ]; then
    echo "🔍 Testing basic imports..."

    if source .venv/bin/activate && python -c "
import sys
import torch
import monai
from pathlib import Path

print('✅ PyTorch import successful')
print('✅ MONAI import successful')
print('✅ Basic smoke test passed')
print()
print('Environment Info:')
print(f'  Python: {sys.version.split()[0]}')
print(f'  PyTorch: {torch.__version__}')
print(f'  MONAI: {monai.__version__}')
print(f'  CUDA available: {torch.cuda.is_available()}')
" 2>/dev/null; then
        echo "✅ Smoke test passed"
    else
        echo "❌ Smoke test failed - dependencies may be missing"
    fi
else
    echo "⚠️ Skipping smoke test - no virtual environment"
fi

# Summary and Next Steps
echo ""
echo "📋 VALIDATION SUMMARY"
echo "====================="
echo ""
echo "🎯 IMMEDIATE NEXT STEPS:"
echo ""
echo "1. Download dataset:"
echo "   source .venv/bin/activate"
echo "   python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour --root data/msd"
echo ""
echo "2. Run quick training test:"
echo "   python src/training/train_enhanced.py \\"
echo "     --config config/recipes/unetr_multimodal.json \\"
echo "     --dataset-config config/datasets/msd_task01_brain.json \\"
echo "     --epochs 2 --amp --save-overlays"
echo ""
echo "3. Test inference:"
echo "   python src/inference/inference.py \\"
echo "     --config config/recipes/unetr_multimodal.json \\"
echo "     --dataset-config config/datasets/msd_task01_brain.json \\"
echo "     --model path/to/trained/model.pt \\"
echo "     --save-overlays --save-prob-maps"
echo ""
echo "4. Start Docker services (optional):"
echo "   ./docker/docker-helper.sh up"
echo ""
echo "🚀 Ready to proceed with medical imaging pipeline validation!"
