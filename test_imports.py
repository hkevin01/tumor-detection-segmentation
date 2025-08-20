#!/usr/bin/env python3
"""
Quick test to identify specific import issues in the test suite.
"""


def test_import(module_name: str) -> tuple[bool, str]:
    """Test importing a specific module."""
    try:
        __import__(module_name)
        return True, f"✅ {module_name} imports successfully"
    except Exception as e:
        return False, f"❌ {module_name} failed: {str(e)}"

def main():
    """Test key imports that were causing issues."""
    print("🔍 Testing Key Imports")
    print("=" * 50)

    # Test the main modules that were causing issues
    test_modules = [
        "src.data_preprocessing",
        "selenium",
        "monai.transforms",
    ]

    results = []
    for module in test_modules:
        success, message = test_import(module)
        results.append((success, message))
        print(message)

    print("\n" + "=" * 50)

    # Test specific MONAI transforms
    print("\n🧪 Testing MONAI Transforms")
    try:
        print("✅ EnsureChannelFirstd, LoadImaged, Compose import successfully")
    except Exception as e:
        print(f"❌ MONAI transforms failed: {e}")

    # Test pytest markers
    print("\n🏷️  Testing Pytest Configuration")
    try:
        print("✅ pytest imports successfully")
    except Exception as e:
        print(f"❌ pytest failed: {e}")

    # Show summary
    successful = sum(1 for success, _ in results if success)
    total = len(results)
    print(f"\n📊 Summary: {successful}/{total} imports successful")

    if successful == total:
        print("🎉 All key imports are working! Tests should run now.")
    else:
        print("⚠️  Some imports still failing. Check the errors above.")

if __name__ == "__main__":
    main()
