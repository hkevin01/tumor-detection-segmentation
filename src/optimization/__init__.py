"""
Hyperparameter Optimization Module

This module provides tools for systematic hyperparameter optimization using Optuna,
specifically designed for medical image segmentation tasks.

Components:
- OptunaTuner: Core optimization engine
- HyperparameterSearchSpace: Search space definitions
- ObjectiveFunction: Training objectives for optimization
- OptimizationTracker: Results tracking and visualization
"""

__version__ = "1.0.0"
__author__ = "Medical AI Team"

from .hyperparameter_search import HyperparameterSearchSpace
from .objective_functions import SegmentationObjective
from .optuna_optimizer import OptunaTuner

__all__ = [
    "OptunaTuner",
    "HyperparameterSearchSpace",
    "SegmentationObjective"
]
