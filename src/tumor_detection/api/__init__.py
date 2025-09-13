"""
Tumor Detection and Segmentation Library - Core API Module

NASA-STD-8739.8 Requirement Implementation Traceability:
=========================================================

REQ-F-001: AI Model Training and Management (API Interface)
- Provides high-level APIs for model training integration
- Supports multiple model architectures through unified interface
- Model configuration and parameter management

REQ-F-002: Model Inference Engine (Public API)
- High-level APIs for tumor detection and segmentation
- Real-time inference capabilities for clinical use
- Batch processing support for multiple medical images
- Confidence scoring and measurement reporting

REQ-F-008: Clinical User Interface (API Backend)
- Clean, professional APIs for medical imaging applications
- Library-focused interface for system integration
- Clinical workflow-compatible function signatures

REQ-NF-U-001: Usability
- Simple, intuitive API design for medical professionals
- Comprehensive documentation and examples
- Consistent function signatures across all modules
- Error handling with meaningful clinical context

REQ-I-002: Clinical Interface (API Layer)
- Standardized interfaces for clinical system integration
- Medical data format support (DICOM, NIfTI)
- Clinical workflow-compatible response formats

Technical Implementation:
- Unified API layer for detection, segmentation, preprocessing, and evaluation
- Professional library interface with clean abstractions
- Integration-ready for clinical and research applications

Author: Medical Imaging AI Team
Classification: Unclassified
Version: 2.0
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
