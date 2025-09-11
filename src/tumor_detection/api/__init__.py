"""
Tumor Detection and Segmentation Library - Core API Module

This module provides the main public APIs for tumor detection and segmentation tasks.
It offers a clean, library-focused interface for medical imaging AI applications.
"""

from .detection import TumorDetector, detect_tumors
from .evaluation import ModelEvaluator, evaluate_model
from .preprocessing import ImagePreprocessor, preprocess_medical_image
from .segmentation import TumorSegmenter, segment_tumors

__all__ = [
    # Detection API
    "TumorDetector",
    "detect_tumors",
    # Segmentation API
    "TumorSegmenter",
    "segment_tumors",
    # Preprocessing API
    "ImagePreprocessor",
    "preprocess_medical_image",
    # Evaluation API
    "ModelEvaluator",
    "evaluate_model",
]
