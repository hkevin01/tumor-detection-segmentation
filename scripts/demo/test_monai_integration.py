#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script showing MONAI dataset integration tests execution.

This script demonstrates how to run the new MONAI dataset tests
and validates the complete integration workflow.
"""

import subprocess
import sys
from pathlib import Path


def run_test_command(test_path: str, description: str) -> bool:
    """Run a specific test and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: pytest -q {test_path}")
    print('='*60)
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q", test_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run MONAI dataset integration tests."""
    print("🧪 MONAI Dataset Integration Test Suite")
    print("=" * 60)
    print("Testing MONAI Decathlon loader, transforms, and training workflow")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")
    
    # Test cases to run
    test_cases = [
        ("tests/unit/test_transforms_presets.py",
         "Transform Presets Unit Tests"),
        ("tests/integration/test_monai_msd_loader.py",
         "MONAI MSD Loader Integration Tests"),
    ]

    results = []
    for test_path, description in test_cases:
        success = run_test_command(test_path, description)
        results.append((description, success))

    # Summary
    print("\n" + "="*60)
    print("🎯 Test Results Summary")
    print("="*60)

    all_passed = True
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} | {description}")
        if not success:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 All MONAI integration tests PASSED!")
        print("✨ Your MONAI dataset system is ready to use!")
        print("\nNext steps:")
        print("1. Download a dataset:")
        print("   python scripts/data/pull_monai_dataset.py "
              "--dataset-id Task01_BrainTumour")
        print("2. Train a model:")
        print("   python src/training/train_enhanced.py "
              "--dataset-config config/datasets/msd_task01_brain.json")
        return 0
    else:
        print("💥 Some tests FAILED - please check the output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
