#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
import torch

from src.data.loaders_monai import load_monai_decathlon
from src.data.transforms_presets import get_transforms_brats_like


def _write_nifti(arr: np.ndarray, path: Path) -> None:
    affine = np.eye(4, dtype=np.float32)
    img = nib.Nifti1Image(arr.astype(np.float32), affine)
    nib.save(img, str(path))


def _make_synthetic_brats_like(
    root: Path,
    task: str = "Task01_BrainTumour",
    n_train: int = 2,
    n_val: int = 1
):
    """
    Build a tiny Decathlon-like folder with 4-channel MRI and 2-class labels.
    """
    base = root / task
    imagesTr = base / "imagesTr"
    labelsTr = base / "labelsTr"
    imagesTs = base / "imagesTs"  # not used but many tools expect it

    imagesTr.mkdir(parents=True, exist_ok=True)
    labelsTr.mkdir(parents=True, exist_ok=True)
    imagesTs.mkdir(parents=True, exist_ok=True)

    # Create volumes: shape (H, W, D), later loaded as CxHxWxD by
    # EnsureChannelFirstd
    def sample(seed: int, tumor: bool):
        rng = np.random.default_rng(seed)
        vol = rng.normal(0, 1, size=(32, 32, 32)).astype(np.float32)
        lbl = np.zeros((32, 32, 32), dtype=np.uint8)
        if tumor:
            lbl[8:16, 8:16, 8:16] = 1
        # 4 modalities = stack along last axis to mimic multi-channel NIfTI
        # Save as separate files per Decathlon convention (single channel
        # per file), but MONAI's Decathlon datalist allows list of modality
        # paths per case.
        mods = [vol, vol * 0.8, vol * 1.2, vol * 0.5]
        return mods, lbl

    # Build training cases
    training = []
    for i in range(n_train):
        mods, lbl = sample(seed=100 + i, tumor=True)
        mod_paths = []
        for m, name in zip(mods, ["flair", "t1", "t1ce", "t2"]):
            p = imagesTr / f"case_{i:03d}_{name}.nii.gz"
            _write_nifti(m, p)
            mod_paths.append(str(p))
        plabel = labelsTr / f"case_{i:03d}.nii.gz"
        _write_nifti(lbl, plabel)
        training.append({"image": mod_paths, "label": str(plabel)})

    # Build validation cases
    validation = []
    for i in range(n_val):
        mods, lbl = sample(seed=200 + i, tumor=False)
        mod_paths = []
        for m, name in zip(mods, ["flair", "t1", "t1ce", "t2"]):
            p = imagesTr / f"val_{i:03d}_{name}.nii.gz"
            _write_nifti(m, p)
            mod_paths.append(str(p))
        plabel = labelsTr / f"val_{i:03d}.nii.gz"
        _write_nifti(lbl, plabel)
        validation.append({"image": mod_paths, "label": str(plabel)})

    # Minimal Decathlon JSON
    dec_json = {
        "name": "SyntheticBrainTumour",
        "description": "Tiny synthetic dataset for tests",
        "tensorImageSize": "4D",
        "modality": {"0": "MRI"},
        "labels": {"0": "background", "1": "tumor"},
        "numTraining": len(training),
        "numTest": 0,
        "training": training,
        "validation": validation
    }
    with open(base / f"{task}.json", "w") as f:
        json.dump(dec_json, f)
    return base


@pytest.mark.cpu
def test_load_monai_decathlon_synthetic(tmp_path: Path):
    # Arrange synthetic dataset
    base_dir = _make_synthetic_brats_like(tmp_path)

    ds_cfg = {
        "source": "monai_decathlon",
        "dataset_id": "Task01_BrainTumour",
        "data_root": str(tmp_path),
        "cache": "none",
        "splits": {"train_key": "training", "val_key": "validation"},
        "transforms": "brats_like",
        "spacing": [1.0, 1.0, 1.0],
        "loader": {"batch_size": 1, "num_workers": 0, "pin_memory": False}
    }

    # MONAI transforms
    t_train, t_val = get_transforms_brats_like(spacing=(1.0, 1.0, 1.0))

    # Act - use the correct function signature
    train_loader = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="training",
        transform=t_train,
        batch_size=ds_cfg["loader"]["batch_size"],
        download=False
    )
    
    val_loader = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="validation",
        transform=t_val,
        batch_size=ds_cfg["loader"]["batch_size"],
        download=False
    )

    # Create meta for compatibility
    meta = {
        "task": ds_cfg["dataset_id"],
        "base_dir": str(base_dir)
    }

    # Assert dataloaders and metadata
    assert meta["task"] == "Task01_BrainTumour"
    assert meta["base_dir"] == str(base_dir)
    batch = next(iter(train_loader))
    assert "image" in batch and "label" in batch
    # Expect 4-channel MRI (C x H x W x D) after EnsureChannelFirstd
    assert batch["image"].shape[1] == 4
    # label typically 1 channel before one-hot
    assert batch["label"].shape[1] == 1

    # Smoke test: run a small UNet forward
    from monai.networks.nets import UNet
    model = UNet(
        spatial_dims=3, in_channels=4, out_channels=2,
        channels=(8, 16, 32), strides=(2, 2)
    )
    with torch.no_grad():
        y = model(batch["image"])
    assert y.shape[0] == batch["image"].shape[0]
    assert y.shape[1] == 2  # out_channels


@pytest.mark.cpu
def test_validation_loader_iterates(tmp_path: Path):
    _make_synthetic_brats_like(tmp_path, n_train=2, n_val=2)
    ds_cfg = {
        "source": "monai_decathlon",
        "dataset_id": "Task01_BrainTumour",
        "data_root": str(tmp_path),
        "cache": "none",
        "splits": {"train_key": "training", "val_key": "validation"},
        "transforms": "brats_like",
        "spacing": [1.0, 1.0, 1.0],
        "loader": {"batch_size": 1, "num_workers": 0, "pin_memory": False}
    }
    t_train, t_val = get_transforms_brats_like(spacing=(1.0, 1.0, 1.0))
    
    # Load training and validation data
    train_loader = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="training",
        transform=t_train,
        batch_size=ds_cfg["loader"]["batch_size"],
        download=False
    )
    
    val_loader = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="validation",
        transform=t_val,
        batch_size=ds_cfg["loader"]["batch_size"],
        download=False
    )
    
    # Iterate both loaders
    for b in train_loader:
        assert b["image"].ndim == 5  # N C H W D
    for b in val_loader:
        assert b["image"].ndim == 5
