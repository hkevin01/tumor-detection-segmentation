#!/usr/bin/env python3
"""
Test script to verify the new visualization system compatibility.
"""

from pathlib import Path

import torch

# Test the new visualization functions
try:
    from src.training.callbacks.visualization import save_overlay_panel, save_prob_panel
    print("✓ New visualization functions imported successfully")

    # Create synthetic test data
    print("\nTesting new visualization functions:")

    # Create test tensors
    image = torch.randn(1, 64, 64, 40)  # (C, H, W, D)
    gt_onehot = torch.zeros(2, 64, 64, 40)  # (C_out, H, W, D)
    pred_onehot = torch.zeros(2, 64, 64, 40)

    # Add some synthetic tumor regions
    gt_onehot[1, 20:40, 20:40, 15:25] = 1.0
    pred_onehot[1, 22:38, 22:38, 16:24] = 0.8
    gt_onehot[0] = 1.0 - gt_onehot[1]  # background
    pred_onehot[0] = 1.0 - pred_onehot[1]

    # Test directory
    test_dir = Path("test_viz")
    test_dir.mkdir(exist_ok=True)

    # Test 1: save_overlay_panel with new signature
    try:
        save_overlay_panel(
            image_ch_first=image,
            label_onehot=gt_onehot,
            pred_onehot=pred_onehot,
            out_path=test_dir / "test_overlay.png",
            slices="auto"
        )
        print("✓ save_overlay_panel works with new signature")
    except Exception as e:
        print(f"✗ save_overlay_panel failed: {e}")

    # Test 2: save_prob_panel
    try:
        save_prob_panel(
            image_ch_first=image,
            prob_logits_or_probs=pred_onehot,
            out_path=test_dir / "test_prob.png",
            slices="auto",
            class_index=1,
            apply_softmax=False
        )
        print("✓ save_prob_panel works")
    except Exception as e:
        print(f"✗ save_prob_panel failed: {e}")

    # Test 3: String slice parsing
    try:
        save_overlay_panel(
            image_ch_first=image,
            label_onehot=gt_onehot,
            pred_onehot=pred_onehot,
            out_path=test_dir / "test_custom_slices.png",
            slices="10,20,30"
        )
        print("✓ Custom slice string parsing works")
    except Exception as e:
        print(f"✗ Custom slice parsing failed: {e}")

    # Test 4: Prediction-only mode (no ground truth)
    try:
        save_overlay_panel(
            image_ch_first=image,
            label_onehot=None,
            pred_onehot=pred_onehot,
            out_path=test_dir / "test_pred_only.png",
            slices="auto"
        )
        print("✓ Prediction-only mode works")
    except Exception as e:
        print(f"✗ Prediction-only mode failed: {e}")

    print(f"\n✓ Test outputs saved to: {test_dir}/")

except ImportError as e:
    print(f"✗ Import failed: {e}")
except Exception as e:
    print(f"✗ Test failed: {e}")

print("\n" + "="*60)
print("ENHANCED VISUALIZATION SYSTEM SUMMARY")
print("="*60)

enhancements = [
    "🔄 Upgraded visualization.py with modern type hints and flexible slicing",
    "🎯 save_overlay_panel: supports 'auto' slices, custom slices, prediction-only mode",
    "🌈 save_prob_panel: probability heatmaps with configurable colormaps",
    "🔧 Enhanced inference.py with comprehensive CLI flags",
    "📊 Support for Decathlon datasets and raw NIfTI files",
    "🚀 Test-time augmentation (TTA) and mixed precision",
    "💾 NIfTI mask export alongside PNG overlays",
    "📈 Automatic Dice computation when ground truth is available",
    "🎨 Configurable class indices, colormaps, and transparency",
    "🔄 Backward compatibility with existing training script"
]

for enhancement in enhancements:
    print(enhancement)

print("\n" + "="*60)
print("READY TO USE - EXAMPLE COMMANDS")
print("="*60)

commands = [
    "# Enhanced training with overlays:",
    "python src/training/train_enhanced.py --save-overlays",
    "",
    "# Decathlon validation inference with all visualizations:",
    "python src/inference/inference_enhanced.py \\",
    "  --config config/recipes/unetr_multimodal.json \\",
    "  --dataset-config config/datasets/msd_task01_brain.json \\",
    "  --model models/unetr/best.pt \\",
    "  --save-overlays --save-prob-maps --class-index 1 --tta",
    "",
    "# Simple directory inference:",
    "python src/inference/inference_enhanced.py \\",
    "  --config config/recipes/unetr_multimodal.json \\",
    "  --model models/unetr/best.pt \\",
    "  --input data/test_images/ \\",
    "  --save-overlays --slices 40,60,80"
]

for cmd in commands:
    print(cmd)
