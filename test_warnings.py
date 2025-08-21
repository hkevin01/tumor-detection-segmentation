#!/usr/bin/env python3
"""
Test warning suppression for SWIG-related deprecation warnings.
"""

import sys
import warnings


def suppress_swig_warnings():
    """Suppress SWIG-related deprecation warnings."""
    # Suppress the specific SWIG warnings
    warnings.filterwarnings("ignore", message=".*has no __module__ attribute.*")
    warnings.filterwarnings("ignore", message=".*builtin type SwigPyPacked.*")
    warnings.filterwarnings("ignore", message=".*builtin type SwigPyObject.*")
    warnings.filterwarnings("ignore", message=".*builtin type swigvarlink.*")

    # Suppress general deprecation warnings from SWIG
    warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*importlib.*")

    print("✅ SWIG warning suppression configured")

def test_warnings():
    """Test if warnings are properly suppressed."""
    print("🧪 Testing warning suppression...")

    # Enable warning suppression
    suppress_swig_warnings()

    # Try to trigger similar warnings (simulated)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")  # Capture all warnings

        # Simulate the warning
        import warnings
        warnings.warn("builtin type SwigPyPacked has no __module__ attribute", DeprecationWarning)

        print(f"📊 Captured warnings: {len(w)}")
        for warning in w:
            print(f"  ⚠️  {warning.message}")

    print("✅ Warning test completed")

def main():
    """Main function to test and configure warning suppression."""
    print("🔧 SWIG Warning Suppression Test")
    print("=" * 50)

    print(f"Python version: {sys.version}")
    print(f"Warnings enabled: {not sys.warnoptions}")

    # Configure warnings
    suppress_swig_warnings()

    # Test warnings
    test_warnings()

    print("\n💡 To use this in your tests, add this to your conftest.py:")
    print("""
import warnings

# Add this at the top of conftest.py
warnings.filterwarnings("ignore", message=".*has no __module__ attribute.*")
warnings.filterwarnings("ignore", message=".*builtin type SwigPyPacked.*")
warnings.filterwarnings("ignore", message=".*builtin type SwigPyObject.*")
warnings.filterwarnings("ignore", message=".*builtin type swigvarlink.*")
""")

if __name__ == "__main__":
    main()
    main()
