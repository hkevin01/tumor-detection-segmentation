"""
Command-line interface for tumor detection and segmentation.
"""

from .infer import main as infer_main
from .train import main as train_main

__all__ = ["train_main", "infer_main"]
