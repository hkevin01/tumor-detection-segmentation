"""
Integration tests for MONAI MSD dataset loading.
"""
import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from src.data.loaders_monai import load_monai_decathlon
from src.data.transforms_presets import get_transforms_brats_like


def _make_synthetic_brats_like(tmp_root: Path, n_train: int = 2, n_val: int = 1) -> Path:
    """Create synthetic BraTS-like dataset with proper structure."""
    task_dir = tmp_root / "Task01_BrainTumour"

    # Create required directories
    (task_dir / "imagesTr").mkdir(parents=True, exist_ok=True)
    (task_dir / "imagesTs").mkdir(parents=True, exist_ok=True)
    (task_dir / "labelsTr").mkdir(parents=True, exist_ok=True)

    # Synthetic 4D MRI volumes (multi-modal: FLAIR, T1, T1CE, T2)
    modalities = ["flair", "t1", "t1ce", "t2"]
    training_cases = []

    # Generate training data
    for i in range(n_train):
        case_id = f"case_{i:03d}"

        # Create multimodal images
        image_paths = []
        for mod in modalities:
            img_file = task_dir / "imagesTr" / f"{case_id}_{mod}.nii.gz"
            # Synthetic 3D volume (64x64x32)
            img_data = np.random.randint(0, 100, (64, 64, 32), dtype=np.int16)
            nib.save(nib.Nifti1Image(img_data, np.eye(4)), str(img_file))
            image_paths.append(str(img_file))

        # Create segmentation mask
        label_file = task_dir / "labelsTr" / f"{case_id}.nii.gz"
        label_data = np.random.randint(0, 3, (64, 64, 32), dtype=np.uint8)
        nib.save(nib.Nifti1Image(label_data, np.eye(4)), str(label_file))

        training_cases.append({
            "image": image_paths,
            "label": str(label_file)
        })

    # Generate validation data
    validation_cases = []
    for i in range(n_val):
        case_id = f"case_{n_train + i:03d}"

        # Create multimodal images
        image_paths = []
        for mod in modalities:
            img_file = task_dir / "imagesTr" / f"{case_id}_{mod}.nii.gz"
            img_data = np.random.randint(0, 100, (64, 64, 32), dtype=np.int16)
            nib.save(nib.Nifti1Image(img_data, np.eye(4)), str(img_file))
            image_paths.append(str(img_file))

        # Create segmentation mask
        label_file = task_dir / "labelsTr" / f"{case_id}.nii.gz"
        label_data = np.random.randint(0, 3, (64, 64, 32), dtype=np.uint8)
        nib.save(nib.Nifti1Image(label_data, np.eye(4)), str(label_file))

        validation_cases.append({
            "image": image_paths,
            "label": str(label_file)
        })

    # Create dataset.json
    dataset_json = {
        "name": "SyntheticBrainTumour",
        "description": "Synthetic multi-modal brain tumor segmentation dataset",
        "tensorImageSize": "4D",
        "modality": {
            "0": "FLAIR",
            "1": "T1w",
            "2": "T1Gd",
            "3": "T2w"
        },
        "labels": {
            "0": "background",
            "1": "necrotic/non-enhancing tumor core",
            "2": "edema",
            "3": "enhancing tumor"
        },
        "numTraining": n_train,
        "numTest": 0,
        "training": training_cases,
        "validation": validation_cases
    }

    with open(task_dir / "Task01_BrainTumour.json", 'w') as f:
        json.dump(dataset_json, f, indent=2)

    return task_dir


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
    train_result = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="training",
        transform=t_train,
        batch_size=ds_cfg["loader"]["batch_size"],
        num_workers=ds_cfg["loader"]["num_workers"],
        cache_rate=0.0,  # Disable caching for testing
        download=False
    )
    train_loader = train_result["dataloader"]

    val_result = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="validation",
        transform=t_val,
        batch_size=ds_cfg["loader"]["batch_size"],
        num_workers=ds_cfg["loader"]["num_workers"],
        cache_rate=0.0,  # Disable caching for testing
        download=False
    )
    val_loader = val_result["dataloader"]

    # Simulate meta dict for compatibility
    meta = {
        "num_train": len(train_loader.dataset),
        "num_val": len(val_loader.dataset),
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
    train_result = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="training",
        transform=t_train,
        batch_size=ds_cfg["loader"]["batch_size"],
        num_workers=ds_cfg["loader"]["num_workers"],
        cache_rate=0.0,  # Disable caching for testing
        download=False
    )
    train_loader = train_result["dataloader"]

    val_result = load_monai_decathlon(
        root_dir=ds_cfg["data_root"],
        task=ds_cfg["dataset_id"],
        section="validation",
        transform=t_val,
        batch_size=ds_cfg["loader"]["batch_size"],
        num_workers=ds_cfg["loader"]["num_workers"],
        cache_rate=0.0,  # Disable caching for testing
        download=False
    )
    val_loader = val_result["dataloader"]

    # Iterate both loaders
    for b in train_loader:
        assert b["image"].ndim == 5  # N C H W D
    for b in val_loader:
        assert b["image"].ndim == 5  # N C H W D
