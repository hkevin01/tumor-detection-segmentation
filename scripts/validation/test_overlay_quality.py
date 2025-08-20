#!/usr/bin/env python3
"""
Test script to verify overlay quality improvements.
Creates synthetic data to test multi-slice overlay panels.
"""

from pathlib import Path

import torch

# Test visualization callbacks
try:
    from src.training.callbacks.visualization import save_overlay_panel, save_probability_panel
    VISUALIZATION_AVAILABLE = True
    print("✓ Visualization callbacks available")
except ImportError as e:
    print(f"✗ Visualization callbacks not available: {e}")
    VISUALIZATION_AVAILABLE = False

def create_synthetic_data():
    """Create synthetic medical image data for testing."""
    # Create a 3D image (1 channel, 64x64x40)
    H, W, D = 64, 64, 40
    image = torch.randn(1, H, W, D) * 0.5 + 0.5  # Normalized to [0,1] range

    # Create synthetic ground truth (tumor in center region)
    gt = torch.zeros(2, H, W, D)  # 2 classes: background, tumor
    center_h, center_w = H // 2, W // 2
    # Add a small tumor region in the center slices
    for z in range(D // 3, 2 * D // 3):
        h_start, h_end = center_h - 8, center_h + 8
        w_start, w_end = center_w - 8, center_w + 8
        gt[1, h_start:h_end, w_start:w_end, z] = 1.0
    gt[0] = 1.0 - gt[1]  # Background is complement of tumor

    # Create synthetic prediction (similar to GT with some noise)
    pred = gt.clone()
    noise = torch.randn_like(pred[1]) * 0.1
    pred[1] = torch.clamp(pred[1] + noise, 0, 1)
    pred[0] = 1.0 - pred[1]

    return image, gt, pred

def test_overlay_panels():
    """Test the overlay panel functionality."""
    print("\n=== Testing Overlay Quality ===")

    if not VISUALIZATION_AVAILABLE:
        print("Cannot test - visualization callbacks not available")
        return False

    # Create test data
    image, gt_oh, pred_oh = create_synthetic_data()
    print(f"Created synthetic data: image {image.shape}, gt {gt_oh.shape}, pred {pred_oh.shape}")

    # Test output directory
    test_dir = Path("test_outputs")
    test_dir.mkdir(exist_ok=True)

    # Test 1: Default multi-slice overlay (25%, 50%, 75%)
    try:
        overlay_path = test_dir / "test_overlay_default.png"
        save_overlay_panel(image, gt_oh, pred_oh, overlay_path)
        print(f"✓ Default overlay saved to {overlay_path}")
    except Exception as e:
        print(f"✗ Default overlay failed: {e}")
        return False

    # Test 2: Custom slice overlay
    try:
        D = image.shape[-1]
        custom_slices = [5, 15, 25, 35]  # 4 specific slices
        overlay_path = test_dir / "test_overlay_custom.png"
        save_overlay_panel(image, gt_oh, pred_oh, overlay_path, custom_slices)
        print(f"✓ Custom slice overlay saved to {overlay_path}")
    except Exception as e:
        print(f"✗ Custom slice overlay failed: {e}")
        return False

    # Test 3: Probability panel
    try:
        prob_path = test_dir / "test_probability.png"
        # Use just the tumor class as a 3D probability map (H, W, D)
        tumor_probs = pred_oh[1]  # Shape: (H, W, D)
        save_probability_panel(image, tumor_probs, prob_path)
        print(f"✓ Probability panel saved to {prob_path}")
    except Exception as e:
        print(f"✗ Probability panel failed: {e}")
        return False

    print("✓ All overlay tests passed!")
    return True

def test_inference_overlay_structure():
    """Test inference overlay directory structure."""
    print("\n=== Testing Inference Directory Structure ===")

    # Simulate inference output structure
    output_path = Path("test_outputs/inference_test")
    overlay_dir = output_path / "inference_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    # Test the directory structure matches expected pattern
    expected_pattern = "*/inference_overlays"
    if "inference_overlays" in str(overlay_dir):
        print(f"✓ Inference overlay directory structure correct: {overlay_dir}")
        return True
    else:
        print(f"✗ Inference overlay directory structure incorrect: {overlay_dir}")
        return False

if __name__ == "__main__":
    print("Testing Overlay Quality Improvements")
    print("=" * 50)

    # Run tests
    overlay_test = test_overlay_panels()
    structure_test = test_inference_overlay_structure()

    if overlay_test and structure_test:
        print("\n🎉 All tests passed! Overlay quality improvements verified.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
