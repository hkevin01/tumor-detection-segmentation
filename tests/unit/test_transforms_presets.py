#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import nibabel as nib
from pathlib import Path

import torch

from src.data.transforms_presets import (
    get_transforms_brats_like,
    get_transforms_ct_liver
)


def _save(img: np.ndarray, path: Path):
    affine = np.eye(4, dtype=np.float32)
    nii_img = nib.Nifti1Image(img.astype(np.float32), affine)
    nib.save(nii_img, str(path))


def test_brats_like_transforms_run(tmp_path: Path):
    # Synthetic 4 modalities and 1 label
    img_paths = []
    for i in range(4):
        p = tmp_path / f"img_{i}.nii.gz"
        _save(np.random.randn(32, 32, 32), p)
        img_paths.append(str(p))
    p_lbl = tmp_path / "label.nii.gz"
    lbl = np.zeros((32, 32, 32), dtype=np.uint8)
    lbl[10:20, 10:20, 10:20] = 1
    _save(lbl, p_lbl)

    t_train, t_val = get_transforms_brats_like(spacing=(1.0, 1.0, 1.0))
    data = {"image": img_paths, "label": str(p_lbl)}
    out = t_train(data)
    assert "image" in out and "label" in out
    assert out["image"].dtype == torch.float32
    assert out["image"].shape[1] == 4  # channels
    assert not torch.isnan(out["image"]).any()


def test_ct_liver_transforms_run(tmp_path: Path):
    # Single-channel CT with label
    p_img = tmp_path / "ct.nii.gz"
    # HU-like values
    ct = np.random.uniform(-150, 450, size=(48, 48, 48)).astype(np.float32)
    _save(ct, p_img)
    p_lbl = tmp_path / "label.nii.gz"
    lbl = np.zeros((48, 48, 48), dtype=np.uint8)
    lbl[12:20, 12:20, 12:20] = 1
    _save(lbl, p_lbl)

    t_train, t_val = get_transforms_ct_liver(spacing=(1.5, 1.5, 1.5))
    data = {"image": str(p_img), "label": str(p_lbl)}
    out = t_train(data)
    assert out["image"].shape[1] == 1
    # after ScaleIntensityRanged
    assert (out["image"] >= 0).all() and (out["image"] <= 1).all()
