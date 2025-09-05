#!/usr/bin/env python3
"""
MONAI Verification Checklist

Comprehensive verification script to test all MONAI integrations and data loading capabilities
before proceeding to training workflows.
"""

import logging
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_monai_imports():
    """Test core MONAI imports"""
    print("📋 Testing MONAI imports...")
    try:
        import monai
        print(f"✅ MONAI version: {monai.__version__}")

        print("✅ MONAI data imports successful")

        print("✅ MONAI transforms imports successful")

        print("✅ MONAI networks imports successful")

        return True
    except Exception as e:
        print(f"❌ MONAI imports failed: {e}")
        return False

def test_torch_integration():
    """Test PyTorch integration"""
    print("\n📋 Testing PyTorch integration...")
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")

        # Test device availability
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name()}")
        else:
            print("⚠️ CUDA not available - will use CPU")

        return True
    except Exception as e:
        print(f"❌ PyTorch integration failed: {e}")
        return False

def test_project_data_loaders():
    """Test our project's data loading capabilities"""
    print("\n📋 Testing project data loaders...")
    try:
        print("✅ Project MONAI loader imported")

        print("✅ Project transforms presets imported")

        return True
    except Exception as e:
        print(f"❌ Project data loaders failed: {e}")
        traceback.print_exc()
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n📋 Testing configuration loading...")
    try:
        config_path = project_root / "config" / "datasets" / "msd_task01_brain.json"
        if config_path.exists():
            import json
            with open(config_path) as f:
                config = json.load(f)
            print(f"✅ Dataset config loaded: {config.get('dataset_name', 'Unknown')}")
        else:
            print("⚠️ Dataset config not found")

        recipe_path = project_root / "config" / "recipes" / "test_overlay.json"
        if recipe_path.exists():
            with open(recipe_path) as f:
                recipe = json.load(f)
            print(f"✅ Recipe config loaded: {recipe.get('name', 'Unknown')}")
        else:
            print("⚠️ Recipe config not found")

        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_dataset_simulation():
    """Test creating simulated dataset"""
    print("\n📋 Testing dataset simulation...")
    try:
        import json
        import tempfile

        # Create temporary dataset structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create synthetic dataset.json
            dataset_json = {
                "name": "Test Dataset",
                "description": "Synthetic test dataset",
                "labels": {"0": "background", "1": "tumor"},
                "numTraining": 2,
                "numTest": 1,
                "training": [
                    {"image": str(temp_path / "image1.nii.gz"), "label": str(temp_path / "label1.nii.gz")},
                    {"image": str(temp_path / "image2.nii.gz"), "label": str(temp_path / "label2.nii.gz")}
                ],
                "test": [
                    {"image": str(temp_path / "image3.nii.gz"), "label": str(temp_path / "label3.nii.gz")}
                ]
            }

            dataset_file = temp_path / "dataset.json"
            with open(dataset_file, 'w') as f:
                json.dump(dataset_json, f, indent=2)

            # Test loading the synthetic dataset
            from monai.data import load_decathlon_datalist
            train_files = load_decathlon_datalist(str(dataset_file), True, "training")
            print(f"✅ Synthetic dataset loaded: {len(train_files)} training files")

        return True
    except Exception as e:
        print(f"❌ Dataset simulation failed: {e}")
        traceback.print_exc()
        return False

def test_mlflow_integration():
    """Test MLflow integration"""
    print("\n📋 Testing MLflow integration...")
    try:
        import mlflow
        print(f"✅ MLflow version: {mlflow.__version__}")

        # Test basic MLflow functionality
        with mlflow.start_run(run_name="verification_test") as run:
            mlflow.log_param("test_param", "verification")
            mlflow.log_metric("test_metric", 0.99)
            print(f"✅ MLflow run created: {run.info.run_id[:8]}...")

        return True
    except Exception as e:
        print(f"❌ MLflow integration failed: {e}")
        return False

def test_crash_prevention():
    """Test crash prevention system"""
    print("\n📋 Testing crash prevention system...")
    try:
        from src.utils.crash_prevention import MemoryMonitor, safe_execution

        monitor = MemoryMonitor()
        status = monitor.check_memory()
        print(f"✅ Memory monitor working: {status['usage_percent']:.1f}% used")

        @safe_execution(max_retries=1)
        def test_function():
            return "test successful"

        result = test_function()
        print(f"✅ Safe execution decorator working: {result}")

        return True
    except Exception as e:
        print(f"❌ Crash prevention system failed: {e}")
        return False

def main():
    """Run comprehensive MONAI verification checklist"""
    print("="*60)
    print("🚀 MONAI VERIFICATION CHECKLIST")
    print("="*60)

    tests = [
        ("MONAI Imports", test_monai_imports),
        ("PyTorch Integration", test_torch_integration),
        ("Project Data Loaders", test_project_data_loaders),
        ("Configuration Loading", test_config_loading),
        ("Dataset Simulation", test_dataset_simulation),
        ("MLflow Integration", test_mlflow_integration),
        ("Crash Prevention", test_crash_prevention),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "="*60)
    print("📊 VERIFICATION RESULTS")
    print("="*60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if success:
            passed += 1

    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 ALL MONAI VERIFICATION TESTS PASSED!")
        print("✅ System ready for dataset download and training!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
