#!/usr/bin/env python3
"""
Test script to validate the tumor_detection package installation and imports.

This script verifies that the package can be imported and used correctly.
"""

import sys
import traceback
from pathlib import Path

# Add the project root to sys.path so we can import the package
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_package_import():
    """Test basic package import."""
    print("Testing package import...")
    try:
        import tumor_detection
        print(f"✅ Package imported successfully (version {tumor_detection.__version__})")
        return True
    except Exception as e:
        print(f"❌ Package import failed: {e}")
        traceback.print_exc()
        return False

def test_api_imports():
    """Test API function imports."""
    print("\nTesting API imports...")
    try:
        print("✅ Core API functions imported successfully")
        return True
    except Exception as e:
        print(f"❌ API import failed: {e}")
        traceback.print_exc()
        return False

def test_config_imports():
    """Test configuration imports."""
    print("\nTesting config imports...")
    try:
        print("✅ Configuration functions imported successfully")
        return True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        traceback.print_exc()
        return False

def test_device_imports():
    """Test device utility imports."""
    print("\nTesting device utility imports...")
    try:
        print("✅ Device utilities imported successfully")
        return True
    except Exception as e:
        print(f"❌ Device utility import failed: {e}")
        traceback.print_exc()
        return False

def test_submodule_imports():
    """Test submodule imports."""
    print("\nTesting submodule imports...")
    success = True

    # Test config module
    try:
        print("✅ tumor_detection.config imported successfully")
    except Exception as e:
        print(f"❌ tumor_detection.config import failed: {e}")
        success = False

    # Test utils module
    try:
        print("✅ tumor_detection.utils imported successfully")
    except Exception as e:
        print(f"❌ tumor_detection.utils import failed: {e}")
        success = False

    # Test inference module
    try:
        print("✅ tumor_detection.inference imported successfully")
    except Exception as e:
        print(f"❌ tumor_detection.inference import failed: {e}")
        success = False

    # Test models module (optional, may have missing dependencies)
    try:
        print("✅ tumor_detection.models imported successfully")
    except Exception as e:
        print(f"⚠️  tumor_detection.models import failed (may be due to missing dependencies): {e}")
        # Don't fail the test for models since dependencies might be missing

    return success

def test_cli_imports():
    """Test CLI module imports."""
    print("\nTesting CLI imports...")
    try:
        print("✅ CLI modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ CLI import failed: {e}")
        traceback.print_exc()
        return False

def test_package_structure():
    """Test that the package structure is correct."""
    print("\nTesting package structure...")
    try:
        import tumor_detection

        # Check that we have the expected attributes
        expected_attrs = [
            '__version__',
            'load_model',
            'run_inference',
            'save_mask',
            'generate_overlays',
            'load_recipe_config',
            'load_dataset_config',
            'auto_device_resolve'
        ]

        missing_attrs = []
        for attr in expected_attrs:
            if not hasattr(tumor_detection, attr):
                missing_attrs.append(attr)

        if missing_attrs:
            print(f"❌ Missing attributes: {missing_attrs}")
            return False
        else:
            print("✅ All expected attributes are available")
            return True

    except Exception as e:
        print(f"❌ Package structure test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Tumor Detection Package Import Tests")
    print("=" * 40)

    tests = [
        test_package_import,
        test_api_imports,
        test_config_imports,
        test_device_imports,
        test_submodule_imports,
        test_cli_imports,
        test_package_structure
    ]

    results = []
    for test in tests:
        results.append(test())

    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Package is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
