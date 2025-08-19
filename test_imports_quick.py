#!/usr/bin/env python3
"""Quick verification script for MONAI integration components."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test basic imports for MONAI integration."""
    print("🔍 Testing MONAI Integration Imports")
    print("=" * 40)

    # Test 1: MONAI loader import
    try:
        from src.data.loaders_monai import load_monai_decathlon
        print("✅ MONAI loader import: OK")
    except ImportError as e:
        print(f"❌ MONAI loader import failed: {e}")
        return False

    # Test 2: Transform presets import
    try:
        from src.data.transforms_presets import get_transforms_brats_like
        print("✅ Transform presets import: OK")
    except ImportError as e:
        print(f"❌ Transform presets import failed: {e}")
        return False

    # Test 3: MONAI dependencies
    try:
        from monai.apps import DecathlonDataset
        from monai.data import DataLoader, Dataset
        print("✅ MONAI dependencies: OK")
    except ImportError as e:
        print(f"❌ MONAI dependencies failed: {e}")
        return False

    print("\n🎉 All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
