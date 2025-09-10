"""
Utilities package for tumor detection.

Common utility functions for device management, file handling, etc.
"""

from .device import auto_device_resolve

__all__ = [
    "auto_device_resolve",
]
