#!/usr/bin/env bash
# MONAI Verification Script - Using Virtual Environment
# This script runs the verification checklist using the venv

echo "🧪 MONAI Integration Verification Checklist (Virtual Environment)"
echo "============================================================"

# Activate virtual environment
source venv/bin/activate

# Verify environment
echo "📍 Using Python: $(which python)"
echo "📍 Using Pip: $(which pip)"
echo

# Import tests
echo "============================================================"
echo "📦 PYTHON IMPORT SANITY CHECKS"
echo "============================================================"

echo "🔍 MONAI loader import..."
if python -c "from src.data.loaders_monai import load_monai_decathlon; print('✅ MONAI loader import - SUCCESS')"; then
    echo "✅ MONAI loader import - SUCCESS"
else
    echo "❌ MONAI loader import - FAILED"
fi

echo
echo "🔍 Transform presets import..."
if python -c "from src.data.transforms_presets import get_transforms_brats_like; print('✅ Transform presets import - SUCCESS')"; then
    echo "✅ Transform presets import - SUCCESS"
else
    echo "❌ Transform presets import - FAILED"
fi

echo
echo "============================================================"
echo "🧪 UNIT TESTS"
echo "============================================================"

echo "🔍 Unit tests - Transform presets..."
if python -m pytest -q tests/unit/test_transforms_presets.py; then
    echo "✅ Unit tests - Transform presets - SUCCESS"
else
    echo "❌ Unit tests - Transform presets - FAILED"
fi

echo
echo "============================================================"
echo "🔗 INTEGRATION TESTS (SYNTHETIC, CPU)"
echo "============================================================"

echo "🔍 Integration tests - MONAI MSD loader..."
if python -m pytest -q tests/integration/test_monai_msd_loader.py; then
    echo "✅ Integration tests - MONAI MSD loader - SUCCESS"
else
    echo "❌ Integration tests - MONAI MSD loader - FAILED"
fi

echo
echo "============================================================"
echo "📊 VERIFICATION COMPLETE"
echo "============================================================"
echo "All verification steps completed using virtual environment."
