#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONAI Integration Verification Checklist Script

This script runs through the verification checklist provided in the user request:
1. Python import sanity checks
2. Unit tests execution
3. Integration tests execution
4. Optional training dry-run
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, check_output=True):
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"Command: {cmd}")
    print('='*60)

    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)

        if check_output:
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run the complete verification checklist."""
    print("🧪 MONAI Integration Verification Checklist")
    print("=" * 60)
    print("Following the verification steps from user request")

    # Change to project root
    os.chdir(Path(__file__).parent)
    print(f"Working directory: {os.getcwd()}")

    results = []

    # 1. Python import sanity checks
    print("\n" + "="*60)
    print("📦 PYTHON IMPORT SANITY CHECKS")
    print("="*60)

    # Test 1a: MONAI loader import
    cmd1 = 'python -c "from src.data.loaders_monai import load_monai_decathlon; print(\'ok\')"'
    success1 = run_command(cmd1, "MONAI loader import")
    results.append(("MONAI loader import", success1))

    # Test 1b: Transform presets import
    cmd2 = 'python -c "from src.data.transforms_presets import get_transforms_brats_like; print(\'ok\')"'
    success2 = run_command(cmd2, "Transform presets import")
    results.append(("Transform presets import", success2))

    # 2. Unit tests
    print("\n" + "="*60)
    print("🧪 UNIT TESTS")
    print("="*60)

    cmd3 = ["python", "-m", "pytest", "-q", "tests/unit/test_transforms_presets.py"]
    success3 = run_command(cmd3, "Unit tests - Transform presets")
    results.append(("Unit tests", success3))

    # 3. Integration tests (synthetic, CPU)
    print("\n" + "="*60)
    print("🔗 INTEGRATION TESTS (SYNTHETIC, CPU)")
    print("="*60)

    cmd4 = ["python", "-m", "pytest", "-q", "tests/integration/test_monai_msd_loader.py"]
    success4 = run_command(cmd4, "Integration tests - MONAI MSD loader")
    results.append(("Integration tests", success4))

    # 4. Optional: Training dry-run (commented out by default as it's slow)
    print("\n" + "="*60)
    print("🏃 TRAINING DRY-RUN (OPTIONAL - COMMENTED OUT)")
    print("="*60)
    print("Skipping training dry-run as it's slow. To run manually:")
    print("python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --epochs 1 --no-deterministic")

    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)

    all_passed = True
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} | {description}")
        if not success:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 All verification checks PASSED!")
        print("✨ MONAI integration is working correctly!")
        print("\n📋 What you can do next:")
        print("1. Download real datasets:")
        print("   python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour")
        print("2. Run complete test suite:")
        print("   python scripts/demo/test_monai_integration.py")
        print("3. Train models with MONAI datasets:")
        print("   python src/training/train_enhanced.py --dataset-config config/datasets/msd_task01_brain.json")
        return 0
    else:
        print("💥 Some verification checks FAILED")
        print("Please check the output above and fix any issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
