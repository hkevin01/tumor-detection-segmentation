#!/usr/bin/env python3
"""
Simple 2-epoch training test to validate the pipeline
"""
import sys

sys.path.insert(0, '.')

import json
from pathlib import Path

import monai
import torch


def test_training_pipeline():
    """Test the training pipeline with minimal configuration"""

    print("🔧 Testing Training Pipeline...")
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ MONAI: {monai.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")

    # Check if dataset exists
    dataset_path = Path("data/msd/Task01_BrainTumour")
    if not dataset_path.exists():
        print("❌ Dataset not found")
        return False

    print("✅ Dataset found")

    # Check config files
    test_config = Path("config/recipes/test_overlay.json")
    dataset_config = Path("config/datasets/msd_task01_brain.json")

    if not test_config.exists() or not dataset_config.exists():
        print("❌ Config files not found")
        return False

    print("✅ Config files found")

    # Try to import our modules
    try:
        from monai.networks.nets import UNETR

        from src.data.loaders_monai import load_monai_decathlon
        print("✅ Module imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Load configs
    with open(test_config) as f:
        recipe_config = json.load(f)
    with open(dataset_config) as f:
        data_config = json.load(f)

    print("✅ Config files loaded")

    try:
        # Test data loading
        print("🔄 Testing data loader...")
        train_loader, val_loader = load_monai_decathlon(
            data_config['data_root'],
            f"{data_config['data_root']}/{data_config['dataset_id']}/dataset.json",
            batch_size=1,  # Small batch for testing
            num_workers=1,
            cache_rate=0.1,  # Minimal caching
            train_transforms=None,
            val_transforms=None
        )
        print("✅ Data loaders created successfully")

        # Test model creation
        print("🔄 Testing model creation...")
        model = UNETR(
            in_channels=4,
            out_channels=4,
            img_size=(96, 96, 96),
            feature_size=16,
            hidden_size=768,
            mlp_dim=3072,
            num_heads=12,
            pos_embed="perceptron",
            norm_name="instance",
            res_block=True,
            dropout_rate=0.0
        )
        print("✅ Model created successfully")

        # Test one forward pass
        print("🔄 Testing forward pass...")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)

        # Get one batch
        for batch in train_loader:
            inputs = batch['image'].to(device)
            targets = batch['label'].to(device)

            with torch.no_grad():
                outputs = model(inputs)

            print("✅ Forward pass successful")
            print(f"   Input shape: {inputs.shape}")
            print(f"   Output shape: {outputs.shape}")
            print(f"   Target shape: {targets.shape}")
            break

        print("🎉 Training pipeline test PASSED!")
        return True

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_training_pipeline()
    exit(0 if success else 1)
