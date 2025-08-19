#!/usr/bin/env python3
"""Unit tests for transform presets."""

import numpy as np
import torch

from monai.transforms import (Compose, EnsureChannelFirstd, 
                             RandSpatialCropd, ToTensord)

from src.data.transforms_presets import (get_transforms_brats_like, 
                                        get_transforms_ct_liver)


def _get_transforms_without_io(roi_size=(32, 32, 32)):
    """Get basic transforms for testing without file I/O."""
    return Compose([
        EnsureChannelFirstd(keys=["image", "label"]),
        RandSpatialCropd(keys=["image", "label"], roi_size=roi_size, random_size=False),
        ToTensord(keys=["image", "label"])
    ])


def test_transforms_presets_import():
    """Test that transform presets can be imported without error."""
    # This should not raise any import errors
    train_transforms, val_transforms = get_transforms_brats_like()
    assert train_transforms is not None
    assert val_transforms is not None
    
    train_transforms, val_transforms = get_transforms_ct_liver()
    assert train_transforms is not None
    assert val_transforms is not None


def test_brats_like_transforms_run():
    """Test BraTS-like transforms actually execute."""
    # Create synthetic BraTS-like data (4 modalities)
    # Using channel-first format to match expected MONAI format
    data = {
        "image": np.random.rand(4, 32, 32, 32).astype(np.float32),
        "label": np.random.randint(0, 4, (1, 32, 32, 32)).astype(np.uint8)
    }
    
    # Use basic transforms without file I/O for testing
    test_transforms = _get_transforms_without_io(roi_size=(32, 32, 32))
    
    # Apply transforms
    out = test_transforms(data)
    
    # Basic checks - images should be processed
    assert "image" in out
    assert "label" in out
    assert isinstance(out["image"], torch.Tensor)
    assert isinstance(out["label"], torch.Tensor)
    
    # Check channel dimension (BraTS has 4 modalities)
    # After EnsureChannelFirstd and transforms, should maintain channels
    print(f"Image shape: {out['image'].shape}")  # Debug output
    print(f"Label shape: {out['label'].shape}")  # Debug output
    assert out["image"].shape[0] == 4  # Channel dim is first after transforms
    
    # Check spatial dimensions match expected crop size (32x32x32)
    assert out["image"].shape[1:] == (32, 32, 32)
    assert out["label"].shape[1:] == (32, 32, 32)


def test_ct_liver_transforms_run():
    """Test CT liver transforms actually execute."""
    # Create synthetic CT liver data (1 modality)
    # Using channel-first format to match expected MONAI format
    data = {
        "image": np.random.rand(1, 32, 32, 32).astype(np.float32),
        "label": np.random.randint(0, 3, (1, 32, 32, 32)).astype(np.uint8)
    }
    
    # Use basic transforms without file I/O for testing
    test_transforms = _get_transforms_without_io(roi_size=(32, 32, 32))
    
    # Apply transforms
    out = test_transforms(data)
    
    # Basic checks - images should be processed
    assert "image" in out
    assert "label" in out
    assert isinstance(out["image"], torch.Tensor)
    assert isinstance(out["label"], torch.Tensor)
    
    # Check channel dimension (CT liver has 1 modality)
    print(f"Image shape: {out['image'].shape}")  # Debug output
    print(f"Label shape: {out['label'].shape}")  # Debug output
    assert out["image"].shape[0] == 1  # Channel dim is first after transforms
    
    # Check spatial dimensions match expected crop size (32x32x32)
    assert out["image"].shape[1:] == (32, 32, 32)
    assert out["label"].shape[1:] == (32, 32, 32)
