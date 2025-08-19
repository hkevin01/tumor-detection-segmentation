#!/usr/bin/env python3

import numpy as np
import torch

from src.data.transforms_presets import get_transforms_brats_like, get_transforms_ct_liver


def test_transforms_presets_import():
    """Test that transform presets can be imported."""
    # Should pass if imports work
    assert callable(get_transforms_brats_like)
    assert callable(get_transforms_ct_liver)


def test_brats_like_transforms_run():
    """Test BraTS-like transforms actually execute."""
    # Create synthetic BraTS-like data (4 modalities)
    data = {
        "image": np.random.rand(4, 32, 32, 32).astype(np.float32),
        "label": np.random.randint(0, 4, (1, 32, 32, 32)).astype(np.uint8)
    }

    # Get transforms (using train transforms for testing)
    train_transforms, _ = get_transforms_brats_like(roi_size=(32, 32, 32))

    # Apply transforms
    out = train_transforms(data)

    # Basic checks - images should be processed
    assert "image" in out
    assert "label" in out
    assert isinstance(out["image"], torch.Tensor)
    assert isinstance(out["label"], torch.Tensor)

    # Check channel dimension (BraTS has 4 modalities)
    # Note: shape is (channel, H, W, D) for 3D data after transforms
    assert out["image"].shape[0] == 4  # Channel dim is first after transforms

    # Check spatial dimensions match expected crop size (32x32x32)
    assert out["image"].shape[1:] == (32, 32, 32)
    assert out["label"].shape[1:] == (32, 32, 32)


def test_ct_liver_transforms_run():
    """Test CT liver transforms actually execute."""
    # Create synthetic CT liver data (1 modality)
    data = {
        "image": np.random.rand(1, 32, 32, 32).astype(np.float32),
        "label": np.random.randint(0, 3, (1, 32, 32, 32)).astype(np.uint8)
    }

    # Get transforms (using train transforms for testing)
    train_transforms, _ = get_transforms_ct_liver(roi_size=(32, 32, 32))

    # Apply transforms
    out = train_transforms(data)

    # Basic checks - images should be processed
    assert "image" in out
    assert "label" in out
    assert isinstance(out["image"], torch.Tensor)
    assert isinstance(out["label"], torch.Tensor)

    # Check channel dimension (CT has 1 modality)
    # Note: shape is (channel, H, W, D) for 3D data after transforms
    assert out["image"].shape[0] == 1  # Channel dim is first after transforms

    # Check spatial dimensions match expected crop size (32x32x32)
    assert out["image"].shape[1:] == (32, 32, 32)
    assert out["label"].shape[1:] == (32, 32, 32)
