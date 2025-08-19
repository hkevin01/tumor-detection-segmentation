#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick validation script to test MONAI integration components."""

import os
import sys

sys.path.insert(0, os.path.abspath('.'))

def main():
    print("🧪 Quick MONAI Integration Validation")
    print("=" * 40)

    # Test imports
    try:
        from src.data.loaders_monai import load_monai_decathlon
        print("✅ MONAI loader import successful")
    except ImportError as e:
        print(f"❌ MONAI loader import failed: {e}")
        return 1

    try:
        from src.data.transforms_presets import (get_transforms_brats_like,
                                                 get_transforms_ct_liver)
        print("✅ Transform presets import successful")
    except ImportError as e:
        print(f"❌ Transform presets import failed: {e}")
        return 1

    # Test configuration files exist
    import json
    from pathlib import Path

    configs = [
        "config/datasets/msd_task01_brain.json",
        "config/datasets/msd_task03_liver.json"
    ]

    for config_path in configs:
        if Path(config_path).exists():
            try:
                with open(config_path) as f:
                    cfg = json.load(f)
                print(f"✅ {config_path} - valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ {config_path} - invalid JSON: {e}")
                return 1
        else:
            print(f"❌ {config_path} - not found")
            return 1

    # Test CLI script exists
    cli_script = "scripts/data/pull_monai_dataset.py"
    if Path(cli_script).exists():
        print(f"✅ {cli_script} - CLI script present")
    else:
        print(f"❌ {cli_script} - not found")
        return 1

    # Test demo script exists
    demo_script = "scripts/demo/test_monai_integration.py"
    if Path(demo_script).exists():
        print(f"✅ {demo_script} - demo script present")
    else:
        print(f"❌ {demo_script} - not found")
        return 1

    print("\n🎉 All MONAI integration components are in place!")
    print("\nReady to use:")
    print("1. Download dataset: python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour")
    print("2. Run tests: python scripts/demo/test_monai_integration.py")
    print("3. Train model: python src/training/train_enhanced.py --dataset-config config/datasets/msd_task01_brain.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
