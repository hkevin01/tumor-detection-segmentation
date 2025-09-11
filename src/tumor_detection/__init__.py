"""
Tumor Detection and Segmentation Library

A professional medical imaging library for tumor detection and segmentation
with clean APIs, service integrations, and deployment tools.

Main Features:
- High-level APIs for detection, segmentation, and preprocessing
- Service integrations (DICOM, FHIR, cloud storage)
- Comprehensive testing and validation tools
- Command-line interfaces and deployment utilities
- Professional PyPI package with examples and documentation

Library Usage:
    >>> from tumor_detection.api import detect_tumors, segment_tumors
    >>> from tumor_detection.services import DicomService
    >>>
    >>> # Basic detection
    >>> results = detect_tumors("brain_scan.nii.gz", threshold=0.5)
    >>>
    >>> # Segmentation with post-processing
    >>> segmentation = segment_tumors("brain_scan.nii.gz", post_process=True)
    >>>
    >>> # DICOM integration
    >>> dicom = DicomService("pacs.hospital.com")
    >>> studies = dicom.find_studies(patient_id="PATIENT_001")
"""

__version__ = "2.0.1"
__author__ = "Medical Imaging AI Team"
__email__ = "team@medical-ai.org"

# Library API imports - Main public interface
from .api import (ImagePreprocessor, ModelEvaluator, TumorDetector,
                  TumorSegmenter, detect_tumors, evaluate_model,
                  preprocess_medical_image, segment_tumors)
# Integration utilities for other applications
from .integration import (TumorAnalyzer, analyze_folder, quick_detect,
                          quick_segment)
# Service integrations
from .services import (CloudComputeClient, CloudService, CloudStorageClient,
                       DicomClient, DicomService, FhirClient, FhirService)

# Legacy compatibility imports (for existing code)
try:
    from . import config, inference, models, utils
    from .config import load_dataset_config, load_recipe_config
    from .inference.api import (generate_overlays, load_model, run_inference,
                                save_mask)
except ImportError:
    # Graceful degradation if legacy modules not available
    pass
from .utils.device import auto_device_resolve

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",

    # Main API classes and functions
    "TumorDetector",
    "TumorSegmenter",
    "ImagePreprocessor",
    "ModelEvaluator",
    "detect_tumors",
    "segment_tumors",
    "preprocess_medical_image",
    "evaluate_model",

    # Integration utilities
    "TumorAnalyzer",
    "quick_detect",
    "quick_segment",
    "analyze_folder",

    # Service integrations
    "DicomService",
    "DicomClient",
    "FhirService",
    "FhirClient",
    "CloudService",
    "CloudStorageClient",
    "CloudComputeClient",

    # Legacy API functions
    "load_model",
    "run_inference",
    "save_mask",
    "generate_overlays",
    "load_recipe_config",
    "load_dataset_config",
    "auto_device_resolve",

    # Submodules
    "inference",
    "config",
    "utils",
    "models",
]
    "run_inference",
    "save_mask",
    "generate_overlays",
    "load_recipe_config",
    "load_dataset_config",
    "auto_device_resolve",

    # Submodules
    "inference",
    "config",
    "utils",
    "models",
]
