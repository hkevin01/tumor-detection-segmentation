#!/usr/bin/env python3
"""
Test Validation Script

This script validates the test structure and organization after reorganization.
It checks for proper Python package structure and basic import functionality.
"""

import os
import sys
from pathlib import Path


def check_package_structure():
    """Check that all test directories have proper __init__.py files."""
    test_dirs = [
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/validation',
        'tests/frameworks',
        'tests/inference',
        'tests/visualization',
        'tests/utilities',
        'tests/docker',
        'tests/data',
        'tests/performance',
        'tests/gui'
    ]

    missing_init = []
    for test_dir in test_dirs:
        init_file = Path(test_dir) / '__init__.py'
        if not init_file.exists():
            missing_init.append(test_dir)

    if missing_init:
        print(f"❌ Missing __init__.py files in: {missing_init}")
        return False
    else:
        print("✅ All test directories have __init__.py files")
        return True


def check_test_files():
    """Check that test files exist and are properly named."""
    test_files = []
    for root, _, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))

    if not test_files:
        print("❌ No test files found")
        return False

    print(f"✅ Found {len(test_files)} test files:")
    for test_file in sorted(test_files)[:10]:  # Show first 10
        print(f"  - {test_file}")
    if len(test_files) > 10:
        print(f"  ... and {len(test_files) - 10} more")

    return True


def check_imports():
    """Check basic import functionality."""
    try:
        # Try to import pytest if available
        import importlib.util
        if importlib.util.find_spec('pytest'):
            print("✅ pytest is available")
        else:
            print("⚠️  pytest not available - install with: pip install pytest")
    except Exception:
        print("⚠️  pytest not available - install with: pip install pytest")

    # Check if we can import the test package
    try:
        import importlib.util
        if importlib.util.find_spec('tests'):
            print("✅ tests package can be imported")
            return True
        else:
            print("❌ Cannot import tests package")
            return False
    except Exception as e:
        print(f"❌ Cannot import tests package: {e}")
        return False


def check_script_structure():
    """Check that scripts are properly organized."""
    script_dirs = [
        'scripts/cleanup',
        'scripts/utilities',
        'scripts/demo',
        'scripts/docker',
        'scripts/setup'
    ]

    missing_dirs = []
    for script_dir in script_dirs:
        if not Path(script_dir).exists():
            missing_dirs.append(script_dir)

    if missing_dirs:
        print(f"❌ Missing script directories: {missing_dirs}")
        return False
    else:
        print("✅ All script directories exist")
        return True


def check_docs_structure():
    """Check that documentation is properly organized."""
    doc_dirs = [
        'docs/setup',
        'docs/status',
        'docs/project'
    ]

    missing_dirs = []
    for doc_dir in doc_dirs:
        if not Path(doc_dir).exists():
            missing_dirs.append(doc_dir)

    if missing_dirs:
        print(f"❌ Missing documentation directories: {missing_dirs}")
        return False
    else:
        print("✅ All documentation directories exist")
        return True


def main():
    """Run all validation checks."""
    print("🔍 Test Structure Validation")
    print("=" * 50)

    checks = [
        ("Package Structure", check_package_structure),
        ("Test Files", check_test_files),
        ("Imports", check_imports),
        ("Script Structure", check_script_structure),
        ("Documentation Structure", check_docs_structure)
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during {name} check: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 Validation Summary:")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("🎉 Test structure validation successful!")
        return 0
    else:
        print(f"⚠️  Some checks failed ({passed}/{total})")
        print("🔧 Review the failed checks above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
