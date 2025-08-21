"""
Phase 4 External Integrations Module
===================================

This module provides integration with state-of-the-art medical imaging
frameworks:
- nnU-Net: Self-configuring medical image segmentation
- MONAI: Medical Open Network for AI
- Detectron2: Advanced computer vision models

Author: Tumor Detection Segmentation Team
Phase: 4 - Advanced External Integrations
"""

# Import integrations conditionally to avoid import errors
try:
    from .nnunet_integration import NnUNetIntegration
    NNUNET_AVAILABLE = True
except ImportError:
    NnUNetIntegration = None
    NNUNET_AVAILABLE = False

try:
    from .monai_integration import MonaiIntegration
    MONAI_AVAILABLE = True
except ImportError:
    MonaiIntegration = None
    MONAI_AVAILABLE = False

try:
    from .detectron2_integration import Detectron2Integration
    DETECTRON2_AVAILABLE = True
except ImportError:
    Detectron2Integration = None
    DETECTRON2_AVAILABLE = False

try:
    from .ensemble_framework import EnsembleFramework
    ENSEMBLE_AVAILABLE = True
except ImportError:
    EnsembleFramework = None
    ENSEMBLE_AVAILABLE = False

__all__ = [
    'NnUNetIntegration',
    'MonaiIntegration',
    'Detectron2Integration',
    'EnsembleFramework'
]

__version__ = "1.0.0"
__phase__ = "4"
