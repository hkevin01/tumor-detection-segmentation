"""Evaluation modules for model assessment."""

try:
    from .evaluate import ModelEvaluator
    __all__ = ['ModelEvaluator']
except ImportError:
    # Handle case where dependencies aren't available
    __all__ = []
