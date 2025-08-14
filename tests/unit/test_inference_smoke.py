"""Smoke test for inference and overlay pipeline without external assets.

This test creates a tiny config and a dummy UNet checkpoint, synthesizes a
small 3D volume saved as NIfTI, runs TumorPredictor.predict_single, and writes
an overlay PNG. It verifies that the pipeline executes end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from src.inference.inference import TumorPredictor
from src.training.trainer import create_model
from src.utils.visualization import save_overlay


@pytest.mark.unit
@pytest.mark.inference
@torch.no_grad()
def test_inference_smoke_tmpdir(tmp_path: Path):
    # Minimal config for UNet 3D with small sizes
    config = {
        "model_type": "unet",
        "dimensions": 3,
        "in_channels": 1,
        "out_channels": 2,
        "channels": [8, 16],
        "strides": [2],
        "num_res_units": 1,
        "image_size": [16, 16, 16],
    }

    config_path = tmp_path / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)

    # Create and save a random-weight model checkpoint compatible with
    # create_model
    model = create_model(config)
    ckpt = {"model_state_dict": model.state_dict()}
    model_path = tmp_path / "dummy_model.pth"
    torch.save(ckpt, model_path)

    # Synthesize a small 3D volume and save as NIfTI via numpy
    # (no nibabel dependency here). TumorPredictor uses MONAI LoadImage which
    # can ingest numpy paths; however, to avoid I/O complexity, we directly
    # feed a numpy array using the predictor's transforms.
    vol = np.random.rand(16, 16, 16).astype(np.float32)
    vol_path = tmp_path / "vol.npy"
    np.save(vol_path, vol)

    # Run prediction
    predictor = TumorPredictor(
        model_path=str(model_path),
        config_path=str(config_path),
        device="cpu",
    )
    # Predict on the saved numpy file; MONAI LoadImage can load .npy
    result = predictor.predict_single(str(vol_path))

    assert "prediction" in result and "input_image" in result
    pred = result["prediction"]
    base = result["input_image"]

    # Save overlay; should produce a file
    out_png = tmp_path / "overlay.png"
    saved_path = save_overlay(base, pred, out_png, strategy="middle")

    assert saved_path.exists() and saved_path.stat().st_size > 0
