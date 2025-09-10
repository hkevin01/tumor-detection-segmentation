"""
Tumor Detection and Segmentation Package.

A comprehensive medical imaging package for brain tumor detection
and segmentation using deep learning models.

Main Features:
- High-level inference API for model loading and prediction
- Configuration management for recipes and datasets
- Device utilities for automatic hardware detection
- Command-line interfaces for training and inference
- Pre-trained models for brain tumor segmentation

Example Usage:
    >>> import tumor_detection
    >>> model = tumor_detection.load_model("path/to/model.pth", "config.json")
    >>> prediction = tumor_detection.run_inference(model, "brain_scan.nii.gz")
    >>> tumor_detection.save_mask(prediction, "output_mask.nii.gz")
"""

__version__ = "2.0.0"
__author__ = "Medical Imaging AI Team"
__email__ = "team@medical-ai.org"

# Core package imports
from . import config, inference, models, utils
from .config import load_dataset_config, load_recipe_config
# Convenience imports for common functionality
from .inference.api import (generate_overlays, load_model, run_inference,
                            save_mask)
from .utils.device import auto_device_resolve

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",

    # Submodules
    "inference",
    "config",
    "utils",
    "models",

    # Core API functions
    "load_model",
    "run_inference",
    "save_mask",
    "generate_overlays",
    "load_recipe_config",
    "load_dataset_config",
    "auto_device_resolve",
]
