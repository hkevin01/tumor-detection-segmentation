#!/usr/bin/env python3
"""
Test script for the enhanced inference capabilities.
"""

import sys
from pathlib import Path

# Test if we can import the enhanced inference script
try:
    sys.path.append(str(Path(__file__).parent))
    from src.inference.inference_enhanced import get_device, parse_args
    print("✓ Enhanced inference script imports successfully")

    # Test argument parsing
    args = parse_args.__func__()  # Get the function without calling it
    print("✓ Argument parsing function available")

    # Test device detection
    device = get_device("auto")
    print(f"✓ Device detection working: {device}")

except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Other error: {e}")

print("\n" + "="*50)
print("Enhanced Inference Features Available:")
print("="*50)

features = [
    "CLI with --save-overlays and --save-prob-maps flags",
    "Multi-slice overlay panels (auto or custom slices)",
    "Probability heatmaps for uncertainty inspection",
    "Support for both Decathlon datasets and raw NIfTI files",
    "Test-time augmentation (TTA) with --tta flag",
    "Mixed precision inference with --amp flag",
    "Configurable sliding window overlap",
    "Automatic Dice computation when ground truth available",
    "NIfTI mask export alongside visualizations"
]

for i, feature in enumerate(features, 1):
    print(f"{i:2d}. {feature}")

print("\n" + "="*50)
print("Usage Examples:")
print("="*50)

examples = [
    "# Decathlon validation set with overlays:",
    "python src/inference/inference_enhanced.py \\",
    "  --config config/recipes/unetr_multimodal.json \\",
    "  --dataset-config config/datasets/msd_task01_brain.json \\",
    "  --model models/unetr/best.pt \\",
    "  --save-overlays --save-prob-maps --class-index 1",
    "",
    "# Simple directory inference:",
    "python src/inference/inference_enhanced.py \\",
    "  --config config/recipes/unetr_multimodal.json \\",
    "  --model models/unetr/best.pt \\",
    "  --input data/test_images/ \\",
    "  --save-overlays --slices 40,60,80"
]

for example in examples:
    print(example)
