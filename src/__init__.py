"""
Tumor Detection and Segmentation Package

A comprehensive deep learning pipeline for medical image analysis using MONAI.
"""

__version__ = "0.1.0"
__author__ = "Tumor Detection Team"

# Conditional imports to avoid import errors during development
__all__ = []

try:
    from . import data
    __all__.append('data')
except ImportError:
    pass

try:
    from . import training
    __all__.append('training')
except ImportError:
    pass

try:
    from . import evaluation
    __all__.append('evaluation')
except ImportError:
    pass

try:
    from . import inference
    __all__.append('inference')
except ImportError:
    pass

try:
    from . import utils
    __all__.append('utils')
except ImportError:
    pass
