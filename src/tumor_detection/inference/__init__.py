"""
Inference module for tumor detection package.

Provides high-level APIs for model inference, sliding window prediction,
and overlay generation.
"""

from .api import generate_overlays, load_model, run_inference, save_mask

__all__ = [
    "load_model",
    "run_inference",
    "save_mask",
    "generate_overlays",
]
