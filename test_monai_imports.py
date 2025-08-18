#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple import test to verify MONAI test dependencies work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_basic_imports():
    """Test that basic imports work for the test files."""
    print("Testing basic imports for MONAI test suite...")
    
    try:
        import numpy as np
        print("✅ NumPy import successful")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import nibabel as nib
        print("✅ NiBabel import successful")
    except ImportError as e:
        print(f"❌ NiBabel import failed: {e}")
        return False
        
    try:
        import torch
        print(f"✅ PyTorch import successful (version: {torch.__version__})")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        from pathlib import Path
        print("✅ Pathlib import successful")
    except ImportError as e:
        print(f"❌ Pathlib import failed: {e}")
        return False
    
    # Test MONAI components needed for tests
    try:
        from monai.networks.nets import UNet
        print("✅ MONAI UNet import successful")
    except ImportError as e:
        print(f"❌ MONAI UNet import failed: {e}")
        return False
    
    # Test our custom modules
    try:
        from src.data.loaders_monai import load_monai_decathlon
        print("✅ MONAI loader import successful")
    except ImportError as e:
        print(f"❌ MONAI loader import failed: {e}")
        return False
        
    try:
        from src.data.transforms_presets import get_transforms_brats_like, get_transforms_ct_liver
        print("✅ Transform presets import successful")
    except ImportError as e:
        print(f"❌ Transform presets import failed: {e}")
        return False
    
    print("\n🎉 All critical imports for MONAI tests are working!")
    return True

def test_synthetic_data_creation():
    """Test creating a simple synthetic NIfTI file."""
    print("\nTesting synthetic data creation...")
    
    try:
        import tempfile
        import numpy as np
        import nibabel as nib
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a small synthetic volume
            data = np.random.randn(16, 16, 16).astype(np.float32)
            affine = np.eye(4, dtype=np.float32)
            img = nib.Nifti1Image(data, affine)
            
            # Save and reload
            test_path = Path(tmp_dir) / "test.nii.gz"
            nib.save(img, str(test_path))
            
            # Verify we can load it back
            loaded_img = nib.load(str(test_path))
            loaded_data = loaded_img.get_fdata()
            
            assert loaded_data.shape == (16, 16, 16)
            print("✅ Synthetic NIfTI creation and loading successful")
            return True
            
    except Exception as e:
        print(f"❌ Synthetic data creation failed: {e}")
        return False

def main():
    """Run all import tests."""
    print("🧪 MONAI Test Environment Validation")
    print("=" * 40)
    
    imports_ok = test_basic_imports()
    data_ok = test_synthetic_data_creation()
    
    print("\n" + "=" * 40)
    if imports_ok and data_ok:
        print("✅ All tests passed! MONAI test environment is ready.")
        print("\nYou can now run:")
        print("  pytest tests/unit/test_transforms_presets.py")
        print("  pytest tests/integration/test_monai_msd_loader.py")
        print("  python scripts/demo/test_monai_integration.py")
        return 0
    else:
        print("❌ Some tests failed. Please check dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
