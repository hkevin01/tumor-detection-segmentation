#!/usr/bin/env python3
"""
Demo: Run tumor detection and save an overlay PNG highlighting the tumor.

Usage:
    python scripts/demo_tumor_overlay.py \
        --model models/best_model.pth \
        --config config.json \
        --input /path/to/image.nii.gz \
        --out ./results/overlay.png
"""

from __future__ import annotations

import argparse

import numpy as np

from src.inference.inference import TumorPredictor
from src.utils.visualization import save_overlay


def main():
    parser = argparse.ArgumentParser(description="Tumor overlay demo")
    parser.add_argument(
        "--model",
        required=True,
        help="Path to model checkpoint",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Config file",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input image path (nii/dcm/png)",
    )
    parser.add_argument(
        "--out",
        default="results/overlay.png",
        help="Output PNG path",
    )
    parser.add_argument(
        "--slice",
        default="largest",
        choices=["largest", "middle"],
        help="Slice selection strategy for 3D volumes",
    )
    args = parser.parse_args()

    predictor = TumorPredictor(
        model_path=args.model, config_path=args.config, device="auto"
    )
    res = predictor.predict_single(args.input)

    pred = res["prediction"]  # (D,H,W) or (H,W)

    # For the background image, reuse the input after preprocessing is not
    # trivially available here. A quick approach: if the predictor saved
    # input shape, synthesize a normalized base using the mask outline for
    # demo purposes. In real usage, load and preprocess the same input into
    # a numpy array.
    if pred.ndim == 2:
        base = (pred > 0).astype(np.float32)
    else:
        # Create a base volume with faint structure from mask for
        # visualization placeholder
        base = (pred > 0).astype(np.float32)

    out_path = save_overlay(
        base, pred, args.out, strategy=args.slice, title="Tumor Overlay"
    )
    print(f"Saved overlay to: {out_path}")


if __name__ == "__main__":
    main()
    main()
