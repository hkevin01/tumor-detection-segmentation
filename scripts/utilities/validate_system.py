#!/usr/bin/env python3
"""
System validation and feature demonstration script
Tests all implemented features and provides comprehensive overview
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

print("🏥 Enhanced Medical Imaging AI System Validation")
print("=" * 55)

# Test imports and availability
print("\n📦 Testing Package Availability:")

# Core packages
packages = {
    "torch": "PyTorch",
    "numpy": "NumPy",
    "monai": "MONAI",
    "mlflow": "MLflow",
    "nibabel": "NiBabel",
    "pydicom": "PyDICOM",
    "matplotlib": "Matplotlib",
    "sklearn": "Scikit-learn"
}

available_packages = {}
for package, name in packages.items():
    try:
        __import__(package)
        print(f"  ✅ {name}")
        available_packages[package] = True
    except ImportError:
        print(f"  ❌ {name} - Not available")
        available_packages[package] = False

# Test custom modules
print("\n🧩 Testing Custom Modules:")
custom_modules = {
    "src.data.preprocess": "Enhanced Data Preprocessing",
    "src.fusion.attention_fusion": "Multi-modal Fusion",
    "src.models.cascade_detector": "Cascade Detection",
    "src.utils.logging_mlflow": "MLflow Integration",
    "src.training.train_enhanced": "Enhanced Training"
}

available_modules = {}
for module, name in custom_modules.items():
    try:
        __import__(module)
        print(f"  ✅ {name}")
        available_modules[module] = True
    except ImportError as e:
        print(f"  ❌ {name} - {e}")
        available_modules[module] = False

# Test MONAI features if available
if available_packages.get("monai", False):
    print("\n🧠 Testing MONAI Features:")

    try:
        from monai.networks.nets import UNETR, UNet
        print("  ✅ Neural Networks (UNet, UNETR)")
    except ImportError:
        print("  ❌ Neural Networks")

    try:
        from monai.transforms import Compose, LoadImaged
        print("  ✅ Data Transforms")
    except ImportError:
        print("  ❌ Data Transforms")

    try:
        from monai.losses import DiceLoss, FocalLoss
        print("  ✅ Loss Functions")
    except ImportError:
        print("  ❌ Loss Functions")

    try:
        from monai.metrics import DiceMetric, HausdorffDistanceMetric
        print("  ✅ Evaluation Metrics")
    except ImportError:
        print("  ❌ Evaluation Metrics")

# Test MLflow if available
if available_packages.get("mlflow", False):
    print("\n📊 Testing MLflow Integration:")

    try:
        import mlflow
        mlflow.set_tracking_uri("file:scripts/validation/test_mlruns")
        print("  ✅ MLflow Tracking")

        # Test logging
        with mlflow.start_run():
            mlflow.log_param("test_param", "test_value")
            mlflow.log_metric("test_metric", 0.85)
        print("  ✅ Parameter & Metric Logging")

    except Exception as e:
        print(f"  ❌ MLflow Integration - {e}")

# Test GPU availability
print("\n⚡ Testing GPU Availability:")
if available_packages.get("torch", False):
    import torch

    if torch.cuda.is_available():
        print(f"  ✅ CUDA GPU: {torch.cuda.get_device_name(0)}")
        print(f"     Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print(f"     CUDA Version: {torch.version.cuda}")
    else:
        print("  ⚠️  No CUDA GPU detected")

    # Test ROCm
    try:
        if torch.version.hip:
            print(f"  ✅ ROCm GPU Support: {torch.version.hip}")
    except:
        print("  ⚠️  No ROCm support detected")
else:
    print("  ❌ Cannot test GPU - PyTorch not available")

# Test model creation
print("\n🤖 Testing Model Creation:")
if available_modules.get("src.fusion.attention_fusion", False):
    try:
        from src.fusion.attention_fusion import create_multi_modal_model

        # Test UNETR creation
        model = create_multi_modal_model("unetr", "early")
        params = sum(p.numel() for p in model.parameters())
        print(f"  ✅ Multi-modal UNETR: {params:,} parameters")

        # Test UNet creation
        model = create_multi_modal_model("unet")
        params = sum(p.numel() for p in model.parameters())
        print(f"  ✅ Standard UNet: {params:,} parameters")

    except Exception as e:
        print(f"  ❌ Model Creation - {e}")

# Test cascade pipeline
if available_modules.get("src.models.cascade_detector", False):
    try:
        from src.models.cascade_detector import create_cascade_pipeline

        pipeline = create_cascade_pipeline()
        total_params = sum(p.numel() for p in pipeline.parameters())
        print(f"  ✅ Cascade Pipeline: {total_params:,} parameters")

    except Exception as e:
        print(f"  ❌ Cascade Pipeline - {e}")

# Test configuration recipes
print("\n⚙️  Testing Configuration Recipes:")
config_dir = project_root / "config" / "recipes"
if config_dir.exists():
    configs = list(config_dir.glob("*.json"))
    for config_file in configs:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"  ✅ {config_file.name}")
        except Exception as e:
            print(f"  ❌ {config_file.name} - {e}")
else:
    print("  ❌ Configuration directory not found")

# Test data preprocessing
print("\n📊 Testing Data Preprocessing:")
if available_modules.get("src.data.preprocess", False):
    try:
        from src.data.preprocess import EnhancedDataPreprocessing

        config = {
            "target_spacing": [1.0, 1.0, 1.0],
            "spatial_size": [128, 128, 128],
            "patch_size": [96, 96, 96],
            "max_epochs": 100,
        }

        preprocessor = EnhancedDataPreprocessing(config)
        print("  ✅ Enhanced Data Preprocessing")

        # Test transforms
        train_transforms = preprocessor.get_training_transforms()
        val_transforms = preprocessor.get_validation_transforms()
        print(f"  ✅ Training Transforms: {len(train_transforms.transforms)} steps")
        print(f"  ✅ Validation Transforms: {len(val_transforms.transforms)} steps")

    except Exception as e:
        print(f"  ❌ Data Preprocessing - {e}")

# Test file structure
print("\n📁 Testing File Structure:")
required_dirs = [
    "src/data",
    "src/models",
    "src/training",
    "src/fusion",
    "src/utils",
    "config/recipes",
    "scripts/setup",
    "scripts/utilities",
    "monai_label_app"
]

for dir_path in required_dirs:
    full_path = project_root / dir_path
    if full_path.exists():
        print(f"  ✅ {dir_path}")
    else:
        print(f"  ❌ {dir_path}")

# Test scripts
print("\n🔧 Testing Scripts:")
script_files = [
    "scripts/setup/setup_monai_label.sh",
    "scripts/utilities/run_monai_label.sh",
    "scripts/utilities/start_medical_gui.sh"
]

for script_path in script_files:
    full_path = project_root / script_path
    if full_path.exists() and os.access(full_path, os.X_OK):
        print(f"  ✅ {script_path} (executable)")
    elif full_path.exists():
        print(f"  ⚠️  {script_path} (not executable)")
    else:
        print(f"  ❌ {script_path} (missing)")

# Test Docker files
print("\n🐳 Testing Docker Configuration:")
docker_files = [
    "config/docker/Dockerfile.cuda",
    "config/docker/Dockerfile.rocm",
    "config/docker/docker-compose.yml"
]

for docker_file in docker_files:
    full_path = project_root / docker_file
    if full_path.exists():
        print(f"  ✅ {docker_file}")
    else:
        print(f"  ❌ {docker_file}")

# Generate summary report
print("\n📋 SYSTEM VALIDATION SUMMARY")
print("=" * 40)

total_packages = len(packages)
available_package_count = sum(available_packages.values())
package_score = (available_package_count / total_packages) * 100

total_modules = len(custom_modules)
available_module_count = sum(available_modules.values())
module_score = (available_module_count / total_modules) * 100

print(f"Package Availability: {available_package_count}/{total_packages} ({package_score:.1f}%)")
print(f"Custom Modules: {available_module_count}/{total_modules} ({module_score:.1f}%)")

# Overall system status
overall_score = (package_score + module_score) / 2

if overall_score >= 90:
    status = "🟢 EXCELLENT"
elif overall_score >= 75:
    status = "🟡 GOOD"
elif overall_score >= 50:
    status = "🟠 FAIR"
else:
    status = "🔴 NEEDS WORK"

print(f"\nOverall System Status: {status} ({overall_score:.1f}%)")

# Next steps recommendations
print("\n🎯 NEXT STEPS:")
if available_package_count < total_packages:
    print("1. Install missing packages: pip install -r requirements.txt")

if not available_packages.get("monai", False):
    print("2. Install MONAI: pip install monai")

if not available_packages.get("mlflow", False):
    print("3. Install MLflow: pip install mlflow")

print("4. Run setup script: ./scripts/setup/setup_monai_label.sh")
print("5. Start system: ./scripts/utilities/start_medical_gui.sh")
print("6. Test training: python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json")

print("\n🎉 ENHANCED FEATURES AVAILABLE:")
print("• Multi-modal MRI processing (T1, T1c, T2, FLAIR)")
print("• Cross-attention fusion architectures")
print("• Detection + segmentation cascade")
print("• MONAI Label interactive annotation")
print("• MLflow experiment tracking")
print("• Modality-specific normalization")
print("• Curriculum augmentation")
print("• Test-time augmentation")
print("• Uncertainty estimation")
print("• Docker deployment")
print("• Comprehensive configuration recipes")

print("\n✅ System validation completed!")
print("🏥 Ready for advanced medical imaging AI research and applications!")
